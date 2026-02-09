"""Pydantic schémata pro FastAPI endpointy.

Modely požadavků a odpovědí pro Czech MedAI API s validací.
"""

import re
from typing import Dict, List, Literal

from pydantic import BaseModel, Field, field_validator


class ConsultRequest(BaseModel):
    """Schéma požadavku pro /api/v1/consult endpoint.

    Atributy:
        query: Uživatelský lékařský dotaz v češtině.
        mode: Režim zpracování ("quick" nebo "deep").
        user_id: Volitelný identifikátor uživatele pro sledování relace.

    Příklad:
        >>> request = ConsultRequest(
        ...     query="Jaké jsou kontraindikace metforminu?",
        ...     mode="quick"
        ... )
    """

    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Lékařský dotaz uživatele (česky)",
    )
    mode: Literal["quick", "deep"] = Field(
        default="quick",
        description="Režim zpracování: quick (5s) nebo deep (detailní výzkum)",
    )
    user_id: str | None = Field(
        default=None,
        description="Volitelný identifikátor uživatele",
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

    source: str = Field(..., description="Typ zdroje")
    source_type: str | None = Field(None, description="Podtyp zdroje")
    # Dynamická pole (pmid, registration_number, url, atd.)
    # Uloženo jako extra pole přes model_config

    model_config = {"extra": "allow"}  # Povolit další pole


class RetrievedDocument(BaseModel):
    """Získaný dokument s obsahem a metadaty pro citace.

    Atributy:
        page_content: Formátovaný obsah dokumentu.
        metadata: Metadata zdroje pro vykreslení citace.

    Příklad:
        >>> doc = RetrievedDocument(
        ...     page_content="Metformin Teva 500mg - Reg. č.: 0012345",
        ...     metadata={
        ...         "source": "sukl",
        ...         "registration_number": "0012345",
        ...         "url": "https://www.sukl.cz/..."
        ...     }
        ... )
    """

    page_content: str = Field(..., description="Obsah dokumentu")
    metadata: DocumentMetadata = Field(..., description="Citační metadata")


class ConsultResponse(BaseModel):
    """Schéma odpovědi pro /api/v1/consult endpoint.

    Atributy:
        answer: AI-generovaná odpověď v češtině s inline citacemi.
        retrieved_docs: Seznam zdrojových dokumentů pro vykreslení citací.
        confidence: Skóre důvěryhodnosti 0.0-1.0 (volitelné).
        latency_ms: Latence odpovědi v milisekundách.

    Příklad:
        >>> response = ConsultResponse(
        ...     answer="Metformin je kontraindikován při eGFR <30 [1].",
        ...     retrieved_docs=[...],
        ...     confidence=0.92,
        ...     latency_ms=2340
        ... )
    """

    answer: str = Field(..., description="AI odpověď s citacemi")
    retrieved_docs: List[RetrievedDocument] = Field(
        default_factory=list,
        description="Zdrojové dokumenty pro citace",
    )
    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Skóre důvěryhodnosti",
    )
    latency_ms: int = Field(..., ge=0, description="Latence odpovědi (ms)")


class HealthCheckResponse(BaseModel):
    """Schéma odpovědi pro /health endpoint.

    Atributy:
        status: Celkový stav systému ("healthy" nebo "degraded").
        mcp_servers: Stav MCP serverů (sukl, biomcp).
        database: Stav databázového připojení.
        version: Verze API.
    """

    status: Literal["healthy", "degraded"] = Field(
        ..., description="Celkový stav systému"
    )
    mcp_servers: Dict[str, str] = Field(
        ..., description="Stav MCP serverů (available/unavailable)"
    )
    database: str | None = Field(default=None, description="Stav databáze")
    version: str = Field(default="0.1.0", description="Verze API")
