# Project Overview: LangGraph App

## Purpose
This project is a starter template for building AI agents using **LangGraph**. It is designed to work seamlessly with **LangGraph Server** and **LangGraph Studio** for visual debugging and development.

## Tech Stack
- **Language**: Python >= 3.10
- **Framework**: [LangGraph](https://github.com/langchain-ai/langgraph)
- **Environment Management**: `python-dotenv`
- **Linting/Formatting**: `ruff`, `mypy`
- **Testing**: `pytest`
- **Build System**: `setuptools`

## Core Structure
- `src/agent/graph.py`: Contains the core logic and graph definition.
- `langgraph.json`: Configuration for the LangGraph CLI and server.
- `pyproject.toml`: Dependency management and tool configurations.
- `Makefile`: Shortcuts for common development tasks.
- `tests/`: Contains unit and integration tests.
