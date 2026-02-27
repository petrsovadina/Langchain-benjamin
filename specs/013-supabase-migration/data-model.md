# Data Model: Supabase Migration (013)

**Date**: 2026-02-18
**Feature**: [spec.md](./spec.md) | [research.md](./research.md)

## Entity: GuidelineSection (Python Domain Model)

**Source**: `langgraph-app/src/agent/models/guideline_models.py`
**Status**: No changes required — model stays the same, only storage mapping changes.

```python
class GuidelineSection(BaseModel):
    guideline_id: str       # e.g., "CLS-JEP-2024-001"
    title: str              # Guideline title
    section_name: str       # Section / organization name
    content: str            # Full text content
    publication_date: str   # "YYYY-MM-DD"
    source: GuidelineSource # cls_jep | esc | ers
    url: str                # Source URL
    metadata: dict[str, Any]  # Includes "embedding" key (list[float], 1536-dim)
```

### Validation Rules (unchanged)
- `guideline_id`: regex `^(CLS-JEP|ESC|ERS)-\d{4}-\d{3}$`
- `title`: min_length=1
- `content`: min_length=1
- `publication_date`: regex `^\d{4}-\d{2}-\d{2}$`, valid date
- `metadata["embedding"]`: list/tuple of 1536 floats (validated in storage layer)

---

## Entity: guidelines (Supabase Table)

**Source**: `public.guidelines` in Supabase project `higziqzcjmtmkzxbbzik`
**Status**: Already exists, no schema changes needed.

### Columns (24 total)

| Column | Type | Nullable | Default | Used by Migration |
|---|---|---|---|---|
| `id` | `uuid` | NO | `gen_random_uuid()` | Yes (PK, returned) |
| `external_id` | `text` | YES | null | Yes (← guideline_id) |
| `title` | `text` | NO | — | Yes (← title) |
| `organization` | `text` | NO | — | Yes (← source display name) |
| `specialty` | `text` | YES | null | No (future use) |
| `source_type` | `source_type` enum | YES | `'guidelines'` | Yes (always 'guidelines') |
| `is_czech` | `boolean` | YES | `true` | No (default OK) |
| `version` | `text` | YES | null | No (future use) |
| `publication_year` | `integer` | NO | — | Yes (← extracted from date) |
| `publication_date` | `date` | YES | null | Yes (← publication_date) |
| `valid_until` | `date` | YES | null | No (future use) |
| `authors` | `text[]` | YES | null | No (future use) |
| `summary` | `text` | YES | null | No (future use) |
| `key_recommendations` | `text[]` | YES | null | No (future use) |
| `full_content` | `text` | YES | null | Yes (← content) |
| `url` | `text` | YES | null | Yes (← url) |
| `pdf_url` | `text` | YES | null | No (future use) |
| `keywords` | `text[]` | YES | null | Partial (from metadata) |
| `icd10_codes` | `text[]` | YES | null | Partial (from metadata) |
| `embedding` | `vector(1536)` | YES | null | Yes (← metadata.embedding) |
| `is_current` | `boolean` | YES | `true` | No (default OK) |
| `superseded_by` | `uuid` | YES | null | No (future use) |
| `created_at` | `timestamptz` | YES | `now()` | No (auto) |
| `updated_at` | `timestamptz` | YES | `now()` | No (auto via trigger) |

### Indexes
| Name | Type | Columns | Notes |
|---|---|---|---|
| `guidelines_pkey` | btree (unique) | `id` | Primary key |
| `guidelines_external_id_key` | btree (unique) | `external_id` | UPSERT target |
| `idx_guidelines_embedding` | HNSW | `embedding vector_cosine_ops` | m=16, ef_construction=64 |

### Constraints
| Name | Definition |
|---|---|
| `guidelines_pkey` | PRIMARY KEY (id) |
| `guidelines_external_id_key` | UNIQUE (external_id) |
| `guidelines_superseded_by_fkey` | FOREIGN KEY (superseded_by) REFERENCES guidelines(id) |

### RLS
- Enabled, with public SELECT policy
- INSERT/UPDATE/DELETE requires service_role key

### Trigger
- `guidelines_updated_at` → `BEFORE UPDATE` → `update_updated_at()` (auto-sets `updated_at`)

---

## Entity: DatabaseConfig (Python Configuration)

**Source**: `langgraph-app/src/agent/utils/guidelines_storage.py`
**Status**: No changes required.

```python
@dataclass
class DatabaseConfig:
    host: str                             # db.xxx.supabase.co
    port: int                             # 5432
    database: str                         # "postgres"
    user: str                             # "postgres"
    password: str                         # from env
    ssl: ssl.SSLContext | bool | None      # SSLContext for Supabase
```

### from_env() Priority
1. `DATABASE_URL` → parse connection string, configure SSL from `sslmode` param
2. `SUPABASE_URL` + `SUPABASE_KEY` → derive `db.{host}`, always SSL
3. Neither → raise `ValueError`

---

## Entity: source_type (PostgreSQL Enum)

**Source**: Supabase custom enum
**Status**: Exists, no changes needed.

| Value | Used by |
|---|---|
| `pubmed` | Future PubMed caching |
| `sukl` | Future SÚKL data |
| `guidelines` | **This migration** (all guidelines) |
| `vzp` | Future VZP pricing |
| `cochrane` | Future Cochrane reviews |
| `other` | Catch-all |

---

## Field Mapping: Python → Supabase (INSERT)

```
GuidelineSection                  guidelines (Supabase)
─────────────────                 ──────────────────────
guideline_id ─────────────────→  external_id
title ────────────────────────→  title
(derived from source) ────────→  organization ("ČLS JEP"/"ESC"/"ERS")
content ──────────────────────→  full_content
publication_date ─────────────→  publication_date (date) + publication_year (int)
source ───────────────────────→  source_type ('guidelines'::source_type)
url ──────────────────────────→  url
metadata["embedding"] ────────→  embedding (vector)
metadata["keywords"] ─────────→  keywords (text[])
metadata["icd10_codes"] ──────→  icd10_codes (text[])
metadata (rest) ──────────────→  (discarded or logged)
```

## Field Mapping: Supabase → Python (SELECT)

```
guidelines (Supabase)             Python dict
──────────────────────            ──────────
id ───────────────────────────→  "id" (str, UUID)
external_id ──────────────────→  "guideline_id" (str)
title ────────────────────────→  "title" (str)
organization ─────────────────→  "section_name" (str, backward compat key)
full_content ─────────────────→  "content" (str, "" if NULL)
publication_date ─────────────→  "publication_date" (str, ISO format)
source_type ──────────────────→  "source" (str, reverse-mapped via organization)
url ──────────────────────────→  "url" (str)
(metadata columns) ───────────→  "metadata" (dict, reconstructed)
1-(embedding<=>query) ────────→  "similarity_score" (float, search only)
```

## State Transitions

No state machine. Guidelines storage is CRUD-only:
- **Insert**: `store_guideline()` — upsert on `external_id`
- **Search**: `search_guidelines()` — vector similarity via HNSW
- **Get**: `get_guideline_section()` — lookup by `external_id` or `id` (UUID)
- **Delete**: `delete_guideline_section()` — delete by `external_id` or `id` (UUID)
