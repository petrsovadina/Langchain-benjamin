# Czech MedAI — Stav projektu

**Vygenerováno**: 2026-02-27 | **Branch**: `013-supabase-migration` | **Konstituce**: v1.2.1

---

## Souhrnný přehled

Czech MedAI je **v pokročilé fázi implementace**. Z 12 plánovaných features
roadmapy je 9 plně implementováno, 1 částečně a 2 neimplementovány. Projekt
je výrazně dále než naznačují formální specifikace — features 006–012 byly
implementovány bez formálního SpecKit workflow.

```
Roadmap:   ████████████████████░░░░  83 % features implementováno
Testy:     ████████████████████████  538 backend (449 unit + 89 integration) + 27 e2e + 17 unit frontend
Spec gap:  7/12 features nemá formální specifikaci (ale jsou implementovány)
Blokující: DB migrace (guidelines tabulka), Feature 004 (VZP)
```

---

## Fáze vs. realita

### Phase 0: Foundation — DOKONČENO 100 %

| # | Feature | Spec | Impl. | Stav | Poznámka |
|---|---------|:----:|:-----:|:----:|----------|
| 001 | LangGraph Foundation | ✅ | ✅ | **HOTOVO** | State (6 polí), Context (9 polí), graph kompilace, route_query |
| 002 | MCP Infrastructure | ✅ | ✅ | **HOTOVO** | SUKLMCPClient (8 tools, JSON-RPC), BioMCPClient (24 tools, REST), IMCPClient interface, retry, health check |

**Detaily 001**: State dataclass s messages, next, retrieved_docs, drug_query, research_query, guideline_query. Context TypedDict s model_name (claude-sonnet-4-5), temperature, sukl_mcp_client, biomcp_client, mode (quick/deep). Graph: `__start__ → supervisor → [agents] → synthesizer → __end__`.

**Detaily 002**: SÚKL — JSON-RPC 2.0 na `sukl-mcp-ts.vercel.app/mcp`, 8 nástrojů (search-medicine, get-medicine-details, get-atc-info, get-reimbursement, check-availability, get-pil-content, get-spc-content, find-pharmacies). BioMCP — REST POST na `/tools/{name}`, Docker-based. Oba: thread-safe ID generace, size limity (1 MB), ReDoS-safe regex, async context manager.

---

### Phase 1: Core Agents — 75 % (3/4)

| # | Feature | Spec | Impl. | Stav | Poznámka |
|---|---------|:----:|:-----:|:----:|----------|
| 003 | SÚKL Drug Agent | ✅ | ✅ | **HOTOVO** | 6 typů dotazů, fuzzy search, regex extrakce, české chybové zprávy |
| 004 | VZP Pricing Agent | ❌ | ❌ | **NEIMPLEMENTOVÁNO** | Žádný kód, žádná specifikace |
| 005 | BioMCP PubMed Agent | ✅ | ✅ | **HOTOVO** | Interní CZ→EN překlad, article_searcher + article_getter, inline citace |
| 006 | Guidelines Agent | ❌ | ⚠️ | **ČÁSTEČNĚ** | Node existuje a funguje, ale chybí DB migrační skript |

**Detaily 003 (drug_agent)**:
- 6 typů dotazů: search, details, reimbursement, availability, atc, ingredient
- `extract_drug_name()` — regex extrakce z českých frází ("Na co je...", "Jaká je dostupnost...")
- `classify_drug_query()` — pattern matching pro ATC kódy, keyword listy
- Timeout: 10 s, zobrazení top 5 výsledků
- MCP volání: search_drugs, get_drug_details, get_reimbursement, check_availability, search_by_atc, search_by_ingredient
- **Plně funkční** s reálným SÚKL MCP serverem

**Detaily 004 (VZP)**: Jediná zcela chybějící feature z Phase 1. V kódu neexistuje žádný `vzp_agent`. Roadmap odhaduje 6 dní práce.

**Detaily 005 (pubmed_agent)**:
- Interní CZ→EN překlad přes LLM (`CZ_TO_EN_PROMPT`) — zachovává latinské termíny, expanduje zkratky (DM2→type 2 diabetes)
- BioMCP tools: article_searcher, article_getter
- Formátování citací: "Smith et al. (2024)" + References sekce
- Timeout: 15 s
- **Plně funkční** s BioMCP Docker serverem

**Detaily 006 (guidelines_agent)**:
- Node `guidelines_agent_node` existuje a funguje
- Dva režimy: SECTION_LOOKUP (přímý SQL podle guideline_id) a SEARCH (pgvector sémantické vyhledávání)
- Embeddings: OpenAI text-embedding-ada-002 (1536 dimenzí)
- Similarity threshold: 0.7 (hardcoded)
- **CO CHYBÍ**: SQL migrační skript pro `guidelines` tabulku není v repozitáři. Kód předpokládá strukturu: external_id, title, organization, full_content, embedding, source_type, keywords, icd10_codes.

---

### Phase 2: Integration — DOKONČENO 100 %

| # | Feature | Spec | Impl. | Stav | Poznámka |
|---|---------|:----:|:-----:|:----:|----------|
| 007 | Supervisor Orchestration | ❌ | ✅ | **HOTOVO** | LLM intent klasifikace (8 typů), Send API, keyword fallback |
| 008 | Citation System | ❌ | ✅ | **HOTOVO** | Inline [1][2][3], CitedResponse, CitationBadge, CitationPopup, ReferencesSection |
| 009 | Synthesizer Node | ❌ | ✅ | **HOTOVO** | Multi-agent kombinování, renumbering citací, česká terminologie |

**Detaily 007 (supervisor)**:
- `IntentClassifier` — Claude function calling s 8 intent typy
- `fallback_to_keyword_routing()` — single source of truth pro keyword matching
- Keyword sety: 29 drug, 15 research, 17 guidelines
- Priorita: Drug > Research > Guidelines > General
- Nízká confidence (<0.5) logována jako warning
- Přeskakuje nedostupné agenty (bez SÚKL → bez drug_agent)
- **Plně funkční**

**Detaily 008 (citation system)**:
- Backend: `extract_citations_from_message()`, `renumber_citations()` v synthesizer.py
- Frontend: `CitedResponse` (parser + renderer), `CitationBadge` (hover preview + click dialog), `CitationPopup` (plný detail s externím odkazem), `ReferencesSection` (číslovaný seznam)
- `citations.ts` — `parseCitations()` regex `/\[(\d+)\]/g`, segmentuje text na text/citation
- 3 formátovače: SÚKL, PubMed, Guidelines
- **Plně funkční end-to-end**

**Detaily 009 (synthesizer)**:
- Single agent: pass-through s minimálním zpracováním
- Multi-agent: globální přečíslování citací → LLM syntéza → česká terminologie validace
- `validate_czech_terminology()` — 14 českých zkratek (DM2T, ICHS, IM...)
- Quick mode: max 5 vět, Deep mode: plná LLM syntéza se sekcemi
- Fallback: konkatenace pokud LLM syntéza selže
- **Plně funkční**

---

### Phase 3: UX & Deployment — 67 % (2/3)

| # | Feature | Spec | Impl. | Stav | Poznámka |
|---|---------|:----:|:-----:|:----:|----------|
| 010 | Czech Localization | ❌ | ⚠️ | **ČÁSTEČNĚ** | UI je česky, 14 lékařských zkratek, ale žádný systematický lokalizační systém |
| 011 | FastAPI Backend | ❌ | ✅ | **HOTOVO** | 3 endpointy, SSE streaming, Redis cache, rate limiting, security headers |
| 012 | Next.js Frontend | ❌ | ✅ | **HOTOVO** | Production-ready, 14 komponent, WCAG 2.1 AA, dark mode, 27 e2e testů |

**Detaily 010 (lokalizace)**:
- UI kompletně v češtině (všechny prompty, chybové zprávy, labely)
- 14 lékařských zkratek v `validate_czech_terminology()`
- Chybí: systematický slovník medicínských zkratek, i18n framework, překlad abstracts z angličtiny
- Roadmap odhaduje 4 dny práce

**Detaily 011 (FastAPI)**:
- 3 endpointy: `GET /` (info), `GET /health` (MCP + DB status), `POST /api/v1/consult` (SSE)
- Middleware stack: CORS, rate limiting (10/min), request ID (UUID v4), security headers (HSTS, CSP, X-Frame-Options), process time tracking
- Redis cache: SHA256 klíče, TTL 1h, jen quick mode
- Timeout: 30 s pro graph execution
- Konfigurace: 57+ env proměnných, Pydantic Settings
- Health check: ověřuje MCP klienty + DB konektivitu, degraded/healthy status
- **Plně funkční, production-ready**

**Detaily 012 (Next.js Frontend)**:
- 14 React komponent: Omnibox, ChatLayout, UserMessage, AssistantMessage, CitedResponse, CitationBadge, CitationPopup, ReferencesSection, AgentThoughtStream, ProgressBar, ErrorBoundary, MessageSkeleton, OfflineBanner, ThemeProvider
- 4 hooks: useConsult (SSE + retry), useRetry (exponential backoff), useOnlineStatus, useSwipeGesture
- SSE klient v `api.ts`: reader-based streaming, `\n\n` delimiter parsing
- Design system: OKLCH color space, 11 shade paleta, light/dark auto-switch
- shadcn/ui: Button (6 variant × 10 velikostí), Badge, Card, Dialog, HoverCard, Input, Popover, ScrollArea, Skeleton
- Accessibility: WCAG 2.1 AA, jest-axe validace, 44px touch targets, skip link, aria-live regions
- **Production-ready, NE prototyp**

---

### Extra: Supabase Migration

| # | Feature | Spec | Impl. | Stav | Poznámka |
|---|---------|:----:|:-----:|:----:|----------|
| 013 | Supabase Migration | ✅ | ⚠️ | **ČÁSTEČNĚ** | asyncpg storage hotov, InsForge odstraněn, ale chybí DB migrační skript |

**Co je hotovo**:
- `.mcp.json` přepnut z InsForge na Supabase (projekt `higziqzcjmtmkzxbbzik`)
- `guidelines_storage.py` přepsán na asyncpg: connection pool (min 2, max 10), SSL, INSERT s ON CONFLICT, pgvector `<->` cosine distance
- Sloupce přejmenovány: guideline_id→external_id, content→full_content, source→source_type (enum), metadata JSONB dekomponován na keywords + icd10_codes
- UUID primární klíče místo SERIAL
- AGENTS.md (InsForge docs) smazán
- Konstituce aktualizována na v1.2.0 (dual persistence model)

**Co chybí**:
- SQL migrační skript pro vytvoření `guidelines` tabulky s pgvector
- Seed data / populace guidelines databáze
- Integrační test s live Supabase instancí

---

## Testovací pokrytí

### Backend (langgraph-app/)

| Kategorie | Testů | Soubory | Pokrytí |
|-----------|------:|--------:|---------|
| MCP Infrastructure | 91 | 7 | SUKLClient (20), BioMCPClient (4), config (18), entities (17), exceptions (15), ports (5), retry (2) |
| Nodes | 120 | 5 | supervisor (35), synthesizer (33), guidelines_agent (19), pubmed_agent (18), drug_agent (15) |
| Models | 37 | 1 | GuidelineQuery, GuidelineSection, validátory |
| Utils | 29 | 2 | guidelines_storage (6), pdf_processor (23) |
| Routing | 21 | 2 | fallback_to_keyword_routing (20), konfigurace (1) |
| Translation | 6 | 1 | CZ↔EN překlad (5 failing — unmocked LLM) |
| **Unit celkem** | **449** | — | ověřeno `pytest --co -q` |
| Integration | 89 | — | API server, parallel execution, synthesizer flow, MCP |
| **Backend celkem** | **538** | — | 444 unit passing + 5 failing + 89 integration |

### Frontend (frontend/)

| Kategorie | Testů/souborů | Pokrytí |
|-----------|-------------:|---------|
| Unit testy (Vitest) | 17 souborů | Omnibox, AssistantMessage, AgentThoughtStream, ErrorBoundary, MessageSkeleton, ProgressBar, OfflineBanner, Button (6×10), Badge, Dialog, HoverCard, CitationBadge, Card, ScrollArea, citations.ts |
| E2E testy (Playwright) | 27 testů / 5 souborů | Chat workflow (4), Citations (3), Accessibility (4), Mobile (4), Visual regression (16) |
| **Frontend celkem** | **17 unit + 27 e2e** | |

### Mezery v testech

| Oblast | Chybí |
|--------|-------|
| FastAPI rate limiting | Žádný test enforcement 10/min limitu |
| Query sanitization | XSS/SQL injection patterns v ConsultRequest |
| SSE timeout handling | 30s limit v consult streamu |
| Redis integrace | Cache miss/hit s reálným Redis |
| Performance testy | `test_pubmed_latency.py` je prázdný stub |
| Guidelines DB integrace | Žádný test s reálnou Supabase instancí |
| Confidence scoring | routes.py:301 — `"confidence": 0.0  # TODO` |

---

## Architektura — zdraví systému

### Silné stránky

| Oblast | Hodnocení | Detail |
|--------|:---------:|--------|
| Hexagonal architektura | ★★★★★ | IMCPClient port + adaptery (SÚKL, BioMCP) |
| Type safety | ★★★★★ | mypy --strict, Pydantic validátory na všech modelech |
| Error handling | ★★★★☆ | Specifické výjimky, graceful degradation, ale `confidence: 0.0` TODO |
| Async-first | ★★★★★ | Veškeré I/O plně async, connection pools |
| Security | ★★★★☆ | Thread-safe IDs, size limity, ReDoS-safe regex, HSTS, CSP. Chybí: JWT autentizace |
| Observability | ★★★★☆ | LangSmith tracing, structured JSON logging, request ID tracking. Chybí: Sentry integrace |
| Frontend kvalita | ★★★★★ | WCAG 2.1 AA, TypeScript strict, design system, 27 e2e testů |
| DRY | ★★★★★ | Shared helpers, single source of truth pro routing, re-exporty z `__init__` |

### Technický dluh

| Položka | Závažnost | Soubor | Detail |
|---------|:---------:|--------|--------|
| Confidence scoring | Střední | `routes.py:301` | Hardcoded `0.0`, TODO komentář |
| DB migrace | **Vysoká** | — | Chybí SQL pro `guidelines` tabulku |
| Python version mismatch | Nízká | Dockerfile vs langgraph.json | 3.11 vs 3.12 |
| Mic/Upload buttons | Nízká | `Omnibox.tsx` | UI wired ale handlery nefunkční |
| Prázdný performance test | Nízká | `test_pubmed_latency.py` | Stub soubor |

---

## Souhrnná matice completeness

```
Feature                     Spec  Plan  Tasks  Code  Tests  Docs  Status
─────────────────────────────────────────────────────────────────────────
001 LangGraph Foundation     ✅    ✅     ✅     ✅     ✅     ✅    DONE
002 MCP Infrastructure       ✅    ✅     ✅     ✅     ✅     ✅    DONE
003 SÚKL Drug Agent          ✅    ✅     ✅     ✅     ✅     ✅    DONE
004 VZP Pricing Agent        ❌    ❌     ❌     ❌     ❌     ❌    NOT STARTED
005 BioMCP PubMed Agent      ✅    ✅     ✅     ✅     ✅     ✅    DONE
006 Guidelines Agent         ❌    ❌     ❌     ⚠️     ⚠️     ❌    PARTIAL (chybí DB)
007 Supervisor Orchestration  ❌    ❌     ❌     ✅     ✅     ❌    DONE (bez spec)
008 Citation System          ❌    ❌     ❌     ✅     ✅     ❌    DONE (bez spec)
009 Synthesizer Node         ❌    ❌     ❌     ✅     ✅     ❌    DONE (bez spec)
010 Czech Localization       ❌    ❌     ❌     ⚠️     ❌     ❌    PARTIAL
011 FastAPI Backend          ❌    ❌     ❌     ✅     ⚠️     ✅    DONE (bez spec)
012 Next.js Frontend         ❌    ❌     ❌     ✅     ✅     ✅    DONE (bez spec)
013 Supabase Migration       ✅    ✅     ❌     ⚠️     ⚠️     ✅    PARTIAL (chybí DB)
─────────────────────────────────────────────────────────────────────────
Legenda: ✅ hotovo  ⚠️ částečně  ❌ chybí
```

---

## Vizuální roadmap — aktuální pozice

```
PHASE 0          PHASE 1            PHASE 2              PHASE 3           EXTRA
Foundation       Core Agents        Integration           UX & Deploy
─────────────────────────────────────────────────────────────────────────────────

[001 LangGraph]  [003 SÚKL Drug]    [007 Supervisor]      [010 Lokalizace]
   DONE ✅          DONE ✅            DONE ✅              ČÁSTEČNĚ ⚠️
                                                          14 zkratek, UI CZ
[002 MCP Infra]  [004 VZP Pricing]  [008 Citation]        ale žádný i18n
   DONE ✅        ❌ NEEXISTUJE       DONE ✅
                                                          [011 FastAPI]
                 [005 PubMed]       [009 Synthesizer]        DONE ✅
                    DONE ✅            DONE ✅
                                                          [012 Frontend]     [013 Supabase]
                 [006 Guidelines]                            DONE ✅           ČÁSTEČNĚ ⚠️
                    ČÁSTEČNĚ ⚠️                              Production-       asyncpg hotov
                    node OK, DB ❌                           ready             DB migrace ❌

─────────────────────────────────────────────────────────────────────────────────
                            ▲
                            │
                    AKTUÁLNÍ POZICE: Konec Phase 3 s mezerami
                    Branch: 013-supabase-migration
```

---

## Blokující problémy

### Kritické (brání production nasazení)

1. **Chybějící DB migrační skript** — Kód v `guidelines_storage.py` a `guidelines_agent.py` předpokládá tabulku `guidelines` s pgvector, ale SQL `CREATE TABLE` není v repozitáři. Potřeba:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   CREATE TYPE source_type AS ENUM ('cls_jep', 'esc', 'ers');
   CREATE TABLE guidelines (
     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
     external_id TEXT UNIQUE NOT NULL,
     title TEXT NOT NULL,
     organization TEXT,
     full_content TEXT,
     publication_year INTEGER,
     publication_date DATE,
     source_type source_type,
     url TEXT,
     embedding vector(1536),
     keywords TEXT[],
     icd10_codes TEXT[],
     created_at TIMESTAMPTZ DEFAULT now(),
     updated_at TIMESTAMPTZ DEFAULT now()
   );
   CREATE INDEX idx_guidelines_embedding ON guidelines
     USING hnsw (embedding vector_cosine_ops);
   ```

2. **Confidence scoring TODO** — `routes.py:301` vrací vždy `0.0`. Frontend to zobrazuje, ale hodnota je bezvýznamná.

### Nekritické (nebrání nasazení, ale omezují funkčnost)

3. **Feature 004 VZP Pricing Agent** — Zcela neimplementováno. Žádný kód ani specifikace.
4. **Feature 010 Czech Localization** — Základní lokalizace funguje, ale chybí systematický slovník a i18n.
5. **Guidelines seed data** — I s migrací bude tabulka prázdná. Potřeba pipeline pro ingest ČLS JEP / ESC / ERS PDFs.

---

## Doporučené další kroky

### Priorita 1 — Dokončit rozpracované (1-2 dny)

- [ ] Vytvořit SQL migrační skript (`migrations/001_guidelines_table.sql`)
- [ ] Vytvořit `tasks.md` pro Feature 013
- [ ] Implementovat confidence scoring v synthesizer/routes
- [ ] Opravit Python version mismatch (Dockerfile 3.11 → 3.12)

### Priorita 2 — Zpětně zdokumentovat (2-3 dny)

- [ ] Vytvořit specifikace pro features 007, 008, 009, 011, 012 (implementovány bez spec)
- [ ] Aktualizovat ROADMAP.md se skutečným stavem (není aktuální od 2026-01-13)
- [ ] Doplnit chybějící testy (rate limiting, Redis integrace, sanitization)

### Priorita 3 — Nové features (1-2 týdny)

- [ ] Feature 004: VZP Pricing Agent — vytvořit specifikaci a implementovat
- [ ] Feature 010: Rozšířit lokalizaci — slovník, i18n framework
- [ ] Guidelines ingest pipeline — PDF → chunking → embedding → Supabase

---

**Celkové hodnocení**: Projekt je ve stavu **"funkční MVP s production-ready infrastrukturou"**. Hlavní architektura je solidní, testovací pokrytí je velmi dobré (538 backend + 44 frontend testů), a frontend je deployment-ready. Hlavní mezery jsou databázová infrastruktura pro guidelines a chybějící VZP agent.

**Verze**: 1.0 | **Vygenerováno**: 2026-02-26
