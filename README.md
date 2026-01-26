# Czech MedAI (Benjamin) 🏥🤖

Multi-agentní AI asistent pro české lékaře postavený na LangGraph frameworku. Poskytuje klinickou rozhodovací podporu založenou na důkazech, integrující specializované AI agenty pro dotazování českých medicínských zdrojů (SÚKL, VZP, ČLS JEP) a mezinárodního výzkumu (PubMed) s kompletním sledováním citací.

[![CI](https://github.com/langchain-ai/new-langgraph-project/actions/workflows/unit-tests.yml/badge.svg)](https://github.com/langchain-ai/new-langgraph-project/actions/workflows/unit-tests.yml)
[![Integration Tests](https://github.com/langchain-ai/new-langgraph-project/actions/workflows/integration-tests.yml/badge.svg)](https://github.com/langchain-ai/new-langgraph-project/actions/workflows/integration-tests.yml)

## 🚀 Quick Start

```bash
# 1. Clone repository
git clone https://github.com/petrsovadina/Langchain-benjamin.git
cd Langchain-benjamin/langgraph-app

# 2. Instalace (doporučeno: uv)
# Instalace uv (fast Python package installer)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Vytvoření virtual environment
uv venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

# Instalace závislostí
uv pip install -e .
uv pip install 'langgraph-cli[inmem]'

# 3. Environment setup
cp .env.example .env
# Editujte .env a přidejte API klíče:
# - ANTHROPIC_API_KEY (AKTUÁLNĚ pro translation, BUDE OPTIONAL po Feature 005 Refactoring)
# - LANGSMITH_API_KEY (volitelné - pro tracing)

# 4. Spustit dev server
# DŮLEŽITÉ: Použijte dev.sh script nebo nastavte PYTHONPATH
./dev.sh
# NEBO manuálně:
# PYTHONPATH=src langgraph dev

# → LangGraph Studio na https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
```

**📖 Detailní návod:** Viz [QUICKSTART.md](./QUICKSTART.md)

### ⚠️ Důležité Poznámky

- **PYTHONPATH**: Server vyžaduje `PYTHONPATH=src` pro správný import modulů
- **dev.sh script**: Automaticky nastavuje PYTHONPATH a aktivuje venv
- **API klíče**:
  - **AKTUÁLNĚ**: Translation nodes vyžadují ANTHROPIC_API_KEY nebo OPENAI_API_KEY
  - **PLÁNOVÁNO**: Po Feature 005 Refactoring bude ANTHROPIC_API_KEY volitelný (direct Czech processing)
- **LangGraph CLI**: Běží v pipx prostředí, proto potřebujeme PYTHONPATH

## 📋 Co je Czech MedAI?

Czech MedAI (kódové jméno "Benjamin") je AI-powered systém určený pro české lékaře, který:

- ✅ **Odpovídá na klinické dotazy** s důkazy z vědecké literatury
- ✅ **Vyhledává informace o lécích** z databáze SÚKL (~100k záznamů)
- ✅ **Kontroluje ceny a úhrady** z VZP LEK-13 databáze
- ✅ **Cituje české i mezinárodní guidelines** (ČLS JEP, PubMed)
- ✅ **Sleduje citace** pro každé tvrzení [1][2][3]
- ✅ **Komunikuje v češtině** s podporou medicínské terminologie

### 🎯 Cílová Skupina

- Praktičtí lékaři (všeobecné lékařství)
- Specialisté (kardiologie, diabetologie, onkologie, ...)
- Farmaceuti
- Zdravotní sestry a studenti medicíny

### 🔄 Aktuální Vývoj

**Feature 005 Refactoring** (v plánu):
- 🎯 Odstranění zbytečného translation layer (CZ→EN→PubMed→EN→CZ)
- 🚀 Využití nativních multilingvních schopností Claude Sonnet 4.5
- 📊 Očekávané výsledky: 40-50% rychlejší, 66% levnější, jednodušší architektura
- 📋 Specifikace: `specs/005-remove-translation-layer/` (spec, plan, 44 tasks ready)

## 🏗️ Architektura

### Multi-Agent Pattern

```
User Query (CZ)
    ↓
[Supervisor Node] → Klasifikace intentu (8 typů)
    ↓
    ├─→ [Drug Agent] → SÚKL-mcp (8 tools, 68k+ léků)
    ├─→ [Pricing Agent] → VZP LEK-13 (exact match)
    ├─→ [PubMed Agent] → BioMCP (24 tools)
    │    └─→ CURRENT: CZ→EN→CZ translation (BUDE ODSTRANĚNO)
    │    └─→ PLANNED: Direct Czech processing (Feature 005 Refactoring)
    └─→ [Guidelines Agent] → ČLS JEP PDFs (pgvector)
    ↓
[Citation System] → Konsolidace referencí
    ↓
[Synthesizer Node] → Kombinace + formátování
    ↓
Response (CZ) s inline citacemi [1][2][3]
```

**MCP Servery**:
- **SÚKL-mcp**: Czech pharmaceutical DB - https://github.com/petrsovadina/SUKL-mcp
- **BioMCP**: Biomedical databases - https://github.com/genomoncology/biomcp

### Tech Stack

- **Framework:** LangGraph ≥1.0.0 (multi-agent orchestrace)
- **Language:** Python ≥3.10 (async-first)
- **Testing:** pytest s async podporou
- **Code Quality:** ruff (linting/formatting), mypy (strict type checking)
- **Database:** Supabase + pgvector
- **Observability:** LangSmith tracing
- **Protocol:** MCP (Model Context Protocol) pro data sources

**Frontend (plánováno):**
- Next.js 14 s TypeScript
- TailwindCSS, shadcn/ui
- Server-Sent Events (SSE) streaming

**Backend (plánováno):**
- FastAPI s WebSocket/SSE support
- Redis caching
- Docker + Docker Compose

## 📁 Struktura Projektu

```
Langchain-benjamin/
├── README.md                  # Tento soubor
├── QUICKSTART.md              # Rychlý start guide
├── CLAUDE.md                  # Guide pro Claude Code instances
│
├── .specify/                  # SpecKit Framework
│   ├── README.md              # SpecKit dokumentace
│   ├── speckit.sh             # Shell helpers (source me!)
│   ├── memory/
│   │   └── constitution.md    # Project Constitution (5 principů)
│   ├── templates/             # Šablony pro spec/plan/tasks
│   └── scripts/               # Bash skripty pro workflow
│
├── specs/                     # Feature Specifications
│   ├── ROADMAP.md             # Master roadmap (12 features, 4 fáze)
│   └── ###-feature-name/      # Jednotlivé features
│       ├── spec.md            # User stories, požadavky
│       ├── plan.md            # Implementační plán
│       └── tasks.md           # Task breakdown
│
├── PRD-docs/                  # Kompletní PRD dokumentace
│   ├── 01-strategicke-dokumenty/
│   │   ├── 01-bila-kniha.md   # Strategická vize
│   │   └── 02-prd-produktovy-brief.md
│   ├── 02-pozadavky-a-uzivatelske-scenare/
│   ├── 03-architektura-a-technicka-dokumentace/
│   └── 04-specifikace-komponent/
│
├── langgraph-app/             # Hlavní aplikace (Python)
│   ├── src/agent/
│   │   └── graph.py           # Core LangGraph definition
│   ├── tests/
│   │   ├── unit_tests/
│   │   └── integration_tests/
│   ├── Makefile               # Development commands
│   ├── pyproject.toml         # Dependencies
│   └── langgraph.json         # LangGraph server config
│
└── .github/
    ├── agents/                # SpecKit AI agents
    │   └── speckit.*.agent.md
    ├── prompts/               # Agent prompts
    │   └── speckit.*.prompt.md
    └── workflows/             # CI/CD
        ├── unit-tests.yml
        └── integration-tests.yml
```

## 🎯 Constitution (5 Principů)

Projekt je řízen 5 základními principy v `.specify/memory/constitution.md`:

### I. Graph-Centric Architecture
**VŠECHNY** features MUSÍ být implementovány jako LangGraph nody a edges. Graf musí být vizualizovatelný v LangGraph Studio.

### II. Type Safety & Schema Validation
**VŠE** state a context MUSÍ používat typed dataclasses/TypedDict. Strict type checking s mypy --strict.

### III. Test-First Development (NEPORUŠITELNÉ!)
**Testy MUSÍ být napsány PŘED implementací**. Workflow: Napsat test → Fail → Implementovat → Pass.

### IV. Observability & Debugging
**VŠECHNY** graph executions MUSÍ být sledovatelné přes LangSmith tracing. Logování state transitions.

### V. Modular & Extensible Design
Každý node MUSÍ mít jednu jasnou zodpovědnost. Preference vícero malých nodů než jeden velký.

**📖 Kompletní Constitution:** [.specify/memory/constitution.md](./.specify/memory/constitution.md)

## 🛠️ Development Workflow

### SpecKit Framework

SpecKit poskytuje strukturovaný workflow pro vývoj features:

```bash
# 1. Vytvoření nové feature
cd langgraph-app
make speckit_new FEATURE="Add PubMed search integration"
# → Vytvoří branch: 005-pubmed-search
# → Vytvoří spec: specs/005-pubmed-search/spec.md

# 2. V Claude Code - Specifikace
# /speckit.specify

# 3. V Claude Code - Plánování
make speckit_plan
# /speckit.plan

# 4. V Claude Code - Task breakdown
# /speckit.tasks

# 5. V Claude Code - Implementace (test-first!)
# /speckit.implement "Task description"

# 6. Commit & Push
git commit -m "feat: Add PubMed search integration"
git push origin 005-pubmed-search
```

### SpecKit Commands

**Makefile příkazy:**
```bash
make speckit_help      # Zobrazit help
make speckit_new       # Nová feature
make speckit_plan      # Setup plánu
make speckit_check     # Kontrola prerekvizit
```

**Shell helpers** (source `.specify/speckit.sh`):
```bash
source .specify/speckit.sh

sn "Feature description"  # Nová feature
sp                        # Setup plánu
si                        # Feature info
sl                        # List všech features
sed                       # Edit spec.md
ped                       # Edit plan.md
```

**Claude Code příkazy:**
- `/speckit.constitution` - Správa Constitution
- `/speckit.specify` - Vytvoření specifikace
- `/speckit.analyze` - Analýza spec
- `/speckit.plan` - Implementační plán
- `/speckit.tasks` - Task breakdown
- `/speckit.implement` - AI-asistovaná implementace

**📖 SpecKit Dokumentace:** [.specify/README.md](./.specify/README.md)

## 🧪 Testing & Quality

```bash
cd langgraph-app

# Development Server
./dev.sh                    # Spustit dev server (doporučeno)
PYTHONPATH=src langgraph dev # Nebo manuálně

# Testy
make test                    # Unit testy
make integration_tests       # Integrační testy
make test_watch             # Watch mode

# Kvalita kódu
make lint                    # ruff + mypy (strict)
make format                  # Auto-format
make spell_check            # Spell check

# Manuální test spouštění (s PYTHONPATH)
PYTHONPATH=src uv run pytest tests/unit_tests/ -v
PYTHONPATH=src uv run mypy --strict src/agent/graph.py
```

### CI/CD

- **Unit Tests:** Běží při každém push (Python 3.11, 3.12)
- **Integration Tests:** Denně v 14:37 UTC (vyžaduje API klíče)
- **Linting:** ruff + mypy --strict enforced
- **Spell Check:** codespell

## 🗺️ Roadmap

### ✅ Fáze 0: Foundation (DOKONČENO - Týdny 1-2)

#### ✅ Feature 001: LangGraph Foundation (5 dní)
- ✅ State dataclass s typed fields (messages, next, retrieved_docs)
- ✅ Context TypedDict s runtime konfigurací (model_name, temperature, MCP clients)
- ✅ pytest fixtures (mock_runtime, sample_state)
- ✅ LangSmith tracing setup s graceful degradation
- ✅ placeholder_node jako reference implementace

#### ✅ Feature 002: MCP Infrastructure (4 dny)
- ✅ **SUKLMCPClient** wrapper s domain-driven design
  - 8 MCP tools (search_medicine, get_details, PIL/SPC, reimbursement)
  - Retry strategies s exponential backoff (3 attempts, 2^n delay)
  - Error handling hierarchy (MCPError → MCPValidationError → MCPServerError)
- ✅ **BioMCPClient** wrapper
  - 24 tools pro biomedical databases
  - article_searcher, article_getter pro PubMed integration
- ✅ MCP protocol integration s async communication patterns

---

### 🔄 Fáze 1: Core Agents (3/4 DOKONČENO - Týdny 3-6)

#### ✅ Feature 003: SÚKL Drug Agent (8 dní)
- ✅ drug_agent_node implementace
- ✅ SÚKL-mcp integration s 8 tools
- ✅ Fuzzy search s typo tolerance (rapidfuzz, threshold 80)
- ✅ Document transformation (PIL/SPC → LangChain Documents)
- ✅ Multi-kriteriální ranking pro alternativy
- ✅ Metadata preservation (ATC kódy, ceny, úhrady)

#### ⏳ Feature 004: VZP Pricing Agent (6 dní) - ČEKÁ NA IMPLEMENTACI
- ⏳ pricing_agent_node s VZP LEK-13 integration
- ⏳ Exact match vyhledávání (KÓDL, název léku)
- ⏳ Kategorie úhrad parsing (A/B/D)
- ⏳ Předepisovatelnost a limitace

#### ✅ Feature 005: BioMCP PubMed Agent (7 dní) - DOKONČENO + HOTFIX
- ✅ **pubmed_agent_node** implementace
  - BioMCP article_searcher integration (abstract search)
  - BioMCP article_getter integration (PMID lookup)
  - ResearchQuery model s filters (date_range, article_types)
- ✅ **Translation nodes** (Sandwich Pattern: CZ→EN→PubMed→EN→CZ)
  - translate_cz_to_en_node s medicínskou terminologií
  - translate_en_to_cz_node s metadata preservation
  - ⚠️ **BUDE ODSTRANĚNO v Feature 005 Refactoring**
- ✅ **Citation tracking**
  - Inline references [1][2][3] v responses
  - Reference section s kompletními citacemi
  - format_citation helper pro IEEE style
- ✅ **Phase 7 Quality Polish**
  - mypy --strict: 0 errors (100% type safety)
  - ruff check: All checks passed
  - ruff format: 27 files reformatted
  - Test coverage: 177/183 passing (97%)
  - Performance validated: <5s latency (SC-001)
- ✅ **Multimodal Content Fix (2026-01-25)**
  - Fixed AttributeError: `route_query` now handles LangGraph Studio multimodal content
  - Content normalization for `list[ContentBlock]` format
  - 8 new routing tests covering all message formats
  - Commit: `a8429ba`

#### 🔄 Feature 005 Refactoring: Remove Translation Layer (PLÁNOVÁNO)
- 📋 **Status**: Specifikace, plán a 44 tasks připraveny k implementaci
- 🎯 **Cíl**: Odstranit Sandwich Pattern, využít nativní Claude Sonnet 4.5 multilingvní capabilities
- 📊 **Očekávané výsledky**:
  - 40-50% rychlejší odpovědi (8-10s → ≤5s)
  - 66% úspora nákladů (3 LLM calls → 1 call)
  - Jednodušší architektura (5 nodes → 3 nodes)
  - Lepší kvalita češtiny (žádné translation artifacts)
- 📁 **Dokumentace**: `specs/005-remove-translation-layer/`
  - spec.md (9 funkčních požadavků, 3 user scenarios)
  - plan.md (12 high-level tasks, constitution check)
  - tasks.md (44 detailed tasks v 11 fázích)
  - checklists/requirements.md (✅ APPROVED)
- ⏱️ **Časový odhad**: 4-5 hodin (single developer, focused work)

#### ⏳ Feature 006: Guidelines Agent (8 dní) - PLÁNOVÁNO
- ⏳ guidelines_agent_node s ČLS JEP PDFs
- ⏳ pgvector semantic search
- ⏳ PDF parsing a chunking
- ⏳ Citation extraction

---

### ⏳ Fáze 2: Integration (PLÁNOVÁNO - Týdny 7-9)

#### ⏳ Feature 007: Supervisor Orchestration (9 dní)
- ⏳ supervisor_node s intent classification (8 typů)
- ⏳ Multi-agent routing logic
- ⏳ Conditional edges pro agent selection

#### ⏳ Feature 008: Citation System (6 dní)
- ⏳ Cross-agent citation consolidation
- ⏳ Deduplikace referencí
- ⏳ Citation formatting (IEEE, AMA, APA)

#### ⏳ Feature 009: Synthesizer Node (5 dní)
- ⏳ Response synthesis z multiple agents
- ⏳ Inline citation insertion
- ⏳ Markdown formatting

---

### ⏳ Fáze 3: UX & Deployment (PLÁNOVÁNO - Týdny 10-12)

#### ⏳ Feature 010: Czech Localization (4 dny)
- ⏳ Kompletní české UI/UX texty
- ⏳ Error messages v češtině
- ⏳ Medical terminology dictionary

#### ⏳ Feature 011: FastAPI Backend (6 dní)
- ⏳ REST API endpoints
- ⏳ WebSocket/SSE streaming
- ⏳ Redis caching layer
- ⏳ Docker containerization

#### ⏳ Feature 012: Next.js Frontend (10 dní)
- ⏳ Chat interface s streaming
- ⏳ Citation popups
- ⏳ TailwindCSS + shadcn/ui
- ⏳ Mobile-responsive design

---

**📊 Aktuální Progress**: 3/12 features dokončeno (25%) | Constitution v1.0.3 | Test Coverage: 97%
**🔄 V Plánu**: Feature 005 Refactoring (remove translation layer) - spec/plan/tasks ready

**📖 Detailní Roadmap s tasky:** [specs/ROADMAP.md](./specs/ROADMAP.md)

## 📚 Dokumentace

### Pro Vývojáře

- **[QUICKSTART.md](./QUICKSTART.md)** - Rychlý start guide (5 minut)
- **[CLAUDE.md](./CLAUDE.md)** - Kompletní guide pro Claude Code
- **[MCP_INTEGRATION.md](./MCP_INTEGRATION.md)** - MCP servery integration guide
- **[BIOAGENTS_INSPIRATION.md](./BIOAGENTS_INSPIRATION.md)** - Architektonické vzory z BioAgents
- **[.specify/README.md](./.specify/README.md)** - SpecKit framework dokumentace
- **[.specify/memory/constitution.md](./.specify/memory/constitution.md)** - Constitution (5 principů)

### Specifikace Features

- **[specs/ROADMAP.md](./specs/ROADMAP.md)** - Master roadmap
- **specs/001-langgraph-foundation/** - Foundation feature (příklad)
  - [spec.md](./specs/001-langgraph-foundation/spec.md) - Specifikace
  - [plan.md](./specs/001-langgraph-foundation/plan.md) - Implementační plán
- **specs/005-remove-translation-layer/** - Feature 005 Refactoring (aktuální)
  - [spec.md](./specs/005-remove-translation-layer/spec.md) - 9 FR, 3 user scenarios
  - [plan.md](./specs/005-remove-translation-layer/plan.md) - 12 tasks, constitution check
  - [tasks.md](./specs/005-remove-translation-layer/tasks.md) - 44 detailed tasks
  - [checklists/requirements.md](./specs/005-remove-translation-layer/checklists/requirements.md) - ✅ APPROVED

### PRD Dokumentace

- **PRD-docs/01-strategicke-dokumenty/** - Strategická vize
- **PRD-docs/02-pozadavky-a-uzivatelske-scenare/** - User stories
- **PRD-docs/03-architektura-a-technicka-dokumentace/** - Architektura deep-dive
- **PRD-docs/04-specifikace-komponent/** - Komponenty specs

### Externí Reference

- **LangGraph:** https://langchain-ai.github.io/langgraph/
- **LangSmith:** https://docs.smith.langchain.com/
- **LangChain:** https://python.langchain.com/

## 🤝 Contributing

### Před prvním PR:

1. ✅ Přečtěte [QUICKSTART.md](./QUICKSTART.md)
2. ✅ Prostudujte [Constitution](./.specify/memory/constitution.md)
3. ✅ Použijte SpecKit workflow
4. ✅ Test-first approach (Princip III)
5. ✅ `make lint` && `make format`

### PR Checklist:

- [ ] Constitution Check passed (všech 5 principů)
- [ ] Testy napsány PŘED implementací a passed
- [ ] `make lint` passed (ruff + mypy --strict)
- [ ] `make format` applied
- [ ] Dokumentace updated (spec.md, plan.md)
- [ ] Commit messages: conventional format

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'agent'"
```bash
# LangGraph CLI běží v pipx prostředí - potřebujeme nastavit PYTHONPATH
cd langgraph-app

# Možnost 1: Použít dev.sh script (doporučeno)
./dev.sh

# Možnost 2: Manuálně nastavit PYTHONPATH
PYTHONPATH=src langgraph dev
```

### "Not on a feature branch"
```bash
make speckit_new FEATURE="Your feature"
```

### "LangGraph dev doesn't work" nebo "Old version warning"
```bash
# Upgrade LangGraph CLI
uv pip install --upgrade 'langgraph-cli[inmem]'

# Nebo s pip
pip install --upgrade langgraph-cli[inmem]
```

### "Tests fail"
```bash
cd langgraph-app

# Všechny unit testy
PYTHONPATH=src uv run pytest tests/unit_tests/ -v

# Konkrétní test file
PYTHONPATH=src uv run pytest tests/unit_tests/test_routing.py -v

# S Makefile
make test TEST_FILE=tests/unit_tests/test_specific.py
```

### "Translation tests fail with API error"
```bash
# Translation testy vyžadují API kredity
# Zkontrolujte .env file:
cat .env | grep API_KEY

# Možnost 1: Použít Anthropic
ANTHROPIC_API_KEY=sk-ant-api03-...
TRANSLATION_MODEL=claude-4.5-haiku

# Možnost 2: Použít OpenAI
OPENAI_API_KEY=sk-proj-...
TRANSLATION_MODEL=gpt-4o-mini

# Pak restartujte server
./dev.sh
```

### "mypy type errors"
```bash
make lint  # Shows all errors
# Fix: Přidejte type hints, použijte TypedDict, Annotated
```

### "AttributeError: 'list' object has no attribute 'lower'"
```bash
# Tento bug byl opraven v commit a8429ba (2026-01-25)
# Pokud se objevuje, aktualizujte na nejnovější verzi:
git pull origin 005-biomcp-pubmed-agent

# Ověřte, že máte multimodal content fix:
grep -A 5 "Normalize content to string" src/agent/graph.py
# Měli byste vidět content normalization logic
```

**📖 Více troubleshooting:** [QUICKSTART.md - Troubleshooting](./QUICKSTART.md#-troubleshooting)

## 📊 Project Status

**Current Phase:** Core Agents (Fáze 1) - 3/4 Complete
**Current Branch:** `005-biomcp-pubmed-agent`
**Main Branch:** `main`
**Constitution:** v1.0.3 (Phase 7 quality standards codified)

**Dokončené Features:**
- ✅ **Feature 001**: LangGraph Foundation (State, Context, pytest)
- ✅ **Feature 002**: MCP Infrastructure (SÚKL-mcp + BioMCP clients)
- ✅ **Feature 003**: SÚKL Drug Agent (fuzzy search, 8 MCP tools)
- ✅ **Feature 005**: BioMCP PubMed Agent (včetně Phase 7 Polish)
  - Sandwich Pattern: CZ→EN→PubMed→EN→CZ (⚠️ BUDE ODSTRANĚNO)
  - Citation tracking [1][2][3]
  - Performance: <5s latency (SC-001 validated)
  - Multimodal content fix (commit `a8429ba`)

**V Plánu - Priorita 1:**
- 🔄 **Feature 005 Refactoring**: Remove Translation Layer (spec/plan/tasks READY)
  - Odstranit Sandwich Pattern, direct Czech processing
  - 40-50% rychlejší, 66% levnější, jednodušší architektura
  - 44 tasks v 11 fázích, 4-5h odhad

**V Plánu - Další:**
- ⏳ **Feature 004**: VZP Pricing Agent (VZP LEK-13 integration)
- ⏳ **Feature 006**: Guidelines Agent (ČLS JEP PDFs)
- ⏳ **Fáze 2**: Integration (supervisor, citations, synthesizer)

**Quality Metrics:**
- 📊 Test Coverage: **177/183 passing (97%)**
  - 6 translation tests vyžadují Anthropic API kredity (očekáváno)
- ✅ Type Safety: **mypy --strict** (0 errors)
- ✅ Code Quality: **ruff check** (all checks passed)
- ✅ Formatting: **ruff format** (automated)
- ⚡ Performance: **<5s latency** (SC-001 requirement)
- ✅ Multimodal Content: **LangGraph Studio kompatibilita** (hotfix 2026-01-25)

**Constitution Compliance:**
- ✅ Princip I: Graph-Centric Architecture (všechny features jako LangGraph nodes)
- ✅ Princip II: Type Safety (mypy --strict enforcement)
- ✅ Princip III: Test-First Development (TDD workflow dodržen)
- ✅ Princip IV: Observability (LangSmith tracing configured)
- ✅ Princip V: Modular Design (single-responsibility nodes)

## 📜 License

[Specify your license here]

## 👥 Team

Czech MedAI Development Team

## 📧 Contact

[Specify contact information]

---

**Verze:** 1.1.2 (Core Agents Phase - 3/4 Complete + Feature 005 Refactoring Ready)
**Poslední aktualizace:** 2026-01-25
**Poslední commit:** `a8429ba` (fix: multimodal content handling for LangGraph Studio)
**Aktuální práce:** Feature 005 Refactoring - Remove Translation Layer (spec/plan/44 tasks ready)

**🚀 Ready to start?** → [QUICKSTART.md](./QUICKSTART.md)
