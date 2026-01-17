# Research: SÚKL Drug Agent

**Feature**: 003-sukl-drug-agent
**Date**: 2026-01-17

## Přehled výzkumu

Tento dokument obsahuje výsledky výzkumu potřebného pro implementaci SÚKL Drug Agent.

---

## 1. SÚKL-mcp Server Integration

### Decision
Využít existující `SUKLMCPClient` z Feature 002 bez modifikací.

### Rationale
- Client již implementuje všech 8 SÚKL-mcp tools
- Retry strategie a error handling jsou otestované
- Pydantic validace odpovědí je připravená
- Health check endpoint je funkční

### Alternatives Considered
1. **Přímé HTTP volání** - Zamítnuto kvůli duplikaci kódu
2. **Nový specializovaný client** - Zamítnuto, existující client je dostatečně flexibilní

---

## 2. Query Type Detection

### Decision
Implementovat rule-based klasifikaci dotazů s možností budoucího rozšíření na LLM-based.

### Rationale
- Rychlé a deterministické
- Nevyžaduje LLM volání pro každý dotaz
- Snadné testování
- Dostatečné pro MVP

### Query Types
| Type | Keywords/Patterns | SÚKL Tool |
|------|------------------|-----------|
| `search` | název léku, vyhledej, najdi | `search_medicine` |
| `details` | složení, indikace, kontraindikace, dávkování | `get_medicine_details` |
| `reimbursement` | cena, úhrada, pojišťovna, kategorie | `get_reimbursement` |
| `availability` | dostupnost, alternativa, náhrada | `check_availability` |
| `atc` | ATC kód, klasifikace | `get_atc_info` |
| `ingredient` | účinná látka, složka | `search_by_ingredient` |

### Alternatives Considered
1. **LLM-based intent detection** - Přidáno jako budoucí vylepšení (Feature 007)
2. **NLP keyword extraction** - Zbytečná komplexita pro MVP

---

## 3. Response Formatting

### Decision
Transformovat SÚKL odpovědi na `langchain_core.documents.Document` s metadaty pro citace.

### Rationale
- Konzistentní formát pro všechny agenty
- Podpora citací ([SÚKL: registrační_číslo])
- Integrace s budoucím Citation System (Feature 008)

### Document Structure
```python
Document(
    page_content="Ibalgin 400 - ibuprofen 400mg...",
    metadata={
        "source": "sukl",
        "source_type": "pharmaceutical_database",
        "registration_number": "58/123/01-C",
        "atc_code": "M01AE01",
        "retrieved_at": "2026-01-17T10:30:00Z",
        "tool_used": "search_medicine"
    }
)
```

### Alternatives Considered
1. **Raw JSON response** - Zamítnuto, nekonzistentní s ostatními agenty
2. **Custom DrugDocument class** - Zamítnuto, Document je dostatečně flexibilní

---

## 4. Error Handling Strategy

### Decision
Graceful degradation s user-friendly chybovými zprávami v češtině.

### Rationale
- Uživatelé jsou čeští lékaři
- Chybové zprávy musí být srozumitelné
- Retry strategie z Feature 002 zajistí robustnost

### Error Messages
| Error Type | Czech Message |
|------------|---------------|
| `MCPConnectionError` | "Nelze se připojit k databázi SÚKL. Zkuste to prosím později." |
| `MCPTimeoutError` | "Dotaz trval příliš dlouho. Zkuste zúžit vyhledávání." |
| `MCPServerError` | "Služba SÚKL je dočasně nedostupná. Zkuste to za chvíli." |
| `NoResults` | "Žádný lék odpovídající '{query}' nebyl nalezen." |

---

## 5. State Extension Pattern

### Decision
Přidat `drug_query: Optional[DrugQuery]` do State dataclass.

### Rationale
- Minimální změna existující struktury
- Optional field nezlomí existující testy
- DrugQuery model poskytuje typovou bezpečnost

### DrugQuery Model
```python
class DrugQuery(BaseModel):
    query_text: str
    query_type: QueryType  # Enum: search, details, reimbursement, etc.
    filters: Optional[Dict[str, Any]] = None
    limit: int = 10
```

### Alternatives Considered
1. **Parsování z messages** - Zachováno jako fallback
2. **Separate drug_state field** - Zbytečná komplexita

---

## 6. LangGraph Node Pattern

### Decision
Jednoduchý async node s workflow: extract → classify → call → transform → return.

### Rationale
- Dodržuje Constitution Principle I (Graph-Centric)
- Jednoduchý pro testování
- Snadno rozšiřitelný

### Node Flow
```
[drug_agent_node]
    ↓
1. Extract query (from drug_query or messages)
    ↓
2. Classify query type
    ↓
3. Call SUKLMCPClient.call_tool()
    ↓
4. Transform to Documents
    ↓
5. Return {retrieved_docs, messages, next}
```

---

## 7. Testing Strategy

### Decision
Kombinace unit testů s mocky a integration testů s aioresponses.

### Rationale
- Unit testy: rychlé, izolované, TDD workflow
- Integration testy: end-to-end ověření s mock HTTP

### Test Structure
```
tests/
├── unit_tests/
│   └── nodes/
│       └── test_drug_agent.py      # 15+ test cases
└── integration_tests/
    └── test_drug_agent_flow.py     # 5+ flow tests
```

### Coverage Target
- Unit tests: ≥90% (per spec SC-006)
- Integration tests: happy path + error paths

---

## Závěr

Všechny technické otázky byly zodpovězeny. Žádné NEEDS CLARIFICATION nezůstává nevyřešeno. Plán je připraven pro Phase 1 design.
