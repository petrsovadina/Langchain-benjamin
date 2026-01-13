.PHONY: all format lint test tests test_watch integration_tests docker_tests help extended_tests speckit_new speckit_plan speckit_check

# Default target executed when no arguments are given to make.
all: help

# Define a variable for the test file path.
TEST_FILE ?= tests/unit_tests/

test:
	python -m pytest $(TEST_FILE)

integration_tests:
	python -m pytest tests/integration_tests 

test_watch:
	python -m ptw --snapshot-update --now . -- -vv tests/unit_tests

test_profile:
	python -m pytest -vv tests/unit_tests/ --profile-svg

extended_tests:
	python -m pytest --only-extended $(TEST_FILE)


######################
# LINTING AND FORMATTING
######################

# Define a variable for Python and notebook files.
PYTHON_FILES=src/
MYPY_CACHE=.mypy_cache
lint format: PYTHON_FILES=.
lint_diff format_diff: PYTHON_FILES=$(shell git diff --name-only --diff-filter=d main | grep -E '\.py$$|\.ipynb$$')
lint_package: PYTHON_FILES=src
lint_tests: PYTHON_FILES=tests
lint_tests: MYPY_CACHE=.mypy_cache_test

lint lint_diff lint_package lint_tests:
	python -m ruff check .
	[ "$(PYTHON_FILES)" = "" ] || python -m ruff format $(PYTHON_FILES) --diff
	[ "$(PYTHON_FILES)" = "" ] || python -m ruff check --select I $(PYTHON_FILES)
	[ "$(PYTHON_FILES)" = "" ] || python -m mypy --strict $(PYTHON_FILES)
	[ "$(PYTHON_FILES)" = "" ] || mkdir -p $(MYPY_CACHE) && python -m mypy --strict $(PYTHON_FILES) --cache-dir $(MYPY_CACHE)

format format_diff:
	ruff format $(PYTHON_FILES)
	ruff check --select I --fix $(PYTHON_FILES)

spell_check:
	codespell --toml pyproject.toml

spell_fix:
	codespell --toml pyproject.toml -w

######################
# SPECKIT WORKFLOW
######################

# Create new feature branch and spec
speckit_new:
	@if [ -z "$(FEATURE)" ]; then \
		echo "Usage: make speckit_new FEATURE='Your feature description'"; \
		echo "Options:"; \
		echo "  NAME='short-name'  - Custom short name (optional)"; \
		echo "  NUM=5              - Specific feature number (optional)"; \
		exit 1; \
	fi
	@ARGS="$(FEATURE)"; \
	[ -n "$(NAME)" ] && ARGS="$$ARGS --short-name $(NAME)"; \
	[ -n "$(NUM)" ] && ARGS="$$ARGS --number $(NUM)"; \
	../.specify/scripts/bash/create-new-feature.sh $$ARGS

# Setup implementation plan
speckit_plan:
	@../.specify/scripts/bash/setup-plan.sh

# Check prerequisites for development
speckit_check:
	@../.specify/scripts/bash/check-prerequisites.sh

# Update agent context
speckit_update:
	@../.specify/scripts/bash/update-agent-context.sh

# Show SpecKit help
speckit_help:
	@echo '======================================'
	@echo 'SpecKit - Feature Development Workflow'
	@echo '======================================'
	@echo ''
	@echo 'Create new feature:'
	@echo '  make speckit_new FEATURE="Your feature description"'
	@echo '  make speckit_new FEATURE="OAuth integration" NAME="oauth"'
	@echo '  make speckit_new FEATURE="User auth" NUM=10'
	@echo ''
	@echo 'Setup implementation plan:'
	@echo '  make speckit_plan'
	@echo ''
	@echo 'Check prerequisites:'
	@echo '  make speckit_check'
	@echo ''
	@echo 'Update agent context:'
	@echo '  make speckit_update'
	@echo ''
	@echo 'Full workflow:'
	@echo '  1. make speckit_new FEATURE="..."'
	@echo '  2. Claude Code: /speckit.specify'
	@echo '  3. Claude Code: /speckit.analyze'
	@echo '  4. make speckit_plan'
	@echo '  5. Claude Code: /speckit.plan'
	@echo '  6. Claude Code: /speckit.tasks'
	@echo '  7. Claude Code: /speckit.implement'
	@echo ''
	@echo 'Documentation:'
	@echo '  ../.specify/README.md'
	@echo '  ../.specify/memory/constitution.md'
	@echo ''

######################
# HELP
######################

help:
	@echo '===================================='
	@echo 'Czech MedAI (Benjamin) - Development'
	@echo '===================================='
	@echo ''
	@echo 'Code Quality:'
	@echo '  make format              - run code formatters'
	@echo '  make lint                - run linters (ruff + mypy)'
	@echo '  make spell_check         - check spelling'
	@echo ''
	@echo 'Testing:'
	@echo '  make test                - run unit tests'
	@echo '  make integration_tests   - run integration tests'
	@echo '  make test_watch          - run tests in watch mode'
	@echo '  make test TEST_FILE=path - run specific test file'
	@echo ''
	@echo 'SpecKit Workflow:'
	@echo '  make speckit_help        - show SpecKit commands'
	@echo '  make speckit_new         - create new feature'
	@echo '  make speckit_plan        - setup implementation plan'
	@echo '  make speckit_check       - check prerequisites'
	@echo ''
	@echo 'Documentation:'
	@echo '  CLAUDE.md                - Guide for Claude Code'
	@echo '  .specify/README.md       - SpecKit documentation'
	@echo '  .specify/memory/constitution.md - Project Constitution'
	@echo ''

