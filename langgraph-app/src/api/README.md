# Czech MedAI FastAPI Backend

Production-ready API server pro Czech MedAI multi-agent systém.

## Quick Start

### 1. Instalace Dependencies

```bash
cd langgraph-app
pip install -e .
```

### 2. Konfigurace Environment

```bash
cp .env.example .env
# Upravit .env s API keys (LANGSMITH_API_KEY, OPENAI_API_KEY)
```

### 3. Spuštění Serveru

**Development mode** (auto-reload):
```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**Production mode**:
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 4. Testování

**Health check**:
```bash
curl http://localhost:8000/health
```

**OpenAPI docs**:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Endpoints

### GET /health

Health check endpoint pro monitoring.

**Response**:
```json
{
  "status": "healthy",
  "mcp_servers": {
    "sukl": "available",
    "biomcp": "available"
  },
  "database": null,
  "version": "0.1.0"
}
```

### POST /api/v1/consult (Coming in Phase 2)

Medical consultation endpoint s LangGraph integration.

## Development

### Spuštění Testů

```bash
# Unit + integration testy
make test

# Pouze API integration testy
pytest tests/integration_tests/test_api_server.py -v
```

### Linting

```bash
make lint
make format
```

## Architecture

```
FastAPI Server
    ↓
CORS Middleware
    ↓
Request Timing Middleware
    ↓
Routes (/health, /api/v1/consult)
    ↓
LangGraph Execution
    ↓
Response (JSON)
```

## Configuration

Environment variables (`.env`):

- `API_HOST` - Server host (default: 0.0.0.0)
- `API_PORT` - Server port (default: 8000)
- `API_RELOAD` - Auto-reload (development only)
- `CORS_ORIGINS` - Allowed origins (comma-separated)

## Next Steps

- **Phase 2**: `/api/v1/consult` endpoint s LangGraph integration
- **Phase 2**: SSE streaming pro real-time responses
- **Phase 3**: Redis caching, rate limiting, Docker deployment
