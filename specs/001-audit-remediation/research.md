# Research: Audit Remediation

**Date**: 2026-03-12
**Branch**: `001-audit-remediation`

## R1: Error Response Sanitization Pattern

**Decision**: Use `settings.environment` check to conditionally include error details. Production sends generic message, development sends `str(e)`.

**Rationale**: FastAPI global exception handler (`main.py:224-234`) already uses `app.debug` for this pattern. SSE stream errors (`routes.py:313-322`) and health endpoint (`routes.py:72,88,100,104`) do not. Align all error paths with the same pattern.

**Affected files**:
- `routes.py:313-322` — SSE catch-all: replace `"detail": str(e)` with conditional
- `routes.py:72` — Health SUKL: `f"error: {str(e)}"` → `"error"` in production
- `routes.py:88` — Health BioMCP: same pattern
- `routes.py:100,104` — Health DB: same pattern

**Implementation**: Import `settings` from `api.config`, check `settings.environment != "production"` before including raw error details.

## R2: CORS Startup Validation

**Decision**: Add `@field_validator("cors_origins")` to `Settings` class that validates non-empty, non-wildcard when `environment == "production"`. Additionally add a startup check in `lifespan()`.

**Rationale**: Pydantic validators run at Settings instantiation time, which happens at module import. This provides the earliest possible fail-fast. The lifespan check serves as a belt-and-suspenders defense.

**Affected files**:
- `config.py` — Add validator for CORS+credentials combination
- `main.py:131` — Remove `["*"]` fallback, use `settings.cors_origins` directly

**Alternative rejected**: Runtime-only check in middleware (too late, requests already processed).

## R3: ChatAnthropic timeout=None Locations

**Decision**: Replace all `timeout=None` with `timeout=60` (configurable via constant `LLM_TIMEOUT = 60`).

**Rationale**: Found 6 instances of `timeout=None`:
1. `supervisor.py:129` — IntentClassifier lazy init
2. `synthesizer.py:607` — synthesizer_node
3. `general_agent.py:65` — general_agent_node
4. `pubmed_agent.py:381` — internal CZ→EN translation
5. `translation.py:73` — translate_to_english_node
6. `translation.py:145` — translate_results_to_czech_node

**Implementation**: Add `LLM_TIMEOUT = 60` constant to `agent/constants.py`, import in all 6 files.

## R4: Cache Key Full SHA-256

**Decision**: Remove `[:16]` truncation from `cache.py:66`.

**Rationale**: `hashlib.sha256(query.encode()).hexdigest()[:16]` produces only 16 hex chars (64 bits). Full `hexdigest()` produces 64 hex chars (256 bits). Change is a one-liner. Existing cached data will be missed (keys change), which is acceptable — cache is ephemeral.

**Affected files**: `cache.py:66` — Remove `[:16]`

## R5: Cache Invalidation SCAN Pattern

**Decision**: Replace `client.keys(pattern)` with async `SCAN` cursor iteration.

**Rationale**: `KEYS *` is O(n) and blocks Redis for the duration. `SCAN` is cursor-based and non-blocking. Redis docs explicitly recommend SCAN over KEYS for production.

**Affected files**: `cache.py:143` — Replace `keys()` with `scan_iter()`

**Implementation**:
```python
async def invalidate_cache(pattern: str = "consult:*") -> int:
    client = await get_redis_client()
    if client is None:
        return 0
    try:
        deleted = 0
        async for key in client.scan_iter(match=pattern, count=100):
            await client.delete(key)
            deleted += 1
        return deleted
    except RedisError as e:
        logger.warning(f"Redis invalidate error: {e}")
        return 0
```

## R6: user_id Validation

**Decision**: Add Pydantic `field_validator` on `ConsultRequest.user_id` in `schemas.py`.

**Rationale**: Currently `user_id: str | None = Field(default=None)` with no validation. Need regex `^[a-zA-Z0-9_-]{1,64}$` when provided.

**Affected files**: `schemas.py:33` — Add validator

## R7: Docker Credentials Externalization

**Decision**: Replace inline `POSTGRES_USER/PASSWORD` with `${POSTGRES_USER}` env var references and add `.env.docker` template.

**Rationale**: `docker-compose.yml:15` has `DATABASE_URL=postgresql://postgres:postgres@...` and lines 48-49 have hardcoded `POSTGRES_USER=postgres`, `POSTGRES_PASSWORD=postgres`. Both `env_file: .env.production` and inline `environment:` exist — inline overrides env_file, defeating the purpose.

**Affected files**:
- `docker-compose.yml` — Remove inline credentials, add Redis `--requirepass`, bind ports to `127.0.0.1`
- `.env.docker.example` — New template with placeholder credentials

## R8: State.next Dead Field

**Decision**: Remove `next` field from State dataclass and all `"next": "__end__"` returns from agent nodes.

**Rationale**: Found 20+ occurrences of `"next": "__end__"` across all agent nodes, but no graph edge reads this field. The `_keep_last` reducer exists but routing uses `Send` API, not `next` field.

**Affected files**:
- `graph.py` — Remove `next` from State, remove `_keep_last` reducer (if unused elsewhere)
- `drug_agent.py` — Remove `"next": "__end__"` from 3 return dicts
- `pubmed_agent.py` — Remove from 5 return dicts
- `guidelines_agent.py` — Remove from 5 return dicts
- `synthesizer.py` — Remove from 3 return dicts
- `general_agent.py` — Remove from 2 return dicts

## R9: RESEARCH_KEYWORDS Consolidation

**Decision**: Keep canonical set in `graph.py`, remove duplicate from `pubmed_agent.py`, import from `graph.py`.

**Rationale**: `graph.py:257` and `pubmed_agent.py:60` define separate `RESEARCH_KEYWORDS` sets. `supervisor.py:230` imports from `graph.py`. PubMed agent's set is used internally for query detection but should use the canonical set.

**Affected files**:
- `pubmed_agent.py:60-77` — Replace local definition with import from `graph.py`
- `pubmed_agent.py:120` — Already uses variable name, no change needed

## R10: Dependency Cleanup

**Decision**: Consolidate dev deps into `[dependency-groups]` only, remove `[project.optional-dependencies]`, add missing `pytest` to proper section, remove `sse-starlette`.

**Rationale**:
- `[project.optional-dependencies].dev` has `mypy>=1.11.1`, `ruff>=0.6.1`
- `[dependency-groups].dev` has `mypy>=1.13.0`, `ruff>=0.8.2` (newer)
- `sse-starlette>=2.1.3` is in deps but code uses manual `StreamingResponse`
- `pytest` is in `[dependency-groups]` but not in `[project.optional-dependencies]`

**Implementation**: Keep `[dependency-groups]` (newer versions, has pytest), remove `[project.optional-dependencies]` section, remove `sse-starlette` from main deps.

## R11: Version Unification

**Decision**: Set `0.2.0` everywhere per clarification decision.

**Affected files**:
- `pyproject.toml:3` — `version = "0.0.1"` → `"0.2.0"`
- `pyproject.toml:4` — Update description from template text
- `pyproject.toml:5-7` — Update author from template
- `main.py:99` — `version="0.1.0"` → `"0.2.0"`
- `routes.py:112` — `version="0.1.0"` → `"0.2.0"`
- `schemas.py:258,260` — HealthCheckResponse default/example version
- `main.py:254` — Root endpoint version

## R12: Double Execution Fallback

**Decision**: Replace `ainvoke()` fallback with proper state capture from `astream_events()` using `on_chain_end` for the root graph.

**Rationale**: `routes.py:253-270` re-invokes the entire graph if `final_state is None` after streaming. The root cause is that `final_state` is only captured from `event.name == "synthesizer"`, but the synthesizer event name may not match exactly in `astream_events` v2. Solution: capture state from the root chain end event instead.

**Affected files**: `routes.py:200-270` — Rewrite state capture logic

## R13: source_filter Bug

**Decision**: Fix the parameter to actually use the provided value, or document the current behavior and remove the misleading parameter.

**Rationale**: `guidelines_storage.py:454` maps `source_filter` to hardcoded `"guidelines"` regardless of input. Since only guidelines are stored in this table, the parameter is misleading but not broken. Best approach: remove the parameter and hardcode the filter internally.

**Affected files**: `guidelines_storage.py` — Remove `source_filter` parameter from public API
