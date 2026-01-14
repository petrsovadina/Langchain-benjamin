# 🚀 Quick Start Guide - Czech MedAI (Benjamin)

Tento průvodce vás provede kompletním setupem a prvním vývojovým cyklem v projektu Czech MedAI.

## ⚡ 5-Minute Setup

### 1. Požadavky

```bash
# Python ≥3.10
python --version

# Git (doporučeno)
git --version

# uv package manager (volitelné, ale rychlejší)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone & Setup

```bash
# Clone repository
git clone https://github.com/petrsovadina/Langchain-benjamin.git
cd Langchain-benjamin

# Přejděte do aplikace
cd langgraph-app

# Instalace závislostí (volba A - pip)
pip install -e .
pip install langgraph-cli[inmem]

# Nebo (volba B - uv, rychlejší)
uv venv
uv pip install -e .
uv pip install langgraph-cli[inmem]
```

### 3. Environment Setup

```bash
# Kopírovat environment šablonu
cp .env.example .env

# Editovat .env a přidat klíče (volitelné)
# LANGSMITH_API_KEY=lsv2_pt_...
# LANGSMITH_PROJECT=czech-medai-dev
```

### 4. Spustit Development Server

```bash
langgraph dev
```

✅ LangGraph Studio se otevře na http://localhost:8000

## 📚 Základní Koncepty

### Constitution (5 Principů)

Projekt je řízen 5 základními principy v `.specify/memory/constitution.md`:

1. **Graph-Centric Architecture** - Vše jako LangGraph nody/edges
2. **Type Safety** - Strict typing s mypy --strict
3. **Test-First Development** - Testy PŘED implementací
4. **Observability** - LangSmith tracing
5. **Modular Design** - Malé, zaměřené nody

### SpecKit Workflow

SpecKit je framework pro strukturovaný vývoj features:

```
Constitution → Specify → Analyze → Plan → Tasks → Implement
```

## 🎯 Váš První Feature

### Krok 1: Vytvoření Feature

```bash
cd langgraph-app

# Vytvořit novou feature branch a spec
make speckit_new FEATURE="Add greeting node to graph"

# Nebo manuálně:
../.specify/scripts/bash/create-new-feature.sh "Add greeting node"
```

To vytvoří:
- ✅ Branch: `002-greeting-node` (auto-increment)
- ✅ Directory: `specs/002-greeting-node/`
- ✅ File: `specs/002-greeting-node/spec.md`

### Krok 2: Specifikace (Claude Code)

V Claude Code:

```
/speckit.specify
```

Claude vytvoří kompletní specifikaci s:
- User stories
- Acceptance criteria
- Functional & non-functional requirements

**Alternativně:** Editujte `spec.md` manuálně

### Krok 3: Plánování

```bash
# Vytvořit implementation plan
make speckit_plan

# Nebo manuálně:
../.specify/scripts/bash/setup-plan.sh
```

V Claude Code:

```
/speckit.plan
```

Claude vyplní `plan.md` s:
- Constitution Check (ověření všech 5 principů)
- Technical context
- Phase breakdown
- Code examples

### Krok 4: Task Breakdown

V Claude Code:

```
/speckit.tasks
```

Claude vytvoří `tasks.md` s atomickými úkoly.

### Krok 5: Implementace (Test-First!)

V Claude Code:

```
/speckit.implement "Write tests for greeting node"
/speckit.implement "Implement greeting node"
```

**Nebo manuálně:**

```bash
# 1. Napsat test FIRST (v tests/unit_tests/)
cd langgraph-app

# 2. Spustit test (musí selhat)
make test

# 3. Implementovat (v src/agent/graph.py)

# 4. Spustit test (musí projít)
make test

# 5. Linting & formátování
make lint
make format
```

### Krok 6: Commit & Push

```bash
git add .
git commit -m "feat: Add greeting node to graph"
git push origin 002-greeting-node
```

## 🛠️ Denní Workflow

### Development Commands

```bash
# Spustit dev server
langgraph dev

# Spustit testy
make test
make test_watch  # Watch mode

# Kvalita kódu
make lint        # Kontrola
make format      # Auto-fix

# Spell check
make spell_check
```

### SpecKit Commands (v Claude Code)

```
/speckit.constitution  - Správa Constitution
/speckit.specify       - Vytvoření specifikace
/speckit.analyze       - Analýza spec
/speckit.clarify       - Vyřešení ambiguities
/speckit.plan          - Implementační plán
/speckit.tasks         - Task breakdown
/speckit.implement     - AI-asistovaná implementace
```

### Makefile SpecKit Commands

```bash
make speckit_help      # Zobrazit SpecKit help
make speckit_new       # Nová feature
make speckit_plan      # Setup plánu
make speckit_check     # Kontrola prerekvizit
```

## 📖 Struktura Projektu

```
Langchain-benjamin/
├── CLAUDE.md              # Guide pro Claude Code instances
├── QUICKSTART.md          # Tento soubor
├── .specify/
│   ├── README.md          # SpecKit dokumentace
│   ├── memory/
│   │   └── constitution.md   # Constitution (5 principů)
│   └── templates/         # Šablony pro spec/plan/tasks
├── specs/
│   ├── ROADMAP.md         # Master roadmap (12 features)
│   └── ###-feature-name/
│       ├── spec.md        # Feature specification
│       ├── plan.md        # Implementation plan
│       └── tasks.md       # Task breakdown
└── langgraph-app/
    ├── src/agent/
    │   └── graph.py       # Core graph definition
    ├── tests/
    │   ├── unit_tests/
    │   └── integration_tests/
    ├── Makefile           # Development commands
    └── langgraph.json     # LangGraph server config
```

## 🎓 Learning Path

### Týden 1: Základy

1. **Přečtěte:**
   - `CLAUDE.md` - Základní orientace
   - `.specify/memory/constitution.md` - 5 principů
   - `.specify/README.md` - SpecKit workflow

2. **Prostudujte:**
   - `specs/001-langgraph-foundation/spec.md` - Příklad specifikace
   - `specs/001-langgraph-foundation/plan.md` - Příklad plánu

3. **Prakticky:**
   - Vytvořte trivial feature (např. echo node)
   - Projděte celý SpecKit workflow
   - Commitněte vaši první změnu

### Týden 2: LangGraph Patterns

1. **Studujte:**
   - `src/agent/graph.py` - Základní graph struktura
   - LangGraph Docs: https://langchain-ai.github.io/langgraph/

2. **Implementujte:**
   - Node s conditional routing
   - State updates s reducers
   - Context-aware node

### Týden 3: Multi-Agent Architecture

1. **Prozkoumejte:**
   - `specs/ROADMAP.md` - Plánované agenty
   - PRD dokumentaci v `PRD-docs/`

2. **Přispějte:**
   - Implementujte část agent workflow
   - Review code jiných features

## 🐛 Troubleshooting

### "Not on a feature branch"

```bash
# Vytvořte feature branch:
make speckit_new FEATURE="Your feature"
```

### "Python version mismatch"

```bash
# Použijte pyenv pro správu verzí:
pyenv install 3.10
pyenv local 3.10
```

### "LangGraph dev nepracuje"

```bash
# Reinstalujte LangGraph CLI:
pip install --upgrade langgraph-cli[inmem]

# Nebo s uv:
uv pip install --upgrade langgraph-cli[inmem]
```

### "Tests fail"

```bash
# Zkontrolujte, že jste v správném adresáři:
cd langgraph-app

# Spusťte pouze failing test:
make test TEST_FILE=tests/unit_tests/test_specific.py

# Verbose output:
python -m pytest tests/unit_tests/ -vv
```

### "mypy errors"

```bash
# Spusťte type check:
make lint

# Fix common issues:
# - Přidejte type hints všude
# - Použijte TypedDict pro dictionaries
# - Annotated pro state fields
```

## 📚 Další Zdroje

### Dokumentace

- **CLAUDE.md** - Kompletní reference pro Claude Code
- **.specify/README.md** - SpecKit kompletní dokumentace
- **Constitution** - `.specify/memory/constitution.md`
- **Roadmap** - `specs/ROADMAP.md`

### Externí Odkazy

- **LangGraph**: https://langchain-ai.github.io/langgraph/
- **LangSmith**: https://docs.smith.langchain.com/
- **LangChain**: https://python.langchain.com/

### PRD Dokumentace

V `PRD-docs/` najdete:
- Bílá kniha (strategic vision)
- PRD (product requirements)
- Architektura (deep-dive)
- UX design specs

## 🤝 Contributing

### Před prvním PR:

1. ✅ Přečtěte Constitution
2. ✅ Projděte existující spec/plan
3. ✅ Použijte SpecKit workflow
4. ✅ Napište testy PŘED implementací
5. ✅ Zkontrolujte lint & format
6. ✅ Update dokumentaci

### PR Checklist:

- [ ] Constitution Check passed (všech 5 principů)
- [ ] Testy napsány a passed
- [ ] `make lint` passed
- [ ] `make format` applied
- [ ] Dokumentace updated (spec.md, plan.md)
- [ ] Commit messages conventional format

## 💡 Tips

### Produktivita

- Použijte `make test_watch` pro TDD workflow
- LangGraph Studio pro vizuální debugging
- LangSmith pro production traces
- `.env` pro API keys (never commit!)

### Best Practices

- **Commitujte často** - Malé, atomické commits
- **Testujte nejdříve** - Princip III je neporušitelný
- **Dokumentujte změny** - Update spec.md průběžně
- **Review Constitution** - Před každou feature

### Shortcuts

```bash
# Alias pro SpecKit (přidejte do ~/.bashrc nebo ~/.zshrc)
alias sn='make speckit_new FEATURE='
alias sp='make speckit_plan'
alias sc='make speckit_check'

# Pak použijte:
sn "Add new feature"
sp
```

## 🎉 Úspěch!

Nyní jste připraveni začít vyvíjet v projektu Czech MedAI!

**První úkol**: Vytvořte svou první feature pomocí SpecKit workflow výše.

**Otázky?** Podívejte se do:
- `.specify/README.md` (SpecKit docs)
- `CLAUDE.md` (Claude Code guide)
- Constitution (`.specify/memory/constitution.md`)

**Happy coding!** 🚀

---

**Version**: 1.0.0
**Last Updated**: 2026-01-13
**Next Steps**: Explore `specs/001-langgraph-foundation/` for real-world example
