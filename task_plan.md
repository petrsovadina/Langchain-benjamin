# Czech MedAI - Task Plan

**Project**: Czech MedAI (Benjamin)
**Updated**: 2026-02-11
**Branch**: main

---

## Current Phase: Post-Phase 0 Stabilization

### Completed Phases
- [x] **Phase 0: Foundation** - LangGraph setup, MCP infrastructure
- [x] **Phase 1: Core Agents** - SÚKL drug agent, BioMCP PubMed agent, Guidelines agent
- [x] **Phase 2: Integration** - Supervisor orchestration, Synthesizer, Translation sandwich
- [x] **Phase 3: UX** - FastAPI backend (SSE), Next.js frontend (chat UI, citations)

### Current Work: Security Hardening & Code Quality
- [x] Migrate SÚKL MCP client REST → JSON-RPC protocol
- [x] Fix routing priority (drug > research > guidelines)
- [x] Address Copilot PR review comments
- [x] Security hardening: size limits, thread-safe IDs, async context manager
- [x] Fix supervisor fallback keyword priority mismatch
- [x] Add routing regression tests
- [ ] Run full test suite to verify all changes
- [ ] Fix Feature 004: VZP Pricing Agent (not yet implemented)

### Next Priority: Production Readiness
- [ ] Fix remaining mypy --strict violations
- [ ] Improve test coverage to ≥80%
- [ ] Remove Translation Sandwich Pattern (CZ→EN→CZ) - use native Claude multilingual
- [ ] Implement Feature 004: VZP Pricing Agent
- [ ] Production Docker setup with health checks
- [ ] CI/CD pipeline (GitHub Actions already partially set up)

---

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| MCP Protocol | JSON-RPC for SÚKL, REST for BioMCP | Server implementations differ |
| Routing Priority | Drug > Research > Guidelines | Most common use case first |
| Default SUKL_MCP_URL | http://localhost:3000 | Consistent with MCPConfig.from_env() |
| Request ID generation | itertools.count() | Thread-safe, no locking overhead |
| Content size limits | 1 MB max | Prevent DoS from untrusted MCP servers |

---

## Open Issues

1. **VZP Pricing Agent** - Feature 004 not implemented (P1)
2. **Translation Layer** - Sandwich pattern adds latency; refactoring spec ready
3. **Test environment** - uv/pytest setup hangs on import (investigate dependency graph)
4. **Unused `review` branch** - was used for PR review, can be cleaned up
