# API Contract Changes: Audit Remediation

**Date**: 2026-03-12

## No New Endpoints

This feature modifies existing endpoint behavior only.

## Modified Behavior

### POST /api/v1/consult

**Request body change**: `user_id` field now validated

```json
{
  "query": "Jaké jsou kontraindikace metforminu?",
  "mode": "quick",
  "user_id": "user-123"  // NEW: must match ^[a-zA-Z0-9_-]{1,64}$ or null
}
```

**Error response (400)** for invalid user_id:
```json
{
  "error": "validation_error",
  "detail": "user_id must be alphanumeric with hyphens/underscores, max 64 chars"
}
```

**SSE error event change** (production mode):

Before:
```
event: error
data: {"type": "error", "error": "internal_error", "detail": "ConnectionRefusedError: [Errno 111] Connection refused"}
```

After:
```
event: error
data: {"type": "error", "error": "internal_error", "detail": "An unexpected error occurred"}
```

### GET /health

**Response change**: Sanitized component status

Before:
```json
{
  "status": "degraded",
  "mcp_servers": {"sukl": "error: ConnectionRefusedError: [Errno 111]"},
  "database": "error: asyncpg.exceptions.ConnectionDoesNotExistError: connection lost",
  "version": "0.1.0"
}
```

After:
```json
{
  "status": "degraded",
  "mcp_servers": {"sukl": "error"},
  "database": "error",
  "version": "0.2.0"
}
```

### GET /

**Response change**: Version bump

```json
{
  "name": "Czech MedAI API",
  "version": "0.2.0",
  "description": "AI asistent pro české lékaře",
  "docs": "/docs",
  "health": "/health"
}
```

## Breaking Changes

1. **Cache keys change format** — existing cached responses will not be found (cache miss, not error). Cache is ephemeral, self-healing.
2. **user_id validation** — previously accepted arbitrary strings, now restricted. Clients sending non-alphanumeric user_ids will get 400 errors.
3. **Error detail messages** — clients parsing raw exception text from SSE errors will now receive generic messages in production.
