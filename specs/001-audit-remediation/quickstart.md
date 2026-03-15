# Quickstart: Audit Remediation

**Branch**: `001-audit-remediation`

## Prerequisites

- Python >=3.10, Node.js >=18
- Redis running locally (or Docker)
- PostgreSQL with pgvector (or Docker)

## Implementation Order

### PR 1: P1 Security Fixes (US1-US3)

```bash
# 1. Error sanitization (routes.py, main.py)
# 2. CORS validation (config.py, main.py)
# 3. LLM timeouts (constants.py + 6 node files)

# Verify
PYTHONPATH=src uv run pytest tests/ -v
grep -rn "timeout=None" src/agent/nodes/  # Should return 0 results
```

### PR 2: P2 Hardening (US4-US8)

```bash
# 1. Cache key fix (cache.py — remove [:16])
# 2. SCAN invalidation (cache.py)
# 3. user_id validation (schemas.py)
# 4. Docker credentials (docker-compose.yml)
# 5. Test cleanup (4 test files)
# 6. Cache tests (new test file)

# Verify
PYTHONPATH=src uv run pytest tests/ -v
grep -rn "changeme\|isinstance(graph, Pregel)" tests/  # Should return 0
```

### PR 3: P3 Cleanup (US9-US12)

```bash
# 1. LLM instance reuse (new utility + node updates)
# 2. Double execution removal (routes.py)
# 3. Dead code (State.next, RESEARCH_KEYWORDS dedup, source_filter)
# 4. Dependencies (pyproject.toml, uv.lock, version 0.2.0)

# Verify
PYTHONPATH=src uv run pytest tests/ -v
grep -rn '"next": "__end__"' src/agent/nodes/  # Should return 0
uv lock  # Should produce uv.lock
```

## Validation

After all 3 PRs merged:

```bash
# Full test suite
PYTHONPATH=src uv run pytest tests/ -v

# Lint + type check
uv run ruff format . && uv run ruff check . && uv run mypy --strict src/agent/

# Version consistency
grep 'version' langgraph-app/pyproject.toml  # 0.2.0
grep 'version' langgraph-app/src/api/main.py  # 0.2.0

# Security checks
grep -rn 'timeout=None' src/  # 0 results
grep -rn 'str(e)' src/api/routes.py  # 0 results in error handlers
grep -rn 'postgres:postgres' docker-compose.yml  # 0 results
```
