"""Pydantic models for Guidelines Agent (Feature 006).

Domain models for guideline queries and responses from ČLS JEP, ESC, ERS sources.
"""

from __future__ import annotations

import re
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, computed_field, field_validator


class GuidelineQueryType(str, Enum):
    """Type of guideline query for routing logic.

    Determines how the guidelines agent processes the request:
    - SEARCH: Full-text search across guideline content
    - SECTION_LOOKUP: Direct lookup of specific guideline section by ID
    """

    SEARCH = "search"
    SECTION_LOOKUP = "section_lookup"


class GuidelineSource(str, Enum):
    """Source organization for clinical guidelines.

    Supported guideline sources:
    - CLS_JEP: České lékařské společnosti Jana Evangelisty Purkyně
    - ESC: European Society of Cardiology
    - ERS: European Respiratory Society
    """

    CLS_JEP = "cls_jep"
    ESC = "esc"
    ERS = "ers"


class GuidelineQuery(BaseModel):
    """Input query for guidelines agent node.

    Attributes:
        query_text: Search text (guideline topic, disease, procedure).
        query_type: Type of query for routing.
        specialty_filter: Optional specialty filter (cardiology, diabetes, etc.).
        limit: Maximum number of results (1-50).

    Example:
        >>> query = GuidelineQuery(
        ...     query_text="léčba hypertenze",
        ...     query_type=GuidelineQueryType.SEARCH,
        ...     specialty_filter="cardiology",
        ...     limit=10
        ... )
    """

    query_text: str = Field(..., min_length=1, description="Search query text")
    query_type: GuidelineQueryType = Field(
        default=GuidelineQueryType.SEARCH, description="Query type for routing"
    )
    specialty_filter: str | None = Field(
        default=None, description="Optional specialty filter"
    )
    limit: int = Field(default=10, ge=1, le=50, description="Max results")

    @field_validator("query_text")
    @classmethod
    def validate_query_not_empty(cls, v: str) -> str:
        """Validate query text is not empty after trimming whitespace."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("Query text cannot be empty or whitespace only")
        return stripped


class GuidelineSection(BaseModel):
    """Represents a guideline section with metadata.

    Attributes:
        guideline_id: Unique guideline identifier (e.g., "CLS-JEP-2024-001").
        title: Guideline title.
        section_name: Section name within guideline.
        content: Section text content.
        publication_date: Publication date (YYYY-MM-DD).
        source: Guideline source (cls_jep/esc/ers).
        url: URL to guideline document.
        metadata: Additional metadata dict for embeddings, chunk info, ingestion timestamp.

    Example:
        >>> section = GuidelineSection(
        ...     guideline_id="CLS-JEP-2024-001",
        ...     title="Doporučené postupy pro hypertenzi",
        ...     section_name="Léčba hypertenze 1. stupně",
        ...     content="U pacientů s hypertenzí 1. stupně...",
        ...     publication_date="2024-01-15",
        ...     source=GuidelineSource.CLS_JEP,
        ...     url="https://www.cls.cz/guidelines/hypertenze-2024.pdf"
        ... )
        >>> section.metadata["embedding"] = [0.1, 0.2, ...]
        >>> section.model_dump()["metadata"]["embedding"]
        [0.1, 0.2, ...]
    """

    guideline_id: str = Field(
        ..., min_length=1, description="Unique guideline identifier"
    )
    title: str = Field(..., min_length=1, description="Guideline title")
    section_name: str = Field(..., description="Section name")
    content: str = Field(..., min_length=1, description="Section text content")
    publication_date: str = Field(..., description="Publication date (YYYY-MM-DD)")
    source: GuidelineSource = Field(..., description="Guideline source")
    url: str = Field(..., description="URL to guideline document")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata (embeddings, chunk info, ingestion timestamp)",
    )

    @field_validator("guideline_id")
    @classmethod
    def validate_guideline_id(cls, v: str) -> str:
        """Validate guideline ID format (e.g., CLS-JEP-2024-001, ESC-2023-042).

        Accepted formats:
        - CLS-JEP-YYYY-NNN (Czech guidelines)
        - ESC-YYYY-NNN (European Society of Cardiology)
        - ERS-YYYY-NNN (European Respiratory Society)
        """
        pattern = r"^(CLS-JEP|ESC|ERS)-\d{4}-\d{3}$"
        if not re.match(pattern, v):
            raise ValueError(
                f"Invalid guideline ID format: {v}. "
                "Expected format: CLS-JEP-YYYY-NNN, ESC-YYYY-NNN, or ERS-YYYY-NNN"
            )
        return v

    @field_validator("publication_date")
    @classmethod
    def validate_publication_date(cls, v: str) -> str:
        """Validate publication date format (YYYY-MM-DD)."""
        pattern = r"^\d{4}-\d{2}-\d{2}$"
        if not re.match(pattern, v):
            raise ValueError(
                f"Invalid publication date format: {v}. Expected format: YYYY-MM-DD"
            )
        # Validate it's a real date
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError as e:
            raise ValueError(f"Invalid date: {v}. {e}") from e
        return v

    @computed_field  # type: ignore[prop-decorator]
    @property
    def guideline_url(self) -> str:
        """Generate canonical URL based on source.

        Returns:
            URL to the guideline on the source organization's website.
        """
        base_urls = {
            GuidelineSource.CLS_JEP: "https://www.cls.cz/guidelines",
            GuidelineSource.ESC: "https://www.escardio.org/Guidelines",
            GuidelineSource.ERS: "https://www.ersnet.org/guidelines",
        }
        base = base_urls.get(self.source, "https://www.cls.cz/guidelines")
        return f"{base}/{self.guideline_id}"


class GuidelineDocument(BaseModel):
    r"""Transformed guideline data as Document-compatible format.

    Used for conversion to langchain_core.documents.Document.

    Attributes:
        page_content: Formatted guideline section content.
        metadata: Document metadata including source, type, and retrieval timestamp.

    Example:
        >>> doc = GuidelineDocument(
        ...     page_content="## Léčba hypertenze\n\nU pacientů s hypertenzí..."
        ... )
        >>> doc.metadata["source"]
        'guidelines'
    """

    page_content: str = Field(..., description="Formatted guideline section")
    metadata: dict[str, Any] = Field(
        default_factory=lambda: {
            "source": "guidelines",
            "source_type": "clinical_guidelines",
            "retrieved_at": datetime.now().isoformat(),
        },
        description="Document metadata",
    )
