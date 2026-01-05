# Task Completion Guidelines

Before submitting or finishing a task, ensure the following steps are taken:

1. **Formatting**: Run `make format` to ensure code style consistency.
2. **Linting**: Run `make lint` to check for errors and type consistency.
3. **Testing**:
    - Run unit tests: `make test`
    - Run integration tests: `make integration_tests` (if applicable).
4. **Documentation**: Ensure any new functions or classes have Google-style docstrings and type hints.
5. **Environment**: If new environment variables are introduced, update `.env.example`.
