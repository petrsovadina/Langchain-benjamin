# Suggested Commands

## Development
- **Start Local Server**: `langgraph dev` (Starts the LangGraph development server with hot-reload).
- **Install Dependencies**: `pip install -e .`

## Testing
- **Run Unit Tests**: `make test` or `python -m pytest tests/unit_tests/`
- **Run Integration Tests**: `make integration_tests`
- **Watch Tests**: `make test_watch`

## Linting and Formatting
- **Lint Code**: `make lint` (Runs ruff check, ruff format diff, and mypy strict).
- **Format Code**: `make format` (Runs ruff format and ruff check --fix).
- **Type Checking**: `python -m mypy --strict src/`

## Utilities
- **Spell Check**: `make spell_check`
- **Clean**: (No explicit clean command in Makefile, but standard `rm -rf .mypy_cache .pytest_cache` applies).
