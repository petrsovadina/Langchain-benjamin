# Czech MedAI - API Reference

**Version**: 0.1.0 | **Base URL**: `http://localhost:8000`

## Authentication

Currently no authentication required. Rate limiting is enforced per IP address.

## Endpoints

### `GET /`

Root endpoint with API metadata and navigation links.

**Response** `200 OK` — `application/json`

```json
{
  "name": "Czech MedAI API",
  "version": "0.1.0",
  "description": "AI asistent pro české lékaře",
  "docs": "/docs",
  "health": "/health"
}
```

---

### `GET /health`

Health check endpoint. Verifies API server, MCP servers, and database connectivity.

**Response** `200 OK` — `application/json`

```json
{
  "status": "healthy",
  "mcp_servers": {
    "sukl": "available",
    "biomcp": "available"
  },
  "database": "available",
  "version": "0.1.0"
}
```

**Degraded Example:**

```json
{
  "status": "degraded",
  "mcp_servers": {
    "sukl": "available",
    "biomcp": "unavailable"
  },
  "database": "error: connection refused",
  "version": "0.1.0"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `status` | `"healthy" \| "degraded"` | Overall system status |
| `mcp_servers` | `object` | Per-server status (`available` / `unavailable` / `error: ...`) |
| `database` | `string \| null` | PostgreSQL + pgvector status |
| `version` | `string` | API version |

---

### `POST /api/v1/consult`

Primary consultation endpoint. Sends a medical query through the multi-agent
system and returns results as a Server-Sent Events (SSE) stream.

**Rate Limit**: 10 requests/minute per IP address.

**Timeout**: 30 seconds maximum execution time.

#### Request Body

`Content-Type: application/json`

```json
{
  "query": "Jaké jsou kontraindikace metforminu?",
  "mode": "quick",
  "user_id": "user_12345"
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `query` | `string` | Yes | — | Medical query in Czech (1–1000 chars) |
| `mode` | `"quick" \| "deep"` | No | `"quick"` | `quick` = cached ~5s, `deep` = thorough research |
| `user_id` | `string \| null` | No | `null` | Optional user ID for session tracking |

**Input Validation:**

- Control characters are stripped
- Excessive whitespace is collapsed
- SQL injection patterns are blocked (`UNION SELECT`, `DROP TABLE`, etc.)
- XSS patterns are blocked (`<script>`, `javascript:`, `onclick=`)

#### Response — SSE Stream

`Content-Type: text/event-stream`

The response is a Server-Sent Events stream. Each event follows the format:

```
event: message|done|error
data: <JSON payload>

```

#### SSE Event Types

##### `agent_start`

Emitted when an agent begins processing.

```
event: message
data: {"type": "agent_start", "agent": "drug_agent"}
```

| Field | Type | Values |
|-------|------|--------|
| `type` | `string` | `"agent_start"` |
| `agent` | `string` | `"drug_agent"`, `"pubmed_agent"`, `"guidelines_agent"`, `"general_agent"`, `"supervisor"`, `"synthesizer"` |

##### `agent_complete`

Emitted when an agent finishes processing.

```
event: message
data: {"type": "agent_complete", "agent": "drug_agent"}
```

| Field | Type | Values |
|-------|------|--------|
| `type` | `string` | `"agent_complete"` |
| `agent` | `string` | `"drug_agent"`, `"pubmed_agent"`, `"guidelines_agent"`, `"general_agent"` |

##### `cache_hit`

Emitted when a cached response is found (quick mode only).

```
event: message
data: {"type": "cache_hit"}
```

When a cache hit occurs, the stream sends: `cache_hit` → `final` → `done`.

##### `final`

The final answer with inline citations and source documents.

```
event: message
data: {
  "type": "final",
  "answer": "Metformin je kontraindikován při eGFR <30 ml/min [1]. Alternativou může být gliptin [2].",
  "retrieved_docs": [
    {
      "page_content": "Metformin Teva 500mg - kontraindikace: těžká renální insuficience",
      "metadata": {
        "source": "sukl",
        "source_type": "drug_details",
        "registration_number": "0012345"
      }
    }
  ],
  "confidence": 0.92,
  "latency_ms": 2340
}
```

| Field | Type | Description |
|-------|------|-------------|
| `type` | `string` | `"final"` |
| `answer` | `string` | AI-generated answer in Czech with `[N]` inline citations |
| `retrieved_docs` | `array` | Source documents for citation rendering |
| `confidence` | `float \| null` | Confidence score 0.0–1.0 (reserved for future use) |
| `latency_ms` | `integer` | Response latency in milliseconds |

**`retrieved_docs[].metadata` fields by source:**

| Source | Fields |
|--------|--------|
| `sukl` | `source_type`, `registration_number`, `url`, `atc_code` |
| `PubMed` | `source_type`, `pmid`, `doi`, `url`, `abstract_en` |
| `cls_jep` | `source_type`, `guideline_name`, `url` |

##### `done`

Signals the end of the SSE stream.

```
event: done
data: {}
```

##### `error`

Error during processing.

```
event: error
data: {"type": "error", "error": "timeout", "detail": "Request timed out after 30 seconds"}
```

| Field | Type | Description |
|-------|------|-------------|
| `type` | `string` | `"error"` |
| `error` | `string` | Error type: `timeout`, `internal_error`, `validation_error`, `rate_limit_exceeded` |
| `detail` | `string` | Human-readable error description |

#### Error Responses

| Status | Error Type | Description |
|--------|-----------|-------------|
| `400` | `validation_error` | Invalid query (empty, too long, SQL injection, XSS) |
| `429` | `rate_limit_exceeded` | Exceeded 10 req/min limit |
| `500` | `internal_error` | Unexpected server error |
| `504` | `timeout` | Processing exceeded 30 seconds |

Error response body:

```json
{
  "error": "rate_limit_exceeded",
  "detail": "Rate limit 10/minute exceeded. Zkuste to znovu za chvíli."
}
```

#### Complete SSE Stream Example

**Normal flow:**

```
event: message
data: {"type": "agent_start", "agent": "supervisor"}

event: message
data: {"type": "agent_start", "agent": "drug_agent"}

event: message
data: {"type": "agent_complete", "agent": "drug_agent"}

event: message
data: {"type": "final", "answer": "Metformin je...[1]", "retrieved_docs": [...], "confidence": 0.92, "latency_ms": 2340}

event: done
data: {}
```

**Cache hit flow (quick mode):**

```
event: message
data: {"type": "cache_hit"}

event: message
data: {"type": "final", "answer": "...", "retrieved_docs": [...], "confidence": 0.92, "latency_ms": 150}

event: done
data: {}
```

---

## Response Headers

All responses include these headers:

| Header | Description | Example |
|--------|-------------|---------|
| `X-Request-ID` | Unique request identifier (UUID v4) | `f47ac10b-58cc-4372-a567-0e02b2c3d479` |
| `X-Process-Time` | Processing time in milliseconds | `2340.00ms` |
| `X-Content-Type-Options` | Prevents MIME sniffing | `nosniff` |
| `X-Frame-Options` | Prevents clickjacking | `DENY` |
| `X-XSS-Protection` | XSS filter | `1; mode=block` |
| `Referrer-Policy` | Referrer policy | `strict-origin-when-cross-origin` |
| `Strict-Transport-Security` | HSTS (HTTPS only) | `max-age=31536000; includeSubDomains` |
| `Content-Security-Policy` | CSP rules | (varies by endpoint) |

SSE responses additionally include:

| Header | Description | Example |
|--------|-------------|---------|
| `Cache-Control` | Disables caching | `no-cache` |
| `Connection` | Persistent connection | `keep-alive` |
| `X-Accel-Buffering` | Disables nginx buffering | `no` |
| `X-Cache` | Cache status | `HIT` or `MISS` |

---

## Code Examples

### Python (requests + sseclient)

```python
import json
import requests
import sseclient

url = "http://localhost:8000/api/v1/consult"
payload = {
    "query": "Jaké jsou kontraindikace metforminu?",
    "mode": "quick"
}

response = requests.post(url, json=payload, stream=True)
client = sseclient.SSEClient(response)

for event in client.events():
    data = json.loads(event.data)

    if data.get("type") == "agent_start":
        print(f"Agent started: {data['agent']}")
    elif data.get("type") == "final":
        print(f"Answer: {data['answer']}")
        print(f"Sources: {len(data['retrieved_docs'])} documents")
        print(f"Latency: {data['latency_ms']}ms")
    elif event.event == "done":
        break
```

### TypeScript (EventSource)

```typescript
const response = await fetch("http://localhost:8000/api/v1/consult", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    query: "Jaké jsou kontraindikace metforminu?",
    mode: "quick",
  }),
});

const reader = response.body!.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;

  const text = decoder.decode(value);
  const lines = text.split("\n");

  for (const line of lines) {
    if (line.startsWith("data: ")) {
      const data = JSON.parse(line.slice(6));

      if (data.type === "agent_start") {
        console.log(`Agent started: ${data.agent}`);
      } else if (data.type === "final") {
        console.log(`Answer: ${data.answer}`);
      }
    }
  }
}
```

### cURL

```bash
curl -X POST http://localhost:8000/api/v1/consult \
  -H "Content-Type: application/json" \
  -d '{"query": "Jaké jsou kontraindikace metforminu?", "mode": "quick"}' \
  --no-buffer
```

---

## Interactive Documentation

FastAPI provides built-in interactive documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

---

## CORS Configuration

| Setting | Value |
|---------|-------|
| Allowed Origins | Configurable via `CORS_ORIGINS` env var (default: `*`) |
| Allowed Methods | `GET`, `POST`, `OPTIONS` |
| Allowed Headers | `Content-Type`, `Authorization`, `X-Request-ID` |
| Allow Credentials | Configurable (default: `true`) |
| Max Age | 3600s (1 hour preflight cache) |
