# SpecKit - Feature Specification & Development Framework

SpecKit je komplexní framework pro řízení vývoje features v projektu Czech MedAI (Benjamin). Kombinuje AI-powered workflow s Git branch managementem, automatizovanou dokumentací a enforcement Constitution principů.

## 🎯 Co je SpecKit?

SpecKit poskytuje strukturovaný workflow pro:
- 📝 **Specifikaci features** - User stories, acceptance criteria, požadavky
- 🗺️ **Plánování implementace** - Detailní technické plány s code examples
- ✅ **Task management** - Rozpad na atomické, testovatelné úkoly
- 🔍 **Analýzu a clarifikaci** - Řešení ambiguities před implementací
- 🤖 **AI-asistovaný development** - Claude Code agenty pro každou fázi

## 📁 Struktura

```
.specify/
├── README.md                    # Tento soubor
├── memory/
│   └── constitution.md          # Constitution projektu (5 principů)
├── templates/
│   ├── spec-template.md         # Šablona pro feature specifikaci
│   ├── plan-template.md         # Šablona pro implementační plán
│   ├── tasks-template.md        # Šablona pro task breakdown
│   ├── checklist-template.md    # Šablona pro checklisty
│   └── agent-file-template.md   # Šablona pro agent context files
└── scripts/
    └── bash/
        ├── common.sh                  # Společné funkce pro všechny scripty
        ├── create-new-feature.sh      # Vytvoření nové feature branch
        ├── setup-plan.sh              # Setup implementačního plánu
        ├── check-prerequisites.sh     # Kontrola prerekvizit
        └── update-agent-context.sh    # Update agent context

.github/
├── agents/                      # SpecKit AI agenty
│   ├── speckit.constitution.agent.md
│   ├── speckit.specify.agent.md
│   ├── speckit.plan.agent.md
│   ├── speckit.tasks.agent.md
│   ├── speckit.implement.agent.md
│   ├── speckit.analyze.agent.md
│   ├── speckit.clarify.agent.md
│   ├── speckit.checklist.agent.md
│   └── speckit.taskstoissues.agent.md
└── prompts/                     # Prompty pro agenty
    └── speckit.*.prompt.md

specs/                           # Feature specifikace
├── ROADMAP.md                   # Master roadmap (12 features)
└── ###-feature-name/
    ├── spec.md                  # Feature specification
    ├── plan.md                  # Implementation plan
    ├── tasks.md                 # Task breakdown
    ├── ANALYSIS.md              # Analysis & findings
    └── quickstart.md            # Quick start guide
```

## 🚀 Quick Start

### 1. Vytvoření nové feature

```bash
# Automatické vytvoření feature branch a spec
cd /path/to/repo
.specify/scripts/bash/create-new-feature.sh "Add PubMed agent for research queries"

# Nebo s vlastním názvem
.specify/scripts/bash/create-new-feature.sh "OAuth2 integration" --short-name "oauth"

# Nebo s konkrétním číslem
.specify/scripts/bash/create-new-feature.sh "User authentication" --number 10
```

To vytvoří:
- ✅ Git branch: `###-feature-name` (např. `005-pubmed-agent`)
- ✅ Adresář: `specs/###-feature-name/`
- ✅ Soubor: `specs/###-feature-name/spec.md` (ze šablony)

### 2. SpecKit Workflow s Claude Code

V Claude Code jsou k dispozici tyto příkazy (v `.github/agents/`):

#### Fáze 1: Constitution & Governance
```
/speckit.constitution
```
- Vytvoření/update Constitution projektu
- Definice nebo úprava principů (aktuálně 5 principů)
- Synchronizace se všemi templates

#### Fáze 2: Specifikace
```
/speckit.specify [feature description]
```
- Vytvoření kompletní feature specifikace
- User stories, acceptance criteria
- Funkční a non-funkční požadavky
- Reference na Constitution

#### Fáze 3: Analýza a Clarifikace
```
/speckit.analyze [spec file or topic]
```
- Analýza existující specifikace
- Identifikace mezer, rizik, dependencies
- Findings a recommendations

```
/speckit.clarify [ambiguity or question]
```
- Řešení ambiguities
- Odpovědi na questions
- Rozhodnutí trade-offs

#### Fáze 4: Plánování
```
/speckit.plan
```
- Vytvoření detailního implementačního plánu
- Constitution Check pro všech 5 principů
- Technical context (dependencies, architecture)
- Code examples a patterns
- Phase breakdown (Research → Design → Implementation → Testing)

#### Fáze 5: Task Breakdown
```
/speckit.tasks
```
- Rozpad plánu na atomické úkoly
- Estimace complexity (S/M/L/XL)
- Dependency mapping
- Prioritizace

#### Fáze 6: Implementace
```
/speckit.implement [task or component]
```
- AI-asistovaná implementace
- Test-first approach (per Constitution Principle III)
- Code quality checks (ruff, mypy)
- LangGraph patterns enforcement

#### Utility příkazy
```
/speckit.checklist [phase or milestone]
```
- Generování checklistů pro fáze
- Tracking completion

```
/speckit.taskstoissues
```
- Export tasks do GitHub Issues
- Automatické linkování s branch

## 🔧 Bash Scripty

### create-new-feature.sh

Vytvoří novou feature branch a spec:

```bash
# Basic usage
./.specify/scripts/bash/create-new-feature.sh "Feature description"

# Options
--short-name <name>    # Custom short name (2-4 words)
--number N             # Manual branch number (overrides auto)
--json                 # JSON output
--help                 # Show help

# Examples
./.specify/scripts/bash/create-new-feature.sh "Add user authentication" --short-name "user-auth"
./.specify/scripts/bash/create-new-feature.sh "OAuth2 integration" --number 5
```

**Chování:**
- Auto-detekuje nejvyšší číslo feature (z branches i specs/)
- Vytvoří branch: `###-short-name`
- Filtruje stop words (the, a, to, for, ...)
- Truncates na 244 bytů (GitHub limit)
- Podporuje non-git repozitáře (fallback mode)

### setup-plan.sh

Vytvoří implementační plán ze šablony:

```bash
./.specify/scripts/bash/setup-plan.sh

# Options
--json    # JSON output
--help    # Show help
```

**Chování:**
- Zkopíruje `plan-template.md` → `plan.md` v current feature
- Auto-detekuje feature z current branch nebo SPECIFY_FEATURE env var
- Kontroluje, že jste na feature branch (###-*)

### check-prerequisites.sh

Zkontroluje prerekvizity pro development:

```bash
./.specify/scripts/bash/check-prerequisites.sh
```

**Kontroluje:**
- Python verze (≥3.10)
- Git instalace
- Required tools (ruff, pytest, mypy)
- LangGraph CLI
- Environment variables (.env)

### update-agent-context.sh

Update context pro AI agenty:

```bash
./.specify/scripts/bash/update-agent-context.sh
```

**Aktualizuje:**
- Agent context files v `.github/agents/`
- Constitution references
- Project structure info

## 📋 Templates

### spec-template.md

Šablona pro feature specifikaci:

**Sekce:**
- **Feature Summary** - High-level popis
- **User Stories** - User stories s prioritami (P1/P2/P3)
- **Functional Requirements** - FR-### numbered requirements
- **Non-Functional Requirements** - NFR-### (performance, observability, maintainability)
- **Acceptance Criteria** - Per-story testable criteria
- **Out of Scope** - Co není součástí
- **Dependencies** - Na co závisí
- **Risks & Mitigations** - Identifikovaná rizika

### plan-template.md

Šablona pro implementační plán:

**Sekce:**
- **Summary** - Technical approach summary
- **Technical Context** - Dependencies, storage, testing, constraints
- **Constitution Check** - Validace všech 5 principů
- **Project Structure** - Dokumentace a source code struktura
- **Implementation Phases**
  - Phase 0: Research & Understanding
  - Phase 1: Data Model & Schema Design
  - Phase 2: Implementation
  - Phase 3: Testing & Validation
- **Testing Strategy** - Unit, integration, edge cases
- **Complexity Tracking** - Known complexity hotspots

### tasks-template.md

Šablona pro task breakdown:

**Sekce:**
- **Task Summary** - Breakdown overview
- **Tasks** - Numbered tasks s:
  - Description
  - Complexity (S/M/L/XL)
  - Dependencies
  - Acceptance Criteria
- **Estimation** - Total effort estimate
- **Critical Path** - Blocking dependencies

## 🎯 Constitution Enforcement

SpecKit enforces Constitution principy v každé fázi:

### I. Graph-Centric Architecture
- **Plan template**: Constitution Check sekce ověřuje graph design
- **Tasks**: Každý task must fit into graph node/edge model
- **Implement**: Code musí extend graph v `src/agent/graph.py`

### II. Type Safety & Schema Validation
- **Plan**: Vyžaduje definici State a Context TypedDicts
- **Implement**: mypy --strict checks before merge
- **Tasks**: Separate tasks pro type annotations

### III. Test-First Development
- **Plan**: Testing Strategy sekce required
- **Tasks**: Test tasks PŘED implementation tasks
- **Implement**: Tests must exist and fail before implementation

### IV. Observability & Debugging
- **Plan**: LangSmith setup v Technical Context
- **Implement**: Logging requirements enforced
- **Tasks**: Observability tasks included

### V. Modular & Extensible Design
- **Plan**: Single-responsibility node design
- **Implement**: Reusable logic extraction
- **Tasks**: Modularity separation

## 🔄 Workflow Example

### Kompletní feature development cycle:

```bash
# 1. Vytvoření feature
./.specify/scripts/bash/create-new-feature.sh "Add PubMed search integration"
# → Branch: 005-pubmed-search
# → Spec: specs/005-pubmed-search/spec.md

# 2. V Claude Code - Specifikace
/speckit.specify
# → Vyplní spec.md s user stories, requirements, criteria

# 3. V Claude Code - Analýza
/speckit.analyze specs/005-pubmed-search/spec.md
# → Vytvoří ANALYSIS.md s findings

# 4. V Claude Code - Clarifikace (pokud potřeba)
/speckit.clarify "Should we use BioMCP or direct PubMed API?"
# → Zapisuje rozhodnutí do spec.md

# 5. Setup plánu
./.specify/scripts/bash/setup-plan.sh
# → Vytvoří plan.md ze šablony

# 6. V Claude Code - Plánování
/speckit.plan
# → Vyplní plan.md s Constitution Check, phases, code examples

# 7. V Claude Code - Task breakdown
/speckit.tasks
# → Vytvoří tasks.md s atomic tasks

# 8. V Claude Code - Implementace (per task)
/speckit.implement "Implement PubMed search node"
# → Test-first implementation

# 9. Export do GitHub Issues (optional)
/speckit.taskstoissues
# → Vytvoří issues pro každý task

# 10. Merge & Close
git add .
git commit -m "feat: Add PubMed search integration"
git push origin 005-pubmed-search
# → Create PR on GitHub
```

## 🛠️ Konfigurace

### Environment Variables

```bash
# V projektu nebo shell rc file:
export SPECIFY_FEATURE="005-feature-name"  # Override auto-detection
```

### Git Hooks (TBD)

Můžete nastavit git hooks pro enforcement:

```bash
# .git/hooks/pre-commit
#!/bin/bash
# Kontrola, že jste na feature branch
# Validace spec.md existence
# Kontrola Constitution compliance
```

## 📚 Best Practices

### 1. Feature Branch Naming
- ✅ `005-pubmed-agent`
- ✅ `010-oauth-integration`
- ❌ `feature/auth` (chybí číslo)
- ❌ `05-auth` (číslo musí být 3 cifry: 005)

### 2. Spec Writing
- Začněte s user stories (co uživatel potřebuje)
- Definujte acceptance criteria (jak poznáte, že je hotovo)
- Reference Constitution principy
- Buďte konkrétní - vyhněte se vague language

### 3. Planning
- Vždy proveďte Constitution Check PŘED implementací
- Použijte code examples pro clarity
- Rozdělte na fáze (Research → Design → Implement → Test)
- Track complexity upfront

### 4. Task Breakdown
- Atomické tasks (1-4 hodiny práce)
- Clear acceptance criteria per task
- Explicit dependencies
- Prioritizace podle critical path

### 5. Implementation
- Test-first VŽDY (Principle III)
- Commit často s conventional commits
- Reference task/issue numbers v commit messages
- Update tasks.md průběžně

## 🐛 Troubleshooting

### "Not on a feature branch"
```bash
# Vytvořte novou feature branch:
./.specify/scripts/bash/create-new-feature.sh "Your feature"
# Nebo checkout existující:
git checkout 005-existing-feature
```

### "Template not found"
```bash
# Templates jsou v .specify/templates/
ls .specify/templates/
# Zkontrolujte, že soubory existují
```

### "Git repository not detected"
```bash
# SpecKit funguje i bez git, ale s omezenými features
# Pro plnou funkcionalitu:
git init
git add .
git commit -m "Initial commit"
```

### SpecKit příkazy nefungují v Claude Code
```bash
# Příkazy jsou v .github/agents/ jako agent files
# Claude Code je automaticky detekuje
# Zkontrolujte:
ls .github/agents/speckit.*.agent.md
ls .github/prompts/speckit.*.prompt.md
```

## 🔗 Related Files

- **Constitution**: `.specify/memory/constitution.md`
- **CLAUDE.md**: Root-level guide pro Claude Code instances
- **Roadmap**: `specs/ROADMAP.md` (12 features, 4 phases)
- **Feature Specs**: `specs/###-feature-name/`

## 📖 Další Zdroje

- **LangGraph Docs**: https://langchain-ai.github.io/langgraph/
- **SpecKit Issues**: `.github/ISSUE_TEMPLATE/` (TBD)
- **Constitution Docs**: `.specify/memory/constitution.md`

## 🤝 Contributing

Pro přidání nového SpecKit příkazu:

1. Vytvořte agent file: `.github/agents/speckit.newcommand.agent.md`
2. Vytvořte prompt: `.github/prompts/speckit.newcommand.prompt.md`
3. Update tento README
4. Test workflow end-to-end

---

**Version**: 1.0.0
**Last Updated**: 2026-01-13
**Maintainer**: Czech MedAI Team
