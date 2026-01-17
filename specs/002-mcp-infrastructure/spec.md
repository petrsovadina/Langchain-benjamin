# Feature Specification: MCP Infrastructure

**Feature Branch**: `002-mcp-infrastructure`
**Created**: 2026-01-14
**Status**: Draft
**Input**: Integrace Model Context Protocol (MCP) pro připojení k SÚKL databázi a BioMCP službám

## User Scenarios & Testing *(mandatory)*

### User Story 1 - SÚKL MCP Client Wrapper (Priority: P1)

Jako vývojář AI agenta potřebuji wrapper pro SÚKL-mcp server, abych mohl dotazovat českou databázi léčiv s 68 000+ léky přes standardizované MCP rozhraní.

**Why this priority**: SÚKL je primární zdroj dat pro české léčivé přípravky. Bez tohoto klienta nemůže Drug Agent (Feature 003) fungovat. Kritická závislost pro MVP.

**Independent Test**: Lze otestovat vytvořením SUKLMCPClient instance, připojením k SÚKL-mcp serveru a provedením testovacího dotazu (např. `search_drugs` pro "aspirin"). Úspěch znamená získání strukturované odpovědi s názvem, ATC kódem a registračním číslem.

**Acceptance Scenarios**:

1. **Given** SÚKL-mcp server běží na localhost:3000, **When** vytvořím SUKLMCPClient a zavolám `search_drugs("aspirin")`, **Then** obdržím list léků obsahující "Aspirin" s ATC kódem "B01AC06"
2. **Given** připojený SUKLMCPClient, **When** zavolám `get_drug_details(reg_number="0123456")`, **Then** obdržím kompletní informace včetně dávkování, indikací a kontraindikací
3. **Given** SUKLMCPClient s konfigurací retry, **When** server dočasně selže, **Then** client automaticky opakuje požadavek s exponential backoff
4. **Given** SUKLMCPClient, **When** zavolám `list_available_tools()`, **Then** obdržím všech 8 SÚKL nástrojů (search_drugs, get_drug_details, search_by_atc, get_interactions, search_side_effects, get_pricing_info, search_by_ingredient, validate_prescription)

---

### User Story 2 - BioMCP Client Wrapper (Priority: P1)

Jako vývojář AI agenta potřebuji wrapper pro BioMCP server, abych mohl prohledávat biomedicínskou literaturu (PubMed, Clinical Trials, bioRxiv) s 24 specializovanými nástroji.

**Why this priority**: BioMCP poskytuje přístup k mezinárodnímu výzkumu, který je nezbytný pro evidence-based odpovědi. PubMed Agent (Feature 005) na tom závisí. Kritická pro vědeckou kredibilitu MVP.

**Independent Test**: Lze otestovat vytvořením BioMCPClient instance, připojením k BioMCP serveru (Docker) a provedením `article_searcher` dotazu. Úspěch znamená získání článků s PubMed ID, abstrakty a DOI.

**Acceptance Scenarios**:

1. **Given** BioMCP server běží v Docker kontejneru, **When** vytvořím BioMCPClient a zavolám `article_searcher("diabetes treatment")`, **Then** obdržím relevantní články s PMID, titulky a abstrakty
2. **Given** připojený BioMCPClient, **When** zavolám `get_article_full_text(pmid="12345678")`, **Then** obdržím plný text článku nebo URL k open access verzi
3. **Given** BioMCPClient, **When** zavolám `search_clinical_trials("cancer immunotherapy")`, **Then** obdržím probíhající klinické studie s NCT ID a stavem
4. **Given** BioMCPClient s filtry, **When** zavolám `article_searcher` s parametrem `max_results=10`, **Then** obdržím přesně 10 nejrelevantnějších článků

---

### User Story 3 - Health Check & Connection Testing (Priority: P2)

Jako vývojář potřebuji automatické testování připojení k MCP serverům, abych detekoval problémy ještě před voláním agentů v runtime.

**Why this priority**: Prevence runtime selhání a rychlá diagnostika. Není kritické pro MVP (agenti můžou selhat gracefully), ale výrazně zlepšuje developer experience.

**Independent Test**: Lze otestovat spuštěním `mcp_client.health_check()` a ověřením, že vrací status kód (zdravý/nezdravý/nedostupný) do 5 sekund.

**Acceptance Scenarios**:

1. **Given** běžící SÚKL-mcp server, **When** zavolám `sukl_client.health_check()`, **Then** obdržím `{"status": "healthy", "latency_ms": <100, "tools_count": 8}`
2. **Given** vypnutý BioMCP server, **When** zavolám `biomcp_client.health_check()`, **Then** obdržím `{"status": "unavailable", "error": "Connection refused"}` do 5s timeout
3. **Given** pomalý server (>5s response), **When** zavolám `health_check(timeout=3)`, **Then** obdržím `{"status": "timeout"}` po 3 sekundách
4. **Given** oba klienti, **When** zavolám `check_all_mcp_connections()`, **Then** obdržím report se stavem všech serverů

---

### User Story 4 - Environment Configuration (Priority: P2)

Jako DevOps inženýr potřebuji konfigurovat MCP server endpoints přes `.env` soubor, abych mohl snadno měnit prostředí (dev/staging/prod) bez změny kódu.

**Why this priority**: Best practice pro 12-factor apps. Není kritické pro MVP (můžeme hardcode localhost), ale usnadňuje deployment a testování.

**Independent Test**: Lze otestovat vytvořením `.env` s `SUKL_MCP_URL=http://custom:3001` a ověřením, že SUKLMCPClient se připojí na tento endpoint.

**Acceptance Scenarios**:

1. **Given** `.env` obsahuje `SUKL_MCP_URL=http://localhost:3000`, **When** inicializuji SUKLMCPClient(), **Then** client se připojí na localhost:3000
2. **Given** `.env` obsahuje `BIOMCP_URL=http://biomcp-prod:8080`, **When** inicializuji BioMCPClient(), **Then** client se připojí na produkční server
3. **Given** chybějící proměnná v `.env`, **When** inicializuji client, **Then** použije default hodnotu z `.env.example`
4. **Given** `.env` s `MCP_TIMEOUT=30`, **When** zavolám jakýkoliv MCP nástroj, **Then** timeout je nastaven na 30 sekund

---

### User Story 5 - Retry Logic s Exponential Backoff (Priority: P1)

Jako vývojář potřebuji automatické retry mechanismy pro transientní selhání MCP serverů, abych zvýšil odolnost systému proti dočasným výpadkům sítě.

**Why this priority**: MCP servery mohou být přetížené nebo mít síťové problémy. Retry logic výrazně zvyšuje reliability. Kritické pro produkční použití MVP.

**Independent Test**: Lze otestovat simulací dočasného selhání (mock server vrací 503 první 2x, pak 200) a ověřením, že client automaticky opakuje s exponential backoff.

**Acceptance Scenarios**:

1. **Given** SÚKL server vrací 503 (service unavailable), **When** zavolám `search_drugs()` s `max_retries=3`, **Then** client opakuje 3x s delays [1s, 2s, 4s] a vrací error po poslední neúspěšné retry
2. **Given** síťový timeout při prvním pokusu, **When** druhý pokus uspěje, **Then** client vrací úspěšnou odpověď bez propagace erroru
3. **Given** permanentní chyba (404 Not Found), **When** zavolám MCP nástroj, **Then** client NERETRYUJE (není transientní) a okamžitě vrací error
4. **Given** konfigurovaný `RetryConfig(max_retries=5, base_delay=2)`, **When** server selže 4x, **Then** client se vzdá po 5. pokusu s celkovou dobou ~30 sekund (2+4+8+16)

---

### Edge Cases

- **Co se stane, když MCP server vrací nevalidní JSON?**
  - Client musí zachytit parse error a vrátit strukturovanou MCP error odpověď s původním raw response v `debug_info`

- **Jak systém zvládne současné dotazy na stejný MCP server?**
  - Klienti musí být thread-safe a podporovat concurrent requests (async I/O), s connection pooling

- **Co když SÚKL databáze vrací 0 výsledků pro validní dotaz?**
  - Client vrací prázdný list (ne error), aby agent mohl odpovědět "Nenašel jsem žádné léky..."

- **Jak se chovají retry při rate limitingu (429 Too Many Requests)?**
  - Client musí respektovat `Retry-After` header a přidat jitter k exponential backoff pro prevenci thundering herd

- **Co když BioMCP Docker kontejner není spuštěný při inicializaci klientů?**
  - Inicializace musí být lazy (připojení až při prvním volání), s jasným error message: "BioMCP server not available at {url}"

- **Jak systém validuje MCP protocol version compatibility?**
  - Každý client musí při první komunikaci ověřit server protocol version (očekáváme MCP v1.0+) a logovat warning při version mismatch

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Systém MUSÍ poskytovat `SUKLMCPClient` třídu s async metodami pro všech 8 SÚKL nástrojů
- **FR-002**: Systém MUSÍ poskytovat `BioMCPClient` třídu s async metodami minimálně pro `article_searcher`, `get_article_full_text`, `search_clinical_trials`
- **FR-003**: Všechny MCP klienti MUSÍ implementovat standardizované `IMCPClient` rozhraní (protocol/ABC) pro polymorfismus
- **FR-004**: Systém MUSÍ implementovat retry logiku s konfigurovatelným exponential backoff (default: 3 retries, base delay 1s)
- **FR-005**: Klienti MUSÍ validovat MCP odpovědi proti očekávanému JSON schema a vracet typed dataclasses
- **FR-006**: Systém MUSÍ poskytovat `health_check()` metodu pro každého MCP klienta s timeout 5 sekund
- **FR-007**: Konfigurace MCP endpoints MUSÍ být loadována z `.env` souboru s fallback na default hodnoty
- **FR-008**: Všechny MCP errory MUSÍ být transformovány na vlastní exception typy (`MCPConnectionError`, `MCPTimeoutError`, `MCPValidationError`)
- **FR-009**: Klienti MUSÍ logovat všechny MCP calls s request/response payloads (v DEBUG level) pro observability
- **FR-010**: Systém MUSÍ podporovat graceful degradation - pokud MCP server není dostupný, agent dostane jasný error message (ne crash)

### Key Entities

- **SUKLMCPClient**: Wrapper pro SÚKL-mcp server poskytující 8 nástrojů pro dotazování české databáze léčiv. Atributy: `base_url`, `timeout`, `retry_config`, `session` (aiohttp). Vztahy: Používán Drug Agentem (Feature 003) a Pricing Agentem (Feature 004).

- **BioMCPClient**: Wrapper pro BioMCP server poskytující 24 nástrojů pro biomedicínský výzkum. Atributy: `base_url`, `timeout`, `retry_config`, `session`, `max_results` (default 10). Vztahy: Používán PubMed Agentem (Feature 005).

- **RetryConfig**: Konfigurace pro exponential backoff retry logiku. Atributy: `max_retries` (default 3), `base_delay` (default 1.0s), `max_delay` (default 30s), `jitter` (bool, default True). Vztahy: Embedded v každém MCP klientovi.

- **MCPResponse**: Standardizovaná odpověď z MCP nástroje. Atributy: `success` (bool), `data` (Any), `error` (Optional[str]), `metadata` (Dict - timing, server info). Vztahy: Vracena všemi MCP client metodami.

- **MCPHealthStatus**: Status report z health check. Atributy: `status` (Literal["healthy", "unhealthy", "unavailable", "timeout"]), `latency_ms` (Optional[int]), `tools_count` (Optional[int]), `error` (Optional[str]). Vztahy: Používán monitoring systémem.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: SUKLMCPClient musí úspěšně provést všech 8 typů dotazů (search_drugs, get_drug_details, atd.) s reálným SÚKL-mcp serverem v <500ms (95th percentile)
- **SC-002**: BioMCPClient musí získat PubMed články pro 10 testovacích dotazů s precision ≥80% (relevantní články v top 10 výsledcích)
- **SC-003**: Retry logic musí úspěšně překonat 95% transientních chyb (simulovaných v unit testech) do 10 sekund
- **SC-004**: Health check musí detekovat nedostupný server do 5 sekund s 100% spolehlivostí
- **SC-005**: Všechny MCP klienti musí mít 100% type coverage (mypy --strict bez chyb)
- **SC-006**: Integration testy musí pokrýt všechny FR-001 až FR-010 požadavky s ≥90% code coverage
- **SC-007**: Systém musí správně loadovat 100% konfiguračních proměnných z `.env` (testováno pomocí různých .env souborů)
- **SC-008**: Dokumentace musí obsahovat příklady pro všech 8+3 MCP nástrojů (SÚKL + top 3 BioMCP nástroje)
- **SC-009**: Graceful degradation musí fungovat - pokud MCP server není dostupný, aplikace vrací user-friendly error (ne stack trace)
- **SC-010**: Performance: Concurrent dotazy (10 paralelních requests) na MCP servery musí mít throughput ≥50 requests/second

## Implementation Notes

### Technology Stack
- **HTTP Client**: `aiohttp` pro async HTTP komunikaci
- **Retry Logic**: `tenacity` library s exponential backoff
- **Validation**: `pydantic` pro MCP response validation
- **Environment**: `python-dotenv` pro .env management
- **Type Safety**: `typing`, `typing_extensions` pro Protocol/TypedDict

### MCP Server Configuration

SÚKL-mcp server (localhost):
```bash
# Clone a spuštění
git clone https://github.com/petrsovadina/SUKL-mcp
cd SUKL-mcp
npm install
npm start  # Běží na http://localhost:3000
```

BioMCP server (Docker):
```bash
# Docker compose setup
docker-compose up -d biomcp
# Běží na http://localhost:8080
```

### Reference Documentation
- SÚKL-mcp API: https://github.com/petrsovadina/SUKL-mcp/blob/main/README.md
- BioMCP API: Viz `docs/MCP_INTEGRATION.md` (bude vytvořen v plan.md)
- Model Context Protocol Spec: https://modelcontextprotocol.io/docs

### Dependencies with Other Features
- **Blocked by**: Feature 001 (LangGraph Foundation) ✅ DONE
- **Blocks**: Feature 003 (SÚKL Drug Agent), Feature 004 (VZP Pricing Agent), Feature 005 (BioMCP PubMed Agent)
- **Related**: Feature 013 (Workflows) - bude používat mode: "quick"/"deep" z Context
