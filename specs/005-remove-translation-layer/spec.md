# Feature 005 Refactoring: Odstranění Translation Sandwich Pattern

**Status**: Draft
**Created**: 2026-01-25
**Author**: Claude Code
**Type**: Refactoring

## Overview

Odstranit zbytečně složitý translation layer (Sandwich Pattern: CZ→EN→PubMed→EN→CZ) z PubMed agenta. Claude Sonnet 4.5 nativně podporuje češtinu, takže agent může pracovat přímo v českém jazyce bez nutnosti překladu na angličtinu a zpět.

## Problem Statement

**Současný stav:**
- PubMed agent používá 3-krokový Sandwich Pattern workflow:
  1. `translate_cz_to_en` node - překlad českého dotazu do angličtiny
  2. `pubmed_agent` node - vyhledávání v PubMed (anglicky)
  3. `translate_en_to_cz` node - překlad výsledků zpět do češtiny
- Vyžaduje Anthropic API key pro translation nodes
- 3 LLM volání místo 1
- Delší latence (každý translation node přidává ~2-3s)
- Vyšší náklady (3× více API calls)
- Složitější architektura grafu

**Proč je to problém:**
- **Overengineering**: Claude Sonnet 4.5 je multilingvní model - zvládá češtinu nativně
- **Zbytečná komplexita**: Translation nodes nepřidávají hodnotu, jen komplikují flow
- **Horší výkon**: 2× delší odpověď kvůli translation overhead
- **Vyšší náklady**: 3× více API volání = 3× vyšší cena

**Dopad na uživatele:**
- Pomalejší odpovědi na research dotazy
- Potenciální chyby v překladu (informace se může ztratit/změnit během CZ→EN→CZ)
- Zbytečně složitý debugging (3 nody místo 1)

## User Scenarios & Testing

### Scenario 1: Research Query - Czech to Czech (Direct)

**Actor**: Český lékař
**Goal**: Získat informace o diabetických studiích
**Preconditions**: Agent dostupný, BioMCP server běží

**Flow:**
1. Lékař zadá dotaz: "jaké jsou nejnovější studie o diabetu typu 2"
2. Systém identifikuje research query (klíčové slovo "studie")
3. `pubmed_agent` node:
   - Přijme český dotaz přímo (bez překladu)
   - Zavolá BioMCP article_searcher s českým query
   - Vrátí výsledky v češtině (Claude zpracuje anglické abstracts a převede do CZ)
4. Lékař vidí výsledky v češtině s citacemi

**Expected Outcome:**
- Odpověď do 5 sekund (místo 8-10s s translation)
- Výsledky v přirozené češtině
- Inline citace [1][2][3] zachovány
- Žádná ztráta informací kvůli překladu

### Scenario 2: PMID Lookup - Direct Processing

**Actor**: Český lékař
**Goal**: Získat konkrétní článek podle PMID
**Preconditions**: Lékař má PMID (např. "12345678")

**Flow:**
1. Lékař zadá: "článek pmid 12345678"
2. Systém identifikuje PMID lookup query
3. `pubmed_agent` node:
   - Přijme dotaz přímo v češtině
   - Zavolá BioMCP article_getter s PMID
   - Vrátí article details v češtině
4. Lékař vidí titulek, autory, abstract v češtině

**Expected Outcome:**
- Rychlá odpověď (<3s místo 5-7s)
- Přesné informace bez translation artifacts
- Zachované technické termíny

### Scenario 3: Empty Results Handling

**Actor**: Český lékař
**Goal**: Hledat neexistující téma
**Preconditions**: BioMCP vrátí 0 výsledků

**Flow:**
1. Lékař zadá: "studie o unicorn medicine"
2. Systém identifikuje research query
3. `pubmed_agent` node:
   - Vyhledá v BioMCP (0 results)
   - Vrátí czech message: "Nebyly nalezeny žádné články..."
4. Lékař vidí jasnou zprávu v češtině

**Expected Outcome:**
- Uživatelsky přívětivá zpráva v češtině
- Návrhy na alternativní hledání (pokud relevantní)

## Functional Requirements

### FR-001: Direct Czech Query Processing
**Priority**: P0 (Critical)
**Description**: PubMed agent musí přijímat a zpracovávat české dotazy přímo bez translation layer.

**Acceptance Criteria:**
- [ ] `pubmed_agent_node` přijímá české dotazy v `state.messages`
- [ ] Claude Sonnet 4.5 zpracovává české dotazy bez překladu
- [ ] Výsledky jsou generovány v češtině (Claude převádí anglické abstracts)
- [ ] Žádné volání `translate_cz_to_en` nebo `translate_en_to_cz` nodes

### FR-002: Remove Translation Nodes from Graph
**Priority**: P0 (Critical)
**Description**: Odstranit `translate_cz_to_en_node` a `translate_en_to_cz_node` z grafu včetně jejich edges.

**Acceptance Criteria:**
- [ ] Nodes `translate_cz_to_en` a `translate_en_to_cz` odstraněny z grafu
- [ ] Routing edge aktualizován: `route_query` → `pubmed_agent` (bez translation)
- [ ] Edge `pubmed_agent` → `__end__` (přímo, bez translation)
- [ ] Graf kompiluje bez chyb
- [ ] LangGraph Studio vizualizace ukazuje přímé spojení

### FR-003: Remove Translation Node Files
**Priority**: P0 (Critical)
**Description**: Smazat soubory `translation.py` a `translation_prompts.py`, protože nejsou potřeba.

**Acceptance Criteria:**
- [ ] `src/agent/nodes/translation.py` smazán
- [ ] `src/agent/utils/translation_prompts.py` smazán
- [ ] Importy v `graph.py` aktualizovány (bez translation imports)
- [ ] Všechny testy projdou bez translation závislostí

### FR-004: Update PubMed Agent for Direct Czech
**Priority**: P0 (Critical)
**Description**: Upravit `pubmed_agent_node` tak, aby pracoval přímo s českými dotazy a vracel české odpovědi.

**Acceptance Criteria:**
- [ ] Node nepřepokládá anglický input (odstraněno očekávání `research_query.query_text` v EN)
- [ ] Claude prompt obsahuje instrukce pro práci v češtině
- [ ] Odpovědi generovány v češtině s inline citacemi [1][2][3]
- [ ] Abstrakty z PubMed (anglicky) jsou převedeny do češtiny Claudem
- [ ] Technické termíny zachovány správně (např. "diabetes mellitus type 2")

### FR-005: Remove ResearchQuery Model Dependency
**Priority**: P1 (High)
**Description**: Odstranit `ResearchQuery` model, protože není potřeba bez translation layer.

**Acceptance Criteria:**
- [ ] `ResearchQuery` dataclass odstraněn z `research_models.py`
- [ ] `state.research_query` field odstraněn ze `State` dataclass
- [ ] PubMed agent parsuje dotaz přímo z `state.messages[-1].content`
- [ ] Routing funguje bez `research_query` pole

### FR-006: Update Routing Logic
**Priority**: P1 (High)
**Description**: Aktualizovat `route_query` funkci tak, aby směrovala přímo na `pubmed_agent` bez translation.

**Acceptance Criteria:**
- [ ] Routing vrací `"pubmed_agent"` pro research queries (místo `"translate_cz_to_en"`)
- [ ] Research keywords fungují stejně (studie, výzkum, pubmed, atd.)
- [ ] Routing testy aktualizovány
- [ ] Žádná reference na translation nodes

### FR-007: Remove Anthropic API Dependency
**Priority**: P2 (Medium)
**Description**: Odstranit requirement na ANTHROPIC_API_KEY z `.env`, protože translation nodes jsou odstraněny.

**Acceptance Criteria:**
- [ ] ANTHROPIC_API_KEY zakomentován nebo odstraněn z `.env`
- [ ] README aktualizováno (ANTHROPIC_API_KEY není required)
- [ ] PubMed agent funguje pouze s BioMCP (bez Anthropic API)
- [ ] Translation-related environment variables odstraněny

### FR-008: Update Tests
**Priority**: P1 (High)
**Description**: Aktualizovat unit a integration testy pro novou architekturu bez translation.

**Acceptance Criteria:**
- [ ] Translation node testy smazány (`tests/unit_tests/nodes/test_translation.py`)
- [ ] PubMed agent testy aktualizovány pro české dotazy
- [ ] Integration testy pro research flow aktualizovány (bez translation steps)
- [ ] Všechny testy projdou (≥169/175 passing)
- [ ] Žádné broken imports

### FR-009: Update Documentation
**Priority**: P2 (Medium)
**Description**: Aktualizovat CLAUDE.md a README.md s novou zjednodušenou architekturou.

**Acceptance Criteria:**
- [ ] CLAUDE.md: Sandwich Pattern dokumentace odstraněna
- [ ] CLAUDE.md: PubMed agent popis aktualizován (direct Czech processing)
- [ ] README.md: Environment variables sekce aktualizována (bez ANTHROPIC_API_KEY)
- [ ] Architecture diagram aktualizován (pokud existuje)

## Success Criteria

1. **Performance Improvement**: Research queries odpovídají do 5 sekund (místo 8-10s)
   - Měřeno: čas od user message po assistant response
   - Target: ≤5s pro 95% queries

2. **Cost Reduction**: 66% reduction v API costs pro research queries
   - Současný stav: 3 LLM calls (2× translation + 1× research)
   - Cílový stav: 1 LLM call (pouze research)
   - Úspora: 2 LLM calls = ~66% cost reduction

3. **Simplified Architecture**: Graf obsahuje pouze 1 node pro research (místo 3)
   - Vizuální validace: LangGraph Studio zobrazí `route_query` → `pubmed_agent` → `__end__`
   - Code validace: 2 nodes odstraněny z graph definition

4. **Zero Translation Errors**: Žádné informační ztráty kvůli CZ→EN→CZ conversion
   - Validace: Technické termíny zůstávají přesné
   - User feedback: Odpovědi jsou přirozenější a přesnější

5. **Simplified Configuration**: ANTHROPIC_API_KEY není required pro PubMed agent
   - Setup guide: Pouze BioMCP URL required
   - Fewer environment variables = easier onboarding

## Dependencies & Assumptions

### Dependencies
- **BioMCP Server**: Musí běžet na `http://localhost:8080` (nebo configured URL)
- **Claude Sonnet 4.5**: Nativní czech support confirmed v model capabilities
- **Existing Code**: Feature 005 implementace s translation layer již existuje

### Assumptions
1. **Claude Czech Quality**: Claude Sonnet 4.5 generuje kvalitní české odpovědi bez překladu
   - Předpoklad: Model quality je dostatečná pro lékařské dotazy
   - Risk mitigation: User testing v Phase 1

2. **BioMCP API Format**: BioMCP přijímá české query strings bez problémů
   - Předpoklad: API ignoruje jazyk query (hledá keywords)
   - Validace: Test s českými queries v BioMCP

3. **Citation Preservation**: Inline citace [1][2][3] fungují bez translation layer
   - Předpoklad: Citation format není závislý na translation
   - Validace: Integration tests

## Out of Scope

- **Změna BioMCP integrace**: BioMCP client zůstává stejný (pouze query format se nezmění)
- **Změna drug agenta**: Drug agent není dotčen tímto refactoringem
- **Přidání nových features**: Pouze odstranění translation layer, žádné nové funkce
- **Změna LLM modelu**: Zůstává Claude Sonnet 4.5 (není nutné měnit)

## Edge Cases & Error Handling

### Edge Case 1: Mixed Language Queries
**Scenario**: Uživatel zadá dotaz částečně česky, částečně anglicky
**Example**: "studie o diabetes mellitus treatment"
**Expected Behavior**: Claude zpracuje mixed-language query přirozeně (podporuje code-switching)

### Edge Case 2: Technical English Terms
**Scenario**: Uživatel chce zachovat anglické technické termíny
**Example**: "evidence-based medicine u diabetes"
**Expected Behavior**: Claude zachová anglické termíny v české odpovědi

### Edge Case 3: Empty BioMCP Results
**Scenario**: BioMCP vrátí 0 articles
**Current Behavior**: Translation node překládá "No articles found" → "Žádné články nenalezeny"
**New Behavior**: PubMed agent generuje českou zprávu přímo

### Edge Case 4: BioMCP API Error
**Scenario**: BioMCP server nedostupný
**Current Behavior**: Error v pubmed_agent, translation se neprovede
**New Behavior**: PubMed agent vrátí českou error zprávu přímo (bez translation)

## Risks & Mitigation

### Risk 1: Czech Quality Degradation
**Probability**: Medium
**Impact**: High
**Description**: Claude může generovat horší češtinu než specialized translation node
**Mitigation**:
- User testing v Phase 1 (compare old vs. new responses)
- Fallback: Pokud kvalita nevyhovuje, rollback translation layer
- Monitoring: Track user satisfaction metrics

### Risk 2: Missing Translation Capabilities
**Probability**: Low
**Impact**: Medium
**Description**: Některé use cases mohou potřebovat explicitní translation
**Mitigation**:
- Keep translation code v git history (easy rollback)
- Document decision v CLAUDE.md
- Monitor user feedback pro translation requests

### Risk 3: Test Coverage Gaps
**Probability**: Medium
**Impact**: Medium
**Description**: Odstranění translation testů může snížit coverage
**Mitigation**:
- Ensure PubMed agent tests pokrývají czech scenarios
- Maintain ≥80% coverage target
- Add integration tests pro direct czech flow

## Notes

### Design Decisions

**Proč odstranit translation místo upgrade?**
- Claude Sonnet 4.5 je state-of-the-art multilingvní model
- Translation layer nepřidává hodnotu pro czech↔english
-Jednodušší architektura = méně bugs, lepší maintainability

**Alternative Considered: Keep translation as optional**
- Rejected: Adds complexity without clear benefit
- Translation může být přidána později jako feature flag pokud potřeba

### Implementation Notes

**Doporučené pořadí implementace:**
1. Update `pubmed_agent_node` pro czech processing (FR-004)
2. Update routing logic (FR-006)
3. Remove translation nodes from graph (FR-002)
4. Delete translation files (FR-003)
5. Update tests (FR-008)
6. Update documentation (FR-009)

**Testing Strategy:**
- Manual testing: Compare old vs. new responses pro same queries
- Performance testing: Measure latency improvement
- User acceptance: Czech doctors validate response quality

---

**Version**: 1.0.0
**Last Updated**: 2026-01-25
**Next Phase**: `/speckit.plan` - vytvořit implementační plán
