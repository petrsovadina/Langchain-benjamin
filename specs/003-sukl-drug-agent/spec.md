# Feature Specification: SÚKL Drug Agent

**Feature Branch**: `003-sukl-drug-agent`
**Created**: 2026-01-17
**Status**: Draft
**Input**: User description: "SÚKL Drug Agent - LangGraph node pro vyhledávání a získávání informací o lécích z české farmaceutické databáze SÚKL pomocí SÚKL-mcp serveru"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Vyhledávání léku podle názvu (Priority: P1)

Jako český lékař chci vyhledat lék podle jeho názvu (včetně částečné shody a překlepů), abych rychle získal základní informace o léku a mohl pokračovat v rozhodování o léčbě pacienta.

**Why this priority**: Základní funkce - bez vyhledávání léků nemá agent smysl. Toto je vstupní bod pro všechny ostatní operace s léky.

**Independent Test**: Lze plně otestovat zadáním názvu léku (např. "Ibalgin", "Paralen") a ověřením, že systém vrátí relevantní výsledky s názvem, ATC kódem a registračním číslem.

**Acceptance Scenarios**:

1. **Given** uživatel zadá přesný název léku "Ibalgin 400", **When** systém zpracuje dotaz, **Then** systém vrátí informace o léku Ibalgin 400 včetně ATC kódu a registračního čísla
2. **Given** uživatel zadá částečný název "Ibal", **When** systém zpracuje dotaz, **Then** systém vrátí seznam léků obsahujících "Ibal" v názvu
3. **Given** uživatel zadá název s překlepem "Ibalgyn", **When** systém zpracuje dotaz s fuzzy matching, **Then** systém vrátí výsledky pro "Ibalgin" s tolerancí pro překlepy

---

### User Story 2 - Detailní informace o léku (Priority: P1)

Jako český lékař chci získat kompletní detailní informace o konkrétním léku (složení, indikace, kontraindikace, dávkování), abych mohl učinit informované rozhodnutí o předepsání.

**Why this priority**: Kritická funkce pro klinické rozhodování - lékař potřebuje kompletní informace před předepsáním léku.

**Independent Test**: Lze otestovat zadáním registračního čísla léku a ověřením, že systém vrátí detailní informace včetně účinné látky a dávkování.

**Acceptance Scenarios**:

1. **Given** uživatel zná registrační číslo léku, **When** požádá o detaily, **Then** systém vrátí kompletní informace o léku včetně složení a indikací
2. **Given** uživatel vybral lék z výsledků vyhledávání, **When** požádá o podrobnosti, **Then** systém vrátí detailní informace o vybraném léku

---

### User Story 3 - Informace o úhradě a cenách (Priority: P2)

Jako český lékař chci znát informace o úhradě léku ze zdravotního pojištění a jeho ceně, abych mohl pacientovi poskytnout informace o finanční stránce léčby.

**Why this priority**: Důležité pro pacienty z ekonomického hlediska, ale není kritické pro samotnou léčbu.

**Independent Test**: Lze otestovat zadáním léku a ověřením, že systém vrátí kategorii úhrady (A/B/D) a cenové informace.

**Acceptance Scenarios**:

1. **Given** uživatel se dotazuje na konkrétní lék, **When** požádá o informace o úhradě, **Then** systém vrátí kategorii úhrady a podmínky předepsání
2. **Given** uživatel se dotazuje na cenově citlivého pacienta, **When** požádá o cenové alternativy, **Then** systém navrhne generické alternativy s lepší úhradou

---

### User Story 4 - Kontrola dostupnosti a alternativy (Priority: P2)

Jako český lékař chci zkontrolovat dostupnost léku a případně získat návrhy alternativ, abych mohl pacientovi předepsat dostupný lék.

**Why this priority**: Prakticky důležité pro reálnou preskripci, ale lékař může tuto informaci získat i jinak.

**Independent Test**: Lze otestovat dotazem na lék a ověřením informace o dostupnosti nebo seznamu alternativ.

**Acceptance Scenarios**:

1. **Given** lék je dostupný, **When** uživatel se dotáže na dostupnost, **Then** systém potvrdí dostupnost
2. **Given** lék není dostupný nebo je v deficitu, **When** uživatel se dotáže na dostupnost, **Then** systém informuje o nedostupnosti a nabídne alternativní léky se stejnou účinnou látkou

---

### User Story 5 - Vyhledávání podle ATC kódu nebo účinné látky (Priority: P3)

Jako český lékař chci vyhledat léky podle ATC klasifikace nebo účinné látky, abych našel všechny dostupné přípravky v dané terapeutické skupině.

**Why this priority**: Pokročilá funkce pro specialisty, většina lékařů vyhledává podle názvu.

**Independent Test**: Lze otestovat zadáním ATC kódu (např. "M01AE01") nebo názvu účinné látky ("ibuprofen") a ověřením seznamu odpovídajících léků.

**Acceptance Scenarios**:

1. **Given** uživatel zadá ATC kód "M01AE01", **When** systém zpracuje dotaz, **Then** vrátí všechny léky s tímto ATC kódem
2. **Given** uživatel zadá účinnou látku "ibuprofen", **When** systém zpracuje dotaz, **Then** vrátí všechny léky obsahující ibuprofen

---

### Edge Cases

- Co se stane, když SÚKL-mcp server není dostupný? → Systém vrátí chybovou odpověď s jasnou informací o nedostupnosti služby
- Jak systém zpracuje neexistující lék? → Systém vrátí prázdný výsledek s informací, že lék nebyl nalezen
- Co když uživatel zadá příliš obecný dotaz (např. "lék")? → Systém vrátí omezený počet výsledků s upozorněním na příliš obecný dotaz
- Jak systém řeší timeout při dlouhém vyhledávání? → Systém má nastaven timeout a vrátí chybu s doporučením zúžit dotaz

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Systém MUSÍ umožnit vyhledávání léků podle názvu s podporou fuzzy matching (tolerance pro překlepy)
- **FR-002**: Systém MUSÍ vrátit detailní informace o léku včetně složení, indikací a kontraindikací
- **FR-003**: Systém MUSÍ poskytovat informace o kategorii úhrady a cenách léků
- **FR-004**: Systém MUSÍ umožnit vyhledávání podle ATC kódu
- **FR-005**: Systém MUSÍ umožnit vyhledávání podle účinné látky
- **FR-006**: Systém MUSÍ kontrolovat dostupnost léku a nabízet alternativy
- **FR-007**: Systém MUSÍ být implementován jako LangGraph node s async funkcí
- **FR-008**: Systém MUSÍ využívat existující MCP infrastrukturu z Feature 002 (SUKLMCPClient)
- **FR-009**: Systém MUSÍ vracet strukturované odpovědi s citacemi zdrojů (SÚKL)
- **FR-010**: Systém MUSÍ logovat všechny dotazy a odpovědi pro observability (LangSmith)

### Key Entities

- **DrugQuery**: Reprezentuje dotaz uživatele na lék (název, ATC kód, účinná látka, typ dotazu)
- **DrugResult**: Výsledek vyhledávání léku s metadaty (název, registrační číslo, ATC, výrobce)
- **DrugDetails**: Kompletní informace o léku (složení, indikace, kontraindikace, dávkování)
- **ReimbursementInfo**: Informace o úhradě (kategorie A/B/D, podmínky, cena)
- **AvailabilityInfo**: Informace o dostupnosti léku a alternativách

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Uživatel může vyhledat lék a získat základní informace do 3 sekund
- **SC-002**: Systém správně nalezne lék i při překlep v názvu (fuzzy matching s prahem 80%)
- **SC-003**: Detailní informace o léku jsou kompletní a obsahují minimálně: název, účinnou látku, ATC kód, indikace
- **SC-004**: Systém dokáže zpracovat minimálně 100 dotazů za minutu bez degradace
- **SC-005**: V případě nedostupnosti SÚKL serveru systém vrátí srozumitelnou chybu do 5 sekund
- **SC-006**: Pokrytí unit testy ≥90% pro všechny funkce node

## Assumptions

- MCP infrastruktura z Feature 002 je plně funkční a testovaná
- SÚKL-mcp server je dostupný na konfigurované URL (z MCPConfig)
- Databáze SÚKL obsahuje aktuální data o 68,000+ lécích
- Retry strategie z Feature 002 bude použita pro robustnost

## Dependencies

- **Feature 002**: MCP Infrastructure (SUKLMCPClient, MCPConfig, RetryConfig)
- **External**: SÚKL-mcp server (https://github.com/petrsovadina/SUKL-mcp)
