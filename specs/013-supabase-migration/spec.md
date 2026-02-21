# Feature Specification: Supabase Migration (Replace InsForge)

**Feature Branch**: `013-supabase-migration`
**Created**: 2026-02-17
**Status**: Draft
**Input**: Replace InsForge with Supabase: Remove InsForge MCP configuration and AGENTS.md, configure Supabase credentials in .env files, adapt guidelines_storage.py to match existing Supabase schema (26 tables already created with pgvector, RLS, custom enums), update all documentation references.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Backend connects to Supabase for guidelines storage (Priority: P1)

When a physician asks a clinical guideline question (e.g. "Doporučení pro léčbu hypertenze"), the guidelines agent retrieves relevant guideline sections from the Supabase PostgreSQL database using vector similarity search. The system uses the existing Supabase `guidelines` table schema (UUID primary keys, `external_id`, `full_content`, `organization`, `source_type` enum, HNSW index on `embedding` column).

**Why this priority**: Without a working database connection, the guidelines agent returns empty results. This is the core deliverable — making `guidelines_storage.py` work with the existing Supabase schema.

**Independent Test**: Run `guidelines_storage.py` integration tests against the live Supabase database — store a guideline section, search by embedding, retrieve by ID.

**Acceptance Scenarios**:

1. **Given** Supabase credentials are configured in `.env`, **When** the backend starts, **Then** it establishes an asyncpg connection pool to `db.higziqzcjmtmkzxbbzik.supabase.co:5432` with SSL enabled.
2. **Given** the connection pool is active, **When** `store_guideline()` is called with a guideline section and embedding, **Then** the record is inserted into the Supabase `guidelines` table using the correct column mapping (`guideline_id` → `external_id`, `content` → `full_content`, `source` → `source_type`).
3. **Given** guidelines exist in the database, **When** `search_guidelines()` is called with a query embedding, **Then** results are returned ordered by cosine similarity using the HNSW index.
4. **Given** a guideline with `external_id = "CLS-JEP-2024-001"`, **When** `get_guideline_section()` is called with that ID, **Then** the full guideline data is returned with all fields mapped correctly.

---

### User Story 2 - InsForge configuration removed from project (Priority: P1)

The project no longer references InsForge in any configuration, documentation, or code. Developers setting up the project follow Supabase-based instructions exclusively. No InsForge MCP tools are loaded into Claude Code sessions.

**Why this priority**: InsForge references create confusion for developers and may cause accidental connections to an unused service. Must be done alongside database migration to maintain consistency.

**Independent Test**: Search the entire codebase for "insforge" (case-insensitive) — zero matches outside of git history.

**Acceptance Scenarios**:

1. **Given** the current `.mcp.json` contains an InsForge server entry, **When** migration is complete, **Then** the InsForge entry is removed and only the Supabase MCP entry remains.
2. **Given** `AGENTS.md` contains InsForge SDK instructions with `alwaysApply: true`, **When** migration is complete, **Then** the file is deleted.
3. **Given** `.env` and `.env.example` contain InsForge references, **When** migration is complete, **Then** all environment variables reference Supabase (`SUPABASE_URL`, `SUPABASE_KEY`, `DATABASE_URL`).

---

### User Story 3 - Environment configuration is correct and documented (Priority: P2)

A new developer cloning the repository can set up Supabase connectivity by following the updated `.env.example` and documentation. The configuration supports both direct connection string (`DATABASE_URL`) and Supabase-specific (`SUPABASE_URL` + `SUPABASE_KEY`) patterns, matching the existing `DatabaseConfig.from_env()` logic.

**Why this priority**: Developer onboarding depends on clear, correct configuration. Secondary to core functionality but essential for team productivity.

**Independent Test**: A fresh clone with only `.env.example` values filled in successfully connects to Supabase and passes the health check.

**Acceptance Scenarios**:

1. **Given** a developer copies `.env.example` to `.env`, **When** they fill in Supabase credentials, **Then** `PYTHONPATH=src python -c "from agent.utils.guidelines_storage import get_pool; import asyncio; asyncio.run(get_pool())"` succeeds.
2. **Given** the README and CLAUDE.md reference database configuration, **When** a developer reads them, **Then** they find Supabase-specific setup instructions (not InsForge, not generic PostgreSQL).
3. **Given** the frontend needs Supabase URL for future auth integration, **When** a developer checks `frontend/.env.local`, **Then** `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY` are documented in `.env.example` or equivalent.

---

### User Story 4 - All existing tests continue to pass (Priority: P2)

The 442 backend unit tests and 216 frontend tests continue to pass without modification. Integration tests for guidelines storage work against the live Supabase database when `DATABASE_URL` or `SUPABASE_URL` is set.

**Why this priority**: Regression prevention. Schema mapping changes in `guidelines_storage.py` must not break existing mock-based unit tests.

**Independent Test**: Run `PYTHONPATH=src uv run pytest tests/ -v` — all tests pass (excluding those that require API keys or live database, which are appropriately skipped).

**Acceptance Scenarios**:

1. **Given** `guidelines_storage.py` column mappings have changed, **When** unit tests run with mocked asyncpg, **Then** all `test_guidelines_storage.py` tests pass with updated mock data matching the new column names.
2. **Given** `SUPABASE_URL` is set in the environment, **When** integration tests run, **Then** `test_guidelines_storage_integration.py` tests pass against the live Supabase database.
3. **Given** no changes were made to node logic, MCP clients, or routing, **When** the full test suite runs, **Then** all non-guidelines tests pass unchanged.

---

### Edge Cases

- What happens when Supabase is unreachable at startup? The connection pool creation raises `GuidelinesStorageError` with a clear message including the host.
- What happens when the `guidelines` table has records with `NULL` `full_content`? The search returns results with empty content strings.
- What happens when `source_type` enum value doesn't match existing `GuidelineSource` Python enum? The system maps known values and logs a warning for unknown ones.
- What happens when the HNSW index is not yet populated (empty table)? Vector search returns empty results without error.
- What happens when `DATABASE_URL` and `SUPABASE_URL` are both set? `DATABASE_URL` takes precedence (existing behavior in `DatabaseConfig.from_env()`).

## Clarifications

### Session 2026-02-18

- Q: Jaký typ Supabase klíče má backend používat pro zápisy (anon vs service_role)? → A: `service_role` klíč — backend je důvěryhodný server, obchází RLS pro plný CRUD přístup.
- Q: Mají se frontend env proměnné (NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY) přidat do frontend/.env.example? → A: Ano, jako komentované placeholdery pro budoucí použití. Nezavádí závislost, ale usnadní budoucí integraci.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST connect to Supabase PostgreSQL via asyncpg using SSL on port 5432.
- **FR-002**: System MUST map Python `GuidelineSection` fields to Supabase `guidelines` table columns: `guideline_id` → `external_id`, `content` → `full_content`, `source` → `source_type`, `section_name` → `organization`.
- **FR-003**: System MUST support both `DATABASE_URL` (connection string) and `SUPABASE_URL` + `SUPABASE_KEY` environment variable patterns for configuration. Backend MUST use the `service_role` key (not `anon`) to bypass RLS for INSERT/UPDATE/DELETE operations.
- **FR-004**: System MUST remove all InsForge references from `.mcp.json`, `AGENTS.md`, `.env`, `.env.example`, and documentation files.
- **FR-005**: System MUST preserve the existing `IMCPClient` interface and MCP client architecture — only database connectivity changes.
- **FR-006**: System MUST use the existing HNSW index (`idx_guidelines_embedding`) with `vector_cosine_ops` for similarity search.
- **FR-007**: System MUST handle UUID primary keys (Supabase) instead of SERIAL integers (previous schema) in all return types.
- **FR-008**: System MUST map `GuidelineSource` enum values (`CLS_JEP`, `ESC`, `ERS`) to Supabase `source_type` enum value `guidelines`, storing the specific organization in the `organization` column.
- **FR-009**: System MUST update `.env.example` with Supabase-specific variables and connection string format.
- **FR-010**: System MUST update `CLAUDE.md`, `README.md`, and relevant documentation to reference Supabase instead of InsForge.
- **FR-011**: System MUST add commented-out `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY` placeholders to `frontend/.env.example` for future frontend integration.

### Key Entities

- **GuidelineSection (Python)**: Domain model with `guideline_id`, `title`, `section_name`, `content`, `source`, `url`, `metadata` (including embedding). Maps to Supabase `guidelines` table.
- **guidelines (Supabase table)**: UUID PK, `external_id` (unique), `title`, `organization`, `specialty`, `source_type` enum, `full_content`, `embedding` (vector), `keywords[]`, `icd10_codes[]`, `publication_year`, `is_current`, `superseded_by` (self-FK).
- **documents (Supabase table)**: UUID PK, `source_type`, `external_id`, `title`, `content`, `pmid`, `doi`, `embedding` (vector), `metadata` JSONB. Available for future PubMed article caching.
- **DatabaseConfig (Python)**: Configuration dataclass with `from_env()` factory method supporting both `DATABASE_URL` and `SUPABASE_URL` + `SUPABASE_KEY` patterns.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 442 backend tests pass after migration (zero regressions).
- **SC-002**: Guidelines storage integration tests pass against live Supabase (store, search, retrieve, delete).
- **SC-003**: Zero references to "insforge" remain in the codebase outside of git history.
- **SC-004**: A new developer can set up database connectivity in under 5 minutes following documentation.
- **SC-005**: Vector similarity search on the `guidelines` table returns results within 2 seconds.
- **SC-006**: Connection pool establishes with SSL to Supabase within 5 seconds of backend startup.

## Assumptions

- The Supabase project supports direct PostgreSQL connections via asyncpg (not limited to REST API).
- The `guidelines` table stores whole guidelines. The `section_name` field from the Python model maps to `organization` (the issuing body).
- Vector search uses direct SQL via asyncpg (existing pattern), not a Supabase RPC function.
- The `documents` table may be used in future for PubMed article caching but is out of scope for this migration.
- Frontend Supabase SDK integration (auth, real-time) is out of scope — this migration focuses on backend database connectivity only.
- Redis caching remains unchanged (separate infrastructure).

## Dependencies

- Supabase project with pgvector v0.8.0 enabled and `guidelines` table with HNSW index.
- Python `asyncpg` library (already in project dependencies).
- Network access from development environment to `db.higziqzcjmtmkzxbbzik.supabase.co:5432`.

## Out of Scope

- Populating the `guidelines` table with actual ČLS JEP/ESC/ERS data (separate feature).
- Frontend Supabase SDK integration or authentication (but placeholder env vars in `frontend/.env.example` ARE in scope).
- Redis cache configuration.
- BioMCP deployment.
- VZP Pricing Agent implementation.
- Supabase Edge Functions.
- Migration of InsForge data (table was empty/test data only).
