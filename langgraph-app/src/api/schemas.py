"""Pydantic schémata pro FastAPI endpointy.

Modely požadavků a odpovědí pro Czech MedAI API s validací.
"""

import re
from typing import Dict, List, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ConsultRequest(BaseModel):
    """Schéma požadavku pro /api/v1/consult endpoint.

    Atributy:
        query: Uživatelský lékařský dotaz v češtině.
        mode: Režim zpracování ("quick" nebo "deep").
        user_id: Volitelný identifikátor uživatele pro sledování relace.
    """

    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Lékařský dotaz uživatele (česky)",
        examples=["Jaké jsou kontraindikace metforminu?"],
    )
    mode: Literal["quick", "deep"] = Field(
        default="quick",
        description="Režim zpracování: quick (5s) nebo deep (detailní výzkum)",
        examples=["quick"],
    )
    user_id: str | None = Field(
        default=None,
        description="Volitelný identifikátor uživatele",
        examples=["user_12345"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "query": "Jaké jsou kontraindikace metforminu?",
                    "mode": "quick",
                },
                {
                    "query": "Doporučení pro léčbu hypertenze u diabetika 2. typu",
                    "mode": "deep",
                    "user_id": "user_12345",
                },
            ]
        }
    )

    @field_validator("query")
    @classmethod
    def sanitize_query(cls, v: str) -> str:
        """Sanitize query input.

        - Remove leading/trailing whitespace
        - Remove control characters
        - Remove excessive whitespace
        - Block SQL injection patterns
        - Block XSS patterns
        """
        # Remove control characters
        v = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', v)

        # Remove excessive whitespace
        v = re.sub(r'\s+', ' ', v)

        # Strip
        v = v.strip()

        # Ensure not empty
        if not v:
            raise ValueError("Query cannot be empty or whitespace")

        # Block SQL injection patterns (basic)
        sql_patterns = [
            r"(\bUNION\b.*\bSELECT\b)",
            r"(\bDROP\b.*\bTABLE\b)",
            r"(\bINSERT\b.*\bINTO\b)",
            r"(\bDELETE\b.*\bFROM\b)",
        ]
        for pattern in sql_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError("Invalid query: potential SQL injection")

        # Block XSS patterns (basic)
        xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
        ]
        for pattern in xss_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError("Invalid query: potential XSS")

        return v


class DocumentMetadata(BaseModel):
    """Metadata získaného dokumentu (citační zdroj).

    Atributy:
        source: Typ zdroje (sukl, PubMed, cls_jep).
        source_type: Podtyp zdroje (drug_search, article, guideline).
        Další pole se liší podle zdroje (pmid, registration_number, atd.).
    """

    source: str = Field(
        ...,
        description="Typ zdroje",
        examples=["sukl"],
    )
    source_type: str | None = Field(
        None,
        description="Podtyp zdroje",
        examples=["drug_search"],
    )
    # Dynamická pole (pmid, registration_number, url, atd.)
    # Uloženo jako extra pole přes model_config

    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "examples": [
                {
                    "source": "sukl",
                    "source_type": "drug_search",
                    "registration_number": "0012345",
                    "url": "https://www.sukl.cz/modules/medication/detail.php?kod=0012345",
                },
                {
                    "source": "PubMed",
                    "source_type": "article",
                    "pmid": "39876543",
                    "doi": "10.1001/jama.2025.12345",
                },
            ]
        },
    )


class RetrievedDocument(BaseModel):
    """Získaný dokument s obsahem a metadaty pro citace.

    Atributy:
        page_content: Formátovaný obsah dokumentu.
        metadata: Metadata zdroje pro vykreslení citace.
    """

    page_content: str = Field(
        ...,
        description="Obsah dokumentu",
        examples=["Metformin Teva 500mg - Reg. č.: 0012345, ATC: A10BA02"],
    )
    metadata: DocumentMetadata = Field(..., description="Citační metadata")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "page_content": "Metformin Teva 500mg - kontraindikace: renální insuficience (eGFR <30 ml/min)",
                    "metadata": {
                        "source": "sukl",
                        "source_type": "drug_details",
                        "registration_number": "0012345",
                    },
                }
            ]
        }
    )


class ConsultResponse(BaseModel):
    """Schéma finální odpovědi v SSE streamu (event type: final).

    Toto schéma popisuje strukturu dat v SSE eventu ``final``.
    Endpoint ``/api/v1/consult`` vrací ``StreamingResponse``, nikoli JSON.

    Atributy:
        answer: AI-generovaná odpověď v češtině s inline citacemi.
        retrieved_docs: Seznam zdrojových dokumentů pro vykreslení citací.
        confidence: Skóre důvěryhodnosti 0.0-1.0 (volitelné).
        latency_ms: Latence odpovědi v milisekundách.
    """

    answer: str = Field(
        ...,
        description="AI odpověď s inline citacemi [1][2]",
        examples=["Metformin je kontraindikován při eGFR <30 ml/min [1]. Doporučuje se pravidelné monitorování renálních funkcí [2]."],
    )
    retrieved_docs: List[RetrievedDocument] = Field(
        default_factory=list,
        description="Zdrojové dokumenty pro citace",
    )
    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Skóre důvěryhodnosti (0.0-1.0)",
        examples=[0.92],
    )
    latency_ms: int = Field(
        ...,
        ge=0,
        description="Latence odpovědi v milisekundách",
        examples=[2340],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "answer": "Metformin je kontraindikován při eGFR <30 ml/min [1]. Alternativou může být gliptin [2].",
                    "retrieved_docs": [
                        {
                            "page_content": "Metformin Teva 500mg - kontraindikace: těžká renální insuficience",
                            "metadata": {"source": "sukl", "source_type": "drug_details"},
                        }
                    ],
                    "confidence": 0.92,
                    "latency_ms": 2340,
                }
            ]
        }
    )


class HealthCheckResponse(BaseModel):
    """Schéma odpovědi pro /health endpoint.

    Atributy:
        status: Celkový stav systému ("healthy" nebo "degraded").
        mcp_servers: Stav MCP serverů (sukl, biomcp).
        database: Stav databázového připojení.
        version: Verze API.
    """

    status: Literal["healthy", "degraded"] = Field(
        ...,
        description="Celkový stav systému",
        examples=["healthy"],
    )
    mcp_servers: Dict[str, str] = Field(
        ...,
        description="Stav MCP serverů (available/unavailable)",
        examples=[{"sukl": "available", "biomcp": "available"}],
    )
    database: str | None = Field(
        default=None,
        description="Stav databáze",
        examples=["available"],
    )
    version: str = Field(
        default="0.1.0",
        description="Verze API",
        examples=["0.1.0"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "status": "healthy",
                    "mcp_servers": {"sukl": "available", "biomcp": "available"},
                    "database": "available",
                    "version": "0.1.0",
                },
                {
                    "status": "degraded",
                    "mcp_servers": {"sukl": "available", "biomcp": "unavailable"},
                    "database": "error: connection refused",
                    "version": "0.1.0",
                },
            ]
        }
    )


class ErrorResponse(BaseModel):
    """Standardní chybová odpověď.

    Používá se pro všechny error status kódy (400, 429, 500, 504).

    Atributy:
        error: Typ chyby (machine-readable).
        detail: Lidsky čitelný popis chyby.
    """

    error: str = Field(
        ...,
        description="Typ chyby (validation_error, rate_limit_exceeded, timeout, internal_error)",
        examples=["validation_error"],
    )
    detail: str = Field(
        ...,
        description="Detailní popis chyby pro uživatele",
        examples=["Query too long (max 1000 characters)"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "error": "validation_error",
                    "detail": "Query too long (max 1000 characters)",
                },
                {
                    "error": "rate_limit_exceeded",
                    "detail": "Rate limit 10/minute exceeded. Zkuste to znovu za chvíli.",
                },
                {
                    "error": "timeout",
                    "detail": "Request timed out after 30 seconds",
                },
                {
                    "error": "internal_error",
                    "detail": "An unexpected error occurred",
                },
            ]
        }
    )


class RootResponse(BaseModel):
    """Schéma odpovědi pro root endpoint (/).

    Atributy:
        name: Název API.
        version: Verze API.
        description: Krátký popis.
        docs: URL na Swagger dokumentaci.
        health: URL na health check endpoint.
    """

    name: str = Field(
        ...,
        description="Název API",
        examples=["Czech MedAI API"],
    )
    version: str = Field(
        ...,
        description="Verze API",
        examples=["0.1.0"],
    )
    description: str = Field(
        ...,
        description="Krátký popis API",
        examples=["AI asistent pro české lékaře"],
    )
    docs: str = Field(
        ...,
        description="URL na Swagger dokumentaci",
        examples=["/docs"],
    )
    health: str = Field(
        ...,
        description="URL na health check",
        examples=["/health"],
    )
