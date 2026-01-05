# Style and Conventions

## Python Style
- **Linter/Formatter**: `ruff` is used for both linting and formatting.
- **Type Hints**: Strict type checking with `mypy` is enforced.
- **Docstrings**: Follows the **Google** convention for docstrings.
- **Imports**: Sorted using `ruff` (isort-like functionality).

## Configuration
- **Environment Variables**: Managed via `.env` file (template in `.env.example`).
- **Graph Definition**: Defined in `src/agent/graph.py` and referenced in `langgraph.json`.

## Naming Conventions
- Standard Python naming (snake_case for functions/variables, PascalCase for classes).
- The main graph object is typically named `graph`.
