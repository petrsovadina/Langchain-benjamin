# Data Model: Audit Remediation

**Date**: 2026-03-12

## Entity Changes

This feature primarily modifies existing entities rather than creating new ones.

### Modified: ConsultRequest (schemas.py)

**Change**: Add `user_id` validation

| Field   | Type         | Validation                                        | Change |
|---------|--------------|---------------------------------------------------|--------|
| query   | str          | 1-1000 chars, sanitized (existing)                | None   |
| mode    | Literal      | "quick" \| "deep" (existing)                      | None   |
| user_id | str \| None  | `^[a-zA-Z0-9_-]{1,64}$` when provided             | **New validator** |

### Modified: HealthCheckResponse (schemas.py)

**Change**: Sanitize error details in component status fields

| Field       | Type         | Change                                     |
|-------------|--------------|---------------------------------------------|
| status      | Literal      | No change                                   |
| mcp_servers | Dict[str,str]| Values MUST be "available", "unavailable", or "error" (no raw details) |
| database    | str \| None  | Values MUST be "available", "unavailable", or "error" (no raw details) |
| version     | str          | Default changed from "0.1.0" to "0.2.0"    |

### Modified: State (graph.py)

**Change**: Remove dead `next` field

| Field          | Type                              | Change      |
|----------------|-----------------------------------|-------------|
| messages       | Annotated[list, add_messages]     | No change   |
| ~~next~~       | ~~Annotated[str, _keep_last]~~    | **Removed** |
| retrieved_docs | Annotated[list, add_documents]    | No change   |
| drug_query     | DrugQuery \| None                 | No change   |
| research_query | ResearchQuery \| None             | No change   |
| guideline_query| GuidelineQuery \| None            | No change   |

### New: Constants (constants.py)

| Constant    | Value | Purpose                            |
|-------------|-------|------------------------------------|
| LLM_TIMEOUT | 60    | Per-call timeout for ChatAnthropic |

### Modified: CacheKey generation (cache.py)

| Before                          | After                        |
|---------------------------------|------------------------------|
| `hexdigest()[:16]` (64 bits)   | `hexdigest()` (256 bits)     |
| Key: `consult:abc123def456ab:quick` | Key: `consult:<64-char-hash>:quick` |

## State Transitions

No new state transitions. Existing graph flow unchanged:

```
supervisor → [drug_agent|pubmed_agent|guidelines_agent|general_agent] → synthesizer
```

The `"next": "__end__"` return values in agent nodes are dead code and will be removed.
Agent routing continues to use `Send` API exclusively.
