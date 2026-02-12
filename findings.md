# Czech MedAI - Research & Findings

**Updated**: 2026-02-11

---

## Architecture Findings

### MCP Protocol Differences
- **SÚKL-mcp** (sukl-mcp-ts.vercel.app): MCP Streamable HTTP transport → JSON-RPC 2.0
  - Endpoint: single POST to base URL
  - Methods: `tools/call`, `tools/list`
  - Response: `{jsonrpc, result: {content: [{type, text}]}, id}`
- **BioMCP**: Traditional REST API
  - Endpoint: POST `/tools/{tool_name}`
  - Response: direct JSON body

### Routing Analysis
- Generic medical terms (léčba, diabetes, terapie) removed from RESEARCH_KEYWORDS
  - Reason: Overlap with drug queries caused misrouting
  - Impact: "léčba diabetu" now goes to placeholder (supervisor LLM handles it)
  - Mitigation: LLM supervisor classifies ambiguous queries correctly
- Drug keywords are most common in Czech medical queries → prioritized

### Security Findings (Code Review 2026-02-11)
1. **JSON parsing** - No size limits on untrusted MCP server responses → Fixed: 1 MB limit
2. **Request IDs** - `self._request_id += 1` not atomic → Fixed: `itertools.count()`
3. **Session cleanup** - No `__aenter__`/`__aexit__` → Fixed: async context manager
4. **Regex ReDoS** - Non-anchored pattern with backtracking → Fixed: line-anchored pattern
5. **Supervisor exceptions** - Broad `except Exception` → Fixed: specific exception types

### Test Environment Issue
- `uv run pytest` and `.venv/bin/pytest` hang during module import
- Likely cause: heavy dependency graph (langgraph, langchain_anthropic) at import time
- graph.py imports trigger MCP client initialization → network calls at import
- Workaround: Test individual modules, or use `--import-mode=importlib`

---

## Frontend Findings

### Design Token System
- OKLCH color space in `globals.css`
- Semantic tokens: `--color-surface`, `--color-text-primary`, etc.
- Light/dark auto-switch via `next-themes`
- Citation-specific tokens: `--citation-badge-hover`, `--citation-badge-active`

### SSE Protocol
- Events: agent_start → agent_complete → final → done
- Error handling via `error` event type
- Cache hits via `cache_hit` event (quick mode only)

---

## Codebase Metrics

| Metric | Value |
|--------|-------|
| Python source files | ~25 |
| TypeScript source files | ~30 |
| Unit tests (Python) | ~50+ |
| Unit tests (Frontend) | Vitest + Playwright |
| LangGraph nodes | 7 (supervisor, drug, pubmed, guidelines, translate x2, synthesizer) |
| MCP tools mapped | 12 SÚKL tools |
