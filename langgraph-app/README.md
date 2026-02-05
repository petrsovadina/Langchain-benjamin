# New LangGraph Project

[![CI](https://github.com/langchain-ai/new-langgraph-project/actions/workflows/unit-tests.yml/badge.svg)](https://github.com/langchain-ai/new-langgraph-project/actions/workflows/unit-tests.yml)
[![Integration Tests](https://github.com/langchain-ai/new-langgraph-project/actions/workflows/integration-tests.yml/badge.svg)](https://github.com/langchain-ai/new-langgraph-project/actions/workflows/integration-tests.yml)

This template demonstrates a simple application implemented using [LangGraph](https://github.com/langchain-ai/langgraph), designed for showing how to get started with [LangGraph Server](https://langchain-ai.github.io/langgraph/concepts/langgraph_server/#langgraph-server) and using [LangGraph Studio](https://langchain-ai.github.io/langgraph/concepts/langgraph_studio/), a visual debugging IDE.

<div align="center">
  <img src="./static/studio_ui.png" alt="Graph view in LangGraph studio UI" width="75%" />
</div>

The core logic defined in `src/agent/graph.py`, showcases an single-step application that responds with a fixed string and the configuration provided.

You can extend this graph to orchestrate more complex agentic workflows that can be visualized and debugged in LangGraph Studio.

## Getting Started

1. Install dependencies, along with the [LangGraph CLI](https://langchain-ai.github.io/langgraph/concepts/langgraph_cli/), which will be used to run the server.

```bash
cd path/to/your/app
pip install -e . "langgraph-cli[inmem]"
```

2. (Optional) Customize the code and project as needed. Create a `.env` file if you need to use secrets.

```bash
cp .env.example .env
```

If you want to enable LangSmith tracing, add your LangSmith API key to the `.env` file.

```text
# .env
LANGSMITH_API_KEY=lsv2...
```

3. Start the LangGraph Server.

```shell
langgraph dev
```

For more information on getting started with LangGraph Server, [see here](https://langchain-ai.github.io/langgraph/tutorials/langgraph-platform/local-server/).

## How to customize

1. **Define runtime context**: Modify the `Context` class in the `graph.py` file to expose the arguments you want to configure per assistant. For example, in a chatbot application you may want to define a dynamic system prompt or LLM to use. For more information on runtime context in LangGraph, [see here](https://langchain-ai.github.io/langgraph/agents/context/?h=context#static-runtime-context).

2. **Extend the graph**: The core logic of the application is defined in [graph.py](./src/agent/graph.py). You can modify this file to add new nodes, edges, or change the flow of information.

## Development

While iterating on your graph in LangGraph Studio, you can edit past state and rerun your app from previous states to debug specific nodes. Local changes will be automatically applied via hot reload.

Follow-up requests extend the same thread. You can create an entirely new thread, clearing previous history, using the `+` button in the top right.

For more advanced features and examples, refer to the [LangGraph documentation](https://langchain-ai.github.io/langgraph/). These resources can help you adapt this template for your specific use case and build more sophisticated conversational agents.

LangGraph Studio also integrates with [LangSmith](https://smith.langchain.com/) for more in-depth tracing and collaboration with teammates, allowing you to analyze and optimize your chatbot's performance.

## Guidelines Storage

Czech MedAI používá pgvector pro ukládání a vyhledávání klinických guidelines.

### Setup

1. **Spustit migration**:
   ```bash
   psql -d your_database -f migrations/003_guidelines_schema.sql
   ```

2. **Nastavit environment variables**:
   ```bash
   # Option 1: Standard PostgreSQL
   export DATABASE_URL="postgresql://user:pass@localhost:5432/dbname"

   # Option 2: Supabase
   export SUPABASE_URL="https://your-project.supabase.co"
   export SUPABASE_KEY="your-service-role-key"
   ```

3. **Použití**:
   ```python
   from agent.utils.guidelines_storage import store_guideline, search_guidelines
   from agent.models.guideline_models import GuidelineSection, GuidelineSource

   # Store guideline
   section = GuidelineSection(
       guideline_id="CLS-JEP-2024-001",
       title="Hypertenze",
       section_name="Farmakologická léčba",
       content="ACE inhibitory jsou...",
       publication_date="2024-01-15",
       source=GuidelineSource.CLS_JEP,
       url="https://www.cls.cz/guidelines/hypertenze-2024.pdf",
       metadata={"embedding": [0.1] * 1536}
   )
   await store_guideline(section)

   # Search guidelines
   results = await search_guidelines(
       query=[0.1] * 1536,  # Pre-computed embedding
       limit=5,
       source_filter="cls_jep"
   )
   ```

### Testing

```bash
# Unit tests
pytest tests/unit_tests/utils/test_guidelines_storage.py -v

# Integration tests (requires database)
pytest tests/integration_tests/test_guidelines_storage_integration.py -v
```
