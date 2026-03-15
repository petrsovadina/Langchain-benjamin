# Feature Specification: Audit Remediation

**Feature Branch**: `001-audit-remediation`
**Created**: 2026-03-12
**Status**: Draft
**Input**: Comprehensive expert audit of Czech MedAI (Benjamin) — 20 prioritized action items across security, architecture, tests, and configuration

## Clarifications

### Session 2026-03-12

- Q: Je autentizace (audit item #4/#11 — API key middleware, Supabase Auth) v scope tohoto feature? → A: Out of scope — Supabase Auth bude řešena jako samostatný feature spec. Projekt již využívá Supabase (PostgreSQL + pgvector) a plánuje rozšířit o Supabase Auth pro konzistentní autentizační vrstvu.
- Q: Jaká je rollback strategie při regresi způsobené opravou? → A: Jeden PR per priorita (P1, P2, P3). Regrese se řeší v rámci daného PR před merge. Inkrementální delivery s maximální bezpečností.
- Q: Na jakou verzi sjednotit projekt po remediaci? → A: `0.2.0` — reflektuje audit remediaci jako meaningful milestone nad stávající `0.1.0` API verzí.

## Out of Scope

- **Autentizace**: API key middleware a Supabase Auth integrace budou řešeny v samostatném feature specu. Tento spec se zaměřuje pouze na remediaci bezpečnostních, architektonických a konfigurančních nálezů z auditu.
- **Frontend security headers** (CSP, Permissions-Policy pro Next.js): Audit item #8/#15 — vyžaduje frontend-specifický přístup, vhodné pro samostatný spec.
- **Next.js upgrade** (14 → 15): Audit item #16 — rozsáhlý upgrade s breaking changes, samostatný feature.
- **GDPR dokumentace LangSmith**: Audit item #20 — dokumentační úkol, ne kódová změna.

**Deployment Note**: Po dokončení této remediace zůstává deployment do produkce stále blokován požadavkem na autentizaci (constitution v1.3.0, Production Readiness Standards). Autentizace bude řešena v samostatném feature specu.

## Delivery Strategy

Implementace probíhá ve 3 inkrementálních PR, jeden per prioritní úroveň:

- **PR 1 (P1)**: US1–US3 — Error sanitization, CORS safety, LLM timeouts. Blokuje deployment.
- **PR 2 (P2)**: US4–US8 — Cache key, user_id validace, Docker credentials, test cleanup, cache testy.
- **PR 3 (P3)**: US9–US12 — LLM reuse, double execution, dead code, dependency cleanup.

Každý PR musí projít všemi existujícími testy + novými testy pro danou prioritu. Regrese se řeší v rámci daného PR před merge.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Error Response Sanitization (Priority: P1)

As a system operator deploying Czech MedAI, I need error responses to never expose internal implementation details (file paths, database errors, stack traces) to end users, so that attackers cannot use error messages for reconnaissance.

**Why this priority**: HIGH security finding. `str(e)` is sent directly to SSE clients, and the health endpoint leaks raw database error strings. This is exploitable in production.

**Independent Test**: Can be tested by triggering errors (invalid queries, DB disconnection) and verifying SSE error events contain only generic messages in production mode.

**Acceptance Scenarios**:

1. **Given** the API is running in production mode, **When** an internal error occurs during SSE streaming, **Then** the error event contains `"An unexpected error occurred"` and NOT the raw exception message
2. **Given** the API is running in production mode, **When** the database is unreachable, **Then** the health endpoint reports `"unavailable"` status without raw connection error details
3. **Given** the API is running in development mode, **When** an error occurs, **Then** the raw error detail MAY be included for debugging purposes
4. **Given** any error occurs, **Then** the full error with traceback is logged server-side via `logger.error(..., exc_info=True)`

---

### User Story 2 - CORS Production Safety (Priority: P1)

As a system operator, I need the API to refuse to start if CORS origins are not explicitly configured in production, so that the API is never accidentally deployed with wildcard CORS allowing credential theft.

**Why this priority**: HIGH security finding. `allow_origins` falls back to `["*"]` combined with `allow_credentials=True`, which indicates a dangerous configuration pattern.

**Independent Test**: Can be tested by starting the API with `environment=production` and empty `cors_origins`, verifying startup fails with a clear error message.

**Acceptance Scenarios**:

1. **Given** environment is `production` and `cors_origins` is empty or `["*"]`, **When** the application starts, **Then** it MUST fail fast with a clear configuration error
2. **Given** environment is `development`, **When** `cors_origins` is empty, **Then** `["*"]` MAY be used as fallback with a warning log
3. **Given** `allow_credentials=True`, **Then** wildcard origins MUST never be configured regardless of environment

---

### User Story 3 - LLM Timeout Protection (Priority: P1)

As a system operator, I need all LLM calls to have explicit per-call timeouts, so that a single slow or hung LLM response cannot consume server resources indefinitely.

**Why this priority**: MEDIUM security finding affecting 6 locations. `timeout=None` on ChatAnthropic disables per-call timeout, creating a DoS vector even when outer `asyncio.timeout` is present.

**Independent Test**: Can be tested by verifying all ChatAnthropic instantiations include `timeout=60` and that no `timeout=None` patterns exist in the codebase.

**Acceptance Scenarios**:

1. **Given** any ChatAnthropic instance is created anywhere in the codebase, **Then** it MUST have `timeout` set to a value of 60 seconds or less
2. **Given** an LLM call exceeds the timeout, **Then** it raises `TimeoutError` which is caught and handled gracefully
3. **Given** a codebase scan for `timeout=None` patterns, **When** searching all ChatAnthropic constructor calls, **Then** zero matches are found

---

### User Story 4 - Cache Key Collision Prevention (Priority: P2)

As a system operator handling medical queries, I need cache keys to use full cryptographic hashes, so that hash collisions cannot cause a patient to receive cached answers for a different medical question.

**Why this priority**: MEDIUM finding in a patient-safety-critical context. SHA-256 truncated to 16 hex chars (64 bits) has non-trivial collision probability at scale.

**Independent Test**: Can be tested by verifying cache key generation uses full SHA-256 hex digest (64 chars) instead of truncated version.

**Acceptance Scenarios**:

1. **Given** a medical query is cached, **Then** the cache key uses the full SHA-256 hex digest (64 characters)
2. **Given** the cache invalidation logic, **Then** it uses `SCAN` pattern instead of `KEYS *` to avoid O(n) blocking

---

### User Story 5 - User ID Input Validation (Priority: P2)

As a system operator, I need user_id inputs to be validated for format and length, so that log injection and oversized payloads are prevented at the API boundary.

**Why this priority**: MEDIUM finding. Unvalidated user_id can inject newlines/special characters into logs and has no length limit.

**Independent Test**: Can be tested by sending requests with malicious user_id values (newlines, 10000+ chars, special characters) and verifying rejection.

**Acceptance Scenarios**:

1. **Given** a request with `user_id` containing newlines or control characters, **When** processed, **Then** the request is rejected with 400 error
2. **Given** a request with `user_id` longer than 64 characters, **When** processed, **Then** the request is rejected with 400 error
3. **Given** a valid `user_id` (alphanumeric, hyphens, underscores, max 64 chars), **Then** it is accepted

---

### User Story 6 - Docker Credentials Externalization (Priority: P2)

As a DevOps engineer, I need database credentials removed from docker-compose.yml and provided via environment injection, so that secrets are not committed to version control.

**Why this priority**: MEDIUM finding. Hardcoded `postgres:postgres` credentials and unauthenticated Redis in compose file.

**Independent Test**: Can be tested by verifying docker-compose.yml contains no inline credentials and references `.env` files for all secrets.

**Acceptance Scenarios**:

1. **Given** docker-compose.yml, **Then** it MUST NOT contain hardcoded database credentials
2. **Given** docker-compose.yml, **Then** all secrets MUST be provided via `env_file` or environment variable references
3. **Given** Redis configuration, **Then** `--requirepass` MUST be configured for production use
4. **Given** production compose profile, **Then** database and cache ports MUST NOT be exposed to `0.0.0.0`

---

### User Story 7 - Broken Test Cleanup (Priority: P2)

As a developer, I need stub and placeholder tests replaced with real behavioral tests or removed, so that the test suite accurately reflects code coverage and CI results are trustworthy.

**Why this priority**: Stub tests create false confidence. 4 test files contain placeholder assertions that pass but test nothing meaningful.

**Independent Test**: Can be tested by running the full test suite and verifying no tests contain `assert isinstance(graph, Pregel)` placeholders, `{"changeme": "some_val"}` stubs, or obsolete `"Echo:"` assertions.

**Acceptance Scenarios**:

1. **Given** `test_configuration.py`, **Then** placeholder `isinstance(graph, Pregel)` assertions are replaced with behavioral tests or the file is removed
2. **Given** `test_graph.py`, **Then** `{"changeme": "some_val"}` stub is replaced with valid State-based tests or removed
3. **Given** `test_graph_foundation.py`, **Then** obsolete `"Echo:"` behavior tests are updated or removed
4. **Given** `test_api_server.py` consult tests, **Then** tests that require live LLM/MCP are properly mocked or marked as integration tests

---

### User Story 8 - Cache Layer Test Coverage (Priority: P2)

As a developer, I need unit tests for the Redis cache layer, so that cache hit/miss/expiry behavior is verified independently of the full SSE flow.

**Why this priority**: HIGH coverage gap. `api/cache.py` has zero tests despite being critical infrastructure for quick mode responses.

**Independent Test**: Can be tested by running cache-specific unit tests with mocked Redis client.

**Acceptance Scenarios**:

1. **Given** a mock Redis client, **When** `get_cached_response` is called for an uncached query, **Then** it returns `None`
2. **Given** a previously cached response, **When** `get_cached_response` is called with the same query and mode, **Then** it returns the cached data
3. **Given** cache TTL has expired, **When** `get_cached_response` is called, **Then** it returns `None`
4. **Given** Redis is unavailable, **When** cache operations are attempted, **Then** they fail gracefully without affecting the main request flow

---

### User Story 9 - LLM Instance Reuse (Priority: P3)

As a system operator, I need LLM client instances to be reused across requests with identical parameters, so that connection setup overhead is eliminated and resource usage is optimized.

**Why this priority**: Architecture improvement. Each request creates new ChatAnthropic instances in supervisor, synthesizer, general_agent, and pubmed_agent, adding ~100ms overhead per instance.

**Independent Test**: Can be tested by verifying that multiple graph executions with the same model parameters share LLM instances.

**Acceptance Scenarios**:

1. **Given** two consecutive requests with the same model_name and temperature, **Then** the same ChatAnthropic instance is reused
2. **Given** requests with different model parameters, **Then** separate instances are created
3. **Given** LLM instance reuse with 10 concurrent requests, **When** all requests use the same model parameters, **Then** no exceptions are raised and all responses are returned correctly

---

### User Story 10 - Double Execution Elimination (Priority: P3)

As a system operator, I need the SSE streaming endpoint to reliably capture the final state from `astream_events()` without falling back to a second full graph execution via `ainvoke()`.

**Why this priority**: Architecture issue. When `astream_events()` doesn't capture the synthesizer output, the entire graph re-executes, doubling LLM costs and latency.

**Independent Test**: Can be tested by verifying SSE streaming always captures final state from the stream and the `ainvoke()` fallback is removed.

**Acceptance Scenarios**:

1. **Given** any consult request, **When** streaming completes, **Then** the final state is captured from stream events without requiring a fallback `ainvoke()` call
2. **Given** the streaming code, **Then** the double execution fallback block is removed or replaced with proper stream state capture

---

### User Story 11 - Dead Code Removal (Priority: P3)

As a developer, I need dead code removed from the codebase, so that the code accurately reflects actual behavior and reduces maintenance burden.

**Why this priority**: Code quality. `State.next` field is populated by every agent but never read. `RESEARCH_KEYWORDS` is duplicated between two modules.

**Independent Test**: Can be tested by verifying `State.next` is removed and `RESEARCH_KEYWORDS` exists in exactly one location.

**Acceptance Scenarios**:

1. **Given** the State dataclass, **Then** the `next` field is removed (or actually used by routing)
2. **Given** `RESEARCH_KEYWORDS`, **Then** it is defined in exactly one module and imported elsewhere
3. **Given** `source_filter` parameter in guidelines storage, **Then** the misleading parameter is removed from the public API and `"guidelines"` is hardcoded internally

---

### User Story 12 - Dependency Cleanup (Priority: P3)

As a developer, I need dependency specifications cleaned up for reproducible builds and consistent tooling versions.

**Why this priority**: Configuration hygiene. Duplicate deps with different versions, missing lock file, inconsistent project version, unused dependencies.

**Independent Test**: Can be tested by verifying `uv.lock` exists, no duplicate tool versions, and consistent version strings.

**Acceptance Scenarios**:

1. **Given** pyproject.toml, **Then** dev tool dependencies are defined in exactly one section without version conflicts
2. **Given** the repository, **Then** a `uv.lock` file is committed for reproducible builds
3. **Given** the project version, **Then** pyproject.toml and API metadata show the same version
4. **Given** dependencies, **Then** unused packages (e.g., `sse-starlette`) are removed

---

### Edge Cases

- What happens when CORS origins contain both specific origins AND `"*"`? System should reject this invalid configuration.
- How does cache key generation handle unicode/emoji in medical queries? SHA-256 handles arbitrary bytes, but encoding must be consistent (UTF-8).
- What happens when an LLM timeout occurs mid-stream after some SSE events have already been sent? The timeout error event must still be properly formatted.
- How does user_id validation interact with legitimate non-ASCII characters (e.g., Czech diacritics)? Decision: restrict to ASCII alphanumeric + hyphens/underscores for IDs.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST sanitize all error responses in production mode, replacing raw exception messages with generic error text
- **FR-002**: System MUST log full error details server-side regardless of what is sent to clients
- **FR-003**: System MUST fail fast on startup when CORS is misconfigured for production environment
- **FR-004**: System MUST set explicit timeout (max 60s) on all ChatAnthropic instances
- **FR-005**: System MUST use full SHA-256 hex digest for cache keys
- **FR-006**: System MUST use `SCAN` instead of `KEYS *` for Redis cache invalidation
- **FR-007**: System MUST validate `user_id` for format (alphanumeric + hyphens/underscores), length (max 64 chars), and absence of control characters
- **FR-008**: Docker compose MUST NOT contain hardcoded credentials
- **FR-009**: System MUST replace or remove all stub/placeholder tests
- **FR-010**: System MUST have unit tests for the Redis cache layer
- **FR-011**: System MUST reuse ChatAnthropic instances when model parameters are identical
- **FR-012**: System MUST capture final state from SSE stream events without double execution fallback
- **FR-013**: System MUST remove dead `State.next` field or implement its routing purpose
- **FR-014**: System MUST consolidate `RESEARCH_KEYWORDS` into a single source of truth
- **FR-015**: System MUST commit a `uv.lock` file for reproducible builds
- **FR-016**: System MUST have consistent version string `0.2.0` across pyproject.toml and API metadata
- **FR-017**: System MUST remove unused dependencies
- **FR-018**: Health endpoint MUST NOT expose raw database error strings to unauthenticated callers

### Key Entities

- **CacheKey**: Represents a unique identifier for cached medical query responses, derived from query text and mode using full SHA-256 hash
- **ErrorResponse**: Represents a sanitized error sent to clients, containing error type and generic detail message (no internal info in production)
- **UserIdentifier**: Represents a validated user ID, constrained to alphanumeric characters, hyphens, and underscores with max 64 char length

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Zero instances of raw exception messages sent to clients in production mode across all API endpoints
- **SC-002**: Application fails to start within 5 seconds when CORS is misconfigured for production
- **SC-003**: All LLM client instances have explicit timeout of 60 seconds or less — verified by automated code scan finding zero `timeout=None` patterns
- **SC-004**: Cache key length is exactly 64 hex characters (full SHA-256) for all cached queries
- **SC-005**: All stub/placeholder tests are removed or replaced — zero tests containing `changeme`, `isinstance(graph, Pregel)` placeholders, or obsolete behavior assertions
- **SC-006**: Cache layer has minimum 80% unit test coverage with at least 4 test scenarios (hit, miss, expiry, unavailable)
- **SC-007**: No hardcoded credentials exist in any compose or configuration file committed to the repository
- **SC-008**: `user_id` values with control characters, newlines, or length >64 are rejected with 400 status
- **SC-009**: `RESEARCH_KEYWORDS` is defined in exactly one module
- **SC-010**: `uv.lock` file is committed and produces deterministic dependency resolution
- **SC-011**: Zero HIGH security findings remain; MEDIUM findings reduced from 6 to ≤2 (items deferred to separate features are excluded from count)
- **SC-012**: Test suite maintains 449+ passing unit tests with zero stub tests
