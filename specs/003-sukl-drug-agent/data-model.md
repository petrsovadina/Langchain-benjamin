# Data Model: SÚKL Drug Agent

**Feature**: 003-sukl-drug-agent
**Date**: 2026-01-17

## Entity Overview

```
┌─────────────────────┐
│     DrugQuery       │ ←── Vstup do node
├─────────────────────┤
│ query_text: str     │
│ query_type: Enum    │
│ filters: dict?      │
│ limit: int          │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐     ┌─────────────────────┐
│   DrugResult        │────▶│   DrugDetails       │
├─────────────────────┤     ├─────────────────────┤
│ name: str           │     │ registration_number │
│ atc_code: str       │     │ name: str           │
│ registration_number │     │ active_ingredient   │
│ manufacturer: str?  │     │ composition: list   │
│ match_score: float? │     │ indications: list   │
└─────────────────────┘     │ contraindications   │
                            │ dosage: str         │
                            │ side_effects: list  │
                            └─────────────────────┘

┌─────────────────────┐     ┌─────────────────────┐
│ ReimbursementInfo   │     │  AvailabilityInfo   │
├─────────────────────┤     ├─────────────────────┤
│ registration_number │     │ registration_number │
│ category: A/B/D     │     │ is_available: bool  │
│ copay_amount: float │     │ shortage_info: str? │
│ prescription_req    │     │ alternatives: list  │
│ conditions: list    │     └─────────────────────┘
└─────────────────────┘
```

## Entity Definitions

### 1. QueryType (Enum)

Typ dotazu pro klasifikaci.

| Value | Description | SÚKL Tool |
|-------|-------------|-----------|
| `SEARCH` | Vyhledávání podle názvu | `search_medicine` |
| `DETAILS` | Detailní informace | `get_medicine_details` |
| `REIMBURSEMENT` | Úhrada a ceny | `get_reimbursement` |
| `AVAILABILITY` | Dostupnost a alternativy | `check_availability` |
| `ATC` | ATC klasifikace | `get_atc_info` |
| `INGREDIENT` | Vyhledávání podle účinné látky | `search_by_ingredient` |

**Validation**: Hodnota musí být jedna z definovaných hodnot.

---

### 2. DrugQuery

Vstupní dotaz na lék.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query_text` | str | Yes | Text dotazu (název léku, ATC kód, účinná látka) |
| `query_type` | QueryType | Yes | Typ dotazu pro routing |
| `filters` | dict | No | Dodatečné filtry (např. limit, manufacturer) |
| `limit` | int | No (default: 10) | Maximální počet výsledků |

**Validation**:
- `query_text` nesmí být prázdný
- `limit` musí být ≥1 a ≤100

**State Transitions**: Vytvořen z user message nebo explicitně nastaven.

---

### 3. DrugResult

Výsledek vyhledávání léku (zkrácená forma).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | str | Yes | Název léku |
| `atc_code` | str | Yes | ATC klasifikační kód |
| `registration_number` | str | Yes | SÚKL registrační číslo |
| `manufacturer` | str | No | Výrobce léku |
| `match_score` | float | No | Skóre shody (fuzzy matching, 0.0-1.0) |

**Validation**:
- `atc_code` musí odpovídat ATC formátu (např. "M01AE01")
- `match_score` musí být v rozsahu 0.0-1.0

**Relationships**: Může být rozšířen na DrugDetails pomocí `registration_number`.

---

### 4. DrugDetails

Kompletní informace o léku.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `registration_number` | str | Yes | SÚKL registrační číslo |
| `name` | str | Yes | Název léku |
| `active_ingredient` | str | Yes | Účinná látka |
| `composition` | list[str] | Yes | Seznam složek |
| `indications` | list[str] | Yes | Indikace (pro co je lék určen) |
| `contraindications` | list[str] | No | Kontraindikace |
| `dosage` | str | Yes | Doporučené dávkování |
| `side_effects` | list[str] | No | Možné nežádoucí účinky |
| `pharmaceutical_form` | str | No | Léková forma (tablety, sirup, ...) |
| `atc_code` | str | Yes | ATC klasifikační kód |

**Validation**:
- `composition` musí mít alespoň 1 položku
- `indications` musí mít alespoň 1 položku

---

### 5. ReimbursementInfo

Informace o úhradě ze zdravotního pojištění.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `registration_number` | str | Yes | SÚKL registrační číslo |
| `category` | Literal["A", "B", "D", "N"] | Yes | Kategorie úhrady |
| `copay_amount` | float | No | Doplatek pacienta v Kč |
| `max_price` | float | No | Maximální cena |
| `prescription_required` | bool | Yes | Vyžaduje předpis |
| `conditions` | list[str] | No | Podmínky úhrady |

**Validation**:
- `category` musí být jedna z: A (plná úhrada), B (částečná), D (bez úhrady), N (nehodnoceno)

**Categories**:
- **A**: Plně hrazeno ze zdravotního pojištění
- **B**: Částečně hrazeno (s doplatkem)
- **D**: Nehrazeno (pacient platí plně)
- **N**: Dosud nehodnoceno

---

### 6. AvailabilityInfo

Informace o dostupnosti léku.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `registration_number` | str | Yes | SÚKL registrační číslo |
| `is_available` | bool | Yes | Je lék aktuálně dostupný |
| `shortage_info` | str | No | Informace o výpadku |
| `expected_availability` | str | No | Očekávaná dostupnost |
| `alternatives` | list[DrugResult] | No | Alternativní léky |

**Validation**:
- Pokud `is_available` je False, `shortage_info` nebo `alternatives` by měly být vyplněny

---

## State Extension

### State (rozšířená verze)

```python
@dataclass
class State:
    # Existing fields (Feature 001)
    messages: Annotated[list[AnyMessage], add_messages]
    next: str = "__end__"
    retrieved_docs: list[Document] = field(default_factory=list)

    # NEW: Feature 003
    drug_query: Optional[DrugQuery] = None
```

---

## Document Transformation

### DrugResult → Document

```python
Document(
    page_content=f"{result.name} ({result.atc_code}) - Reg. č.: {result.registration_number}",
    metadata={
        "source": "sukl",
        "source_type": "drug_search",
        "registration_number": result.registration_number,
        "atc_code": result.atc_code,
        "match_score": result.match_score,
        "retrieved_at": datetime.now().isoformat()
    }
)
```

### DrugDetails → Document

```python
Document(
    page_content=f"""
## {details.name}
**Účinná látka**: {details.active_ingredient}
**ATC kód**: {details.atc_code}

### Indikace
{format_list(details.indications)}

### Dávkování
{details.dosage}

### Kontraindikace
{format_list(details.contraindications)}
""",
    metadata={
        "source": "sukl",
        "source_type": "drug_details",
        "registration_number": details.registration_number,
        "atc_code": details.atc_code,
        "retrieved_at": datetime.now().isoformat()
    }
)
```
