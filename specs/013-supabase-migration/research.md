# Research: Supabase Migration (013)

**Date**: 2026-02-18
**Feature**: [spec.md](./spec.md)
**Status**: Complete

## Research Tasks

### RT-001: Schema Column Mapping (NEEDS CLARIFICATION → Resolved)

**Decision**: Map Python `GuidelineSection` fields to Supabase `guidelines` table as follows:

| Python Field (GuidelineSection) | Supabase Column | Type (Python → Supabase) | Notes |
|---|---|---|---|
| `guideline_id` | `external_id` | `str` → `text` (UNIQUE) | Unique identifier for deduplication |
| `title` | `title` | `str` → `text` (NOT NULL) | Direct mapping, no change |
| `section_name` | `organization` | `str` → `text` (NOT NULL) | Semantic shift: stores issuing body name |
| `content` | `full_content` | `str` → `text` (nullable) | Name change only |
| `publication_date` | `publication_date` + `publication_year` | `str (YYYY-MM-DD)` → `date` + `int` | Year extracted from date string |
| `source` (GuidelineSource enum) | `source_type` | `"cls_jep"/"esc"/"ers"` → `'guidelines'::source_type` | Always 'guidelines' per FR-008 |
| `url` | `url` | `str` → `text` | Direct mapping |
| `metadata["embedding"]` | `embedding` | `list[float]` → `vector(1536)` | pgvector column, same dimensions |
| `metadata` (rest) | `keywords[]`, `icd10_codes[]`, etc. | `dict` → native array columns | Extract known keys to native columns |
| (auto-generated) | `id` | N/A → `uuid` (PK) | `gen_random_uuid()` default |
| (derived from source) | `organization` | `GuidelineSource` → display name | `CLS_JEP`→"ČLS JEP", `ESC`→"ESC", `ERS`→"ERS" |

**Rationale**: The Supabase schema was designed for whole guidelines (not sections). The `organization` column semantically holds the issuing body name. Per FR-008, `GuidelineSource` enum values map to `source_type='guidelines'` with the org display name in `organization`.

**Key conflict resolution (FR-002 vs FR-008)**:
- FR-002 says `section_name` → `organization`
- FR-008 says `GuidelineSource` values provide the organization name
- Resolution: The `organization` column gets populated from `GuidelineSource` display name (ČLS JEP/ESC/ERS), which is the semantically correct mapping. The `section_name` field value is stored in `metadata` JSONB for backward compatibility if needed.

**Alternatives considered**:
1. Create a `section_name` column in Supabase → Rejected: schema already finalized, and the conceptual model is whole-guideline not sections.
2. Store section_name directly in organization → Rejected: breaks semantic meaning of the column.

---

### RT-002: Primary Key Type Change (int → UUID)

**Decision**: Change all return types and parameters from `int` to `str` (UUID).

**Affected signatures**:
- `store_guideline() -> int` → `store_guideline() -> str`
- `get_guideline_section(section_id: int | None)` → `get_guideline_section(section_id: str | None)`
- `delete_guideline_section(section_id: int | None)` → `delete_guideline_section(section_id: str | None)`
- All returned dicts: `"id": row["id"]` changes from int to UUID string

**Rationale**: Supabase uses `gen_random_uuid()` for PKs. UUID as `str` is the idiomatic Python representation.

**Alternatives considered**:
1. Use `uuid.UUID` type → Rejected: adds import, complicates JSON serialization, `str` is simpler.
2. Keep int wrapper → Rejected: Supabase has no SERIAL column.

---

### RT-003: UPSERT Conflict Resolution

**Decision**: Change `ON CONFLICT (guideline_id, section_name)` to `ON CONFLICT (external_id)`.

**Rationale**: Supabase has `UNIQUE (external_id)` constraint, not a composite unique on two columns. The `external_id` is the deduplication key.

**Alternatives considered**:
1. Add composite unique constraint to Supabase → Rejected: schema already in production with existing RLS/indexes.
2. Use separate SELECT + INSERT/UPDATE → Rejected: race conditions, more complex.

---

### RT-004: Source Type Enum Mapping

**Decision**: Map all `GuidelineSource` values to Supabase `source_type='guidelines'` enum.

| Python GuidelineSource | Supabase source_type | Supabase organization |
|---|---|---|
| `CLS_JEP` ("cls_jep") | `'guidelines'` | "ČLS JEP" |
| `ESC` ("esc") | `'guidelines'` | "ESC" |
| `ERS` ("ers") | `'guidelines'` | "ERS" |

Reverse mapping (read from DB):
- `source_type='guidelines'` + `organization='ČLS JEP'` → `GuidelineSource.CLS_JEP`
- `source_type='guidelines'` + `organization='ESC'` → `GuidelineSource.ESC`
- `source_type='guidelines'` + `organization='ERS'` → `GuidelineSource.ERS`
- Unknown organization → log warning, return `organization` as-is in "source" field

**Rationale**: Supabase enum has only 6 values (`pubmed`, `sukl`, `guidelines`, `vzp`, `cochrane`, `other`). All guideline sources map to `'guidelines'` type.

---

### RT-005: SSL and Connection Configuration

**Decision**: Use `DATABASE_URL` as primary connection method (takes precedence per existing behavior).

**Connection string format**:
```
postgresql://postgres.[project-ref]:[password]@aws-0-eu-central-1.pooler.supabase.com:5432/postgres
```

Or direct connection:
```
postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres
```

**SSL handling**: Supabase mandates SSL. The existing `DatabaseConfig.from_env()` already handles:
- `DATABASE_URL` with `?sslmode=require` → `ssl.SSLContext`
- `SUPABASE_URL` + `SUPABASE_KEY` → `ssl.SSLContext` (always)

No changes needed to SSL logic.

**Rationale**: Existing code already supports both patterns correctly.

---

### RT-006: Search Query Changes

**Decision**: Update search query column references:

| Current SQL | New SQL |
|---|---|
| `SELECT id, guideline_id, title, section_name, content, ...` | `SELECT id, external_id, title, organization, full_content, ...` |
| `FROM guidelines WHERE embedding IS NOT NULL` | Same (embedding column name unchanged) |
| `AND source = $N` | `AND source_type = $N::source_type` (enum cast) |
| `WHERE guideline_id = $1 AND section_name = $2` | `WHERE external_id = $1` (single unique key) |
| `1 - (embedding <=> $1::vector)` | Same (cosine similarity unchanged, uses HNSW index) |

**Key**: Source filter now uses enum casting (`$N::source_type`) since `source_type` is a PostgreSQL enum, not a plain text column.

**Rationale**: HNSW index `idx_guidelines_embedding` with `vector_cosine_ops` works with the same `<=>` operator. No search logic changes beyond column renaming.

---

### RT-007: NULL full_content Handling (Edge Case)

**Decision**: When `full_content IS NULL`, return empty string `""` in Python dict.

```python
"content": row["full_content"] or ""
```

**Rationale**: Spec edge case: "search returns results with empty content strings." The `full_content` column is nullable in Supabase.

---

### RT-008: publication_year Required Field

**Decision**: Extract `publication_year` from `publication_date` when inserting.

```python
publication_year = datetime.strptime(publication_date, "%Y-%m-%d").year
```

**Rationale**: Supabase schema has `publication_year int NOT NULL` but `publication_date date` is nullable. Always set both — year from date string, full date as actual date.

---

### RT-009: Files Requiring Changes

| File | Action | Scope |
|---|---|---|
| `langgraph-app/src/agent/utils/guidelines_storage.py` | **Major edit** | Column mapping, types, SQL queries |
| `.mcp.json` | **Edit** | Remove insforge entry |
| `AGENTS.md` | **Delete** | Entire file is InsForge docs |
| `.claude/settings.local.json` | **Edit** | Remove insforge permissions + server |
| `langgraph-app/.env.example` | **Edit** | Uncomment Supabase vars, add DATABASE_URL |
| `langgraph-app/.env` | **Edit** | Add real Supabase credentials |
| `CLAUDE.md` | **Edit** | Update DB config section |
| `README.md` | **Edit** | Update setup instructions |
| `langgraph-app/tests/unit_tests/utils/test_guidelines_storage.py` | **Major edit** | Column names, UUID types, mock data |
| `langgraph-app/tests/integration_tests/test_guidelines_storage_integration.py` | **Edit** | UUID return types |

**No changes needed**:
- `langgraph-app/src/agent/models/guideline_models.py` — Python model unchanged
- `langgraph-app/src/agent/nodes/guidelines_agent.py` — calls storage functions, types flow through
- `langgraph-app/src/agent/graph.py` — no DB references
- `langgraph-app/tests/unit_tests/nodes/test_guidelines_agent.py` — mocks storage, no SQL
- Frontend files — no DB connection from frontend

---

### RT-010: Test Impact Analysis

**Unit tests (test_guidelines_storage.py, ~763 lines)**:
- `TestDatabaseConfig` — No changes (from_env() logic unchanged)
- `TestStoreGuideline` — Update: column names in SQL assertions, return type int→str(UUID), mock data
- `TestSearchGuidelines` — Update: column names in SELECT assertions, source filter with enum cast
- `TestGetGuidelineSection` — Update: column names, lookup by `external_id` instead of `guideline_id + section_name`
- `TestDeleteGuidelineSection` — Update: `section_id: int` → `str`, column names

**Integration tests (test_guidelines_storage_integration.py, ~113 lines)**:
- Return type assertions: `record_id > 0` → `isinstance(record_id, str)` and UUID format check
- Test guideline section fixture: update expected column names in assertions

**Guidelines agent tests** — No changes needed (mock storage functions, don't test SQL).

---

## Summary

All NEEDS CLARIFICATION items resolved. Key decisions:
1. Column mapping follows FR-002 + FR-008 combined mapping
2. UUID strings for all IDs (no uuid.UUID type)
3. Single-column UPSERT on `external_id`
4. `source_type` uses enum cast, always `'guidelines'`
5. `publication_year` extracted from `publication_date`
6. 10 files to modify, 1 file to delete
7. ~763 lines of unit tests need column name updates
8. No changes to Python domain models or agent node logic
