# Czech MedAI (Benjamin) 🏥🤖

Multi-agentní AI asistent pro české lékaře postavený na LangGraph frameworku. Poskytuje klinickou rozhodovací podporu založenou na důkazech, integrující specializované AI agenty pro dotazování českých medicínských zdrojů (SÚKL, VZP, ČLS JEP) a mezinárodního výzkumu (PubMed) s kompletním sledováním citací.

[![CI](https://github.com/langchain-ai/new-langgraph-project/actions/workflows/unit-tests.yml/badge.svg)](https://github.com/langchain-ai/new-langgraph-project/actions/workflows/unit-tests.yml)
[![Integration Tests](https://github.com/langchain-ai/new-langgraph-project/actions/workflows/integration-tests.yml/badge.svg)](https://github.com/langchain-ai/new-langgraph-project/actions/workflows/integration-tests.yml)

## 🚀 Quick Start

```bash
# 1. Clone repository
git clone https://github.com/petrsovadina/Langchain-benjamin.git
cd Langchain-benjamin/langgraph-app

# 2. Instalace
pip install -e .
pip install langgraph-cli[inmem]

# 3. Environment setup
cp .env.example .env
# Editujte .env a přidejte klíče (volitelné)

# 4. Spustit dev server
langgraph dev
# → LangGraph Studio na http://localhost:8000
```

**📖 Detailní návod:** Viz [QUICKSTART.md](./QUICKSTART.md)

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

## 🏗️ Architektura

### Multi-Agent Pattern

```
User Query (CZ)
    ↓
[Supervisor Node] → Klasifikace intentu (8 typů)
    ↓
    ├─→ [Drug Agent] → SÚKL-mcp (8 tools, 68k+ léků)
    ├─→ [Pricing Agent] → VZP LEK-13 (exact match)
    ├─→ [PubMed Agent] → BioMCP (24 tools) + CZ→EN→CZ translation
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

# Testy
make test                    # Unit testy
make integration_tests       # Integrační testy
make test_watch             # Watch mode

# Kvalita kódu
make lint                    # ruff + mypy (strict)
make format                  # Auto-format
make spell_check            # Spell check
```

### CI/CD

- **Unit Tests:** Běží při každém push (Python 3.11, 3.12)
- **Integration Tests:** Denně v 14:37 UTC (vyžaduje API klíče)
- **Linting:** ruff + mypy --strict enforced
- **Spell Check:** codespell

## 🗺️ Roadmap

### Fáze 0: Foundation (Aktuální - Týdny 1-2)
- [x] **001-langgraph-foundation** - AgentState, Context, LangSmith setup
- [ ] **002-mcp-infrastructure** - MCP protocol, Docker, Supabase

### Fáze 1: Core Agents (Týdny 3-6)
- [ ] **003-sukl-drug-agent** - SÚKL drug search
- [ ] **004-vzp-pricing-agent** - VZP pricing & coverage
- [ ] **005-biomcp-pubmed-agent** - PubMed research (BioMCP)
- [ ] **006-guidelines-agent** - ČLS JEP guidelines

### Fáze 2: Integration (Týdny 7-9)
- [ ] **007-supervisor-orchestration** - Intent routing
- [ ] **008-citation-system** - Citation tracking
- [ ] **009-synthesizer-node** - Response synthesis

### Fáze 3: UX & Deployment (Týdny 10-12)
- [ ] **010-czech-localization** - České lokalizace
- [ ] **011-fastapi-backend** - REST API
- [ ] **012-nextjs-frontend** - Chat interface

**📖 Detailní Roadmap:** [specs/ROADMAP.md](./specs/ROADMAP.md)

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

### "Not on a feature branch"
```bash
make speckit_new FEATURE="Your feature"
```

### "LangGraph dev doesn't work"
```bash
pip install --upgrade langgraph-cli[inmem]
```

### "Tests fail"
```bash
cd langgraph-app
make test TEST_FILE=tests/unit_tests/test_specific.py
```

### "mypy type errors"
```bash
make lint  # Shows all errors
# Fix: Přidejte type hints, použijte TypedDict, Annotated
```

**📖 Více troubleshooting:** [QUICKSTART.md - Troubleshooting](./QUICKSTART.md#-troubleshooting)

## 📊 Project Status

**Current Phase:** Foundation (Fáze 0)
**Current Branch:** `001-langgraph-foundation`
**Main Branch:** `main`

**Progress:**
- ✅ Constitution vytvořena (v1.0.1)
- ✅ SpecKit framework inicializován
- ✅ Foundation spec hotová
- ✅ Foundation plan hotový
- 🚧 Foundation implementace probíhá
- ⏳ MCP infrastructure čeká

## 📜 License

[Specify your license here]

## 👥 Team

Czech MedAI Development Team

## 📧 Contact

[Specify contact information]

---

**Verze:** 1.0.0 (Foundation Phase)
**Poslední aktualizace:** 2026-01-13

**🚀 Ready to start?** → [QUICKSTART.md](./QUICKSTART.md)
