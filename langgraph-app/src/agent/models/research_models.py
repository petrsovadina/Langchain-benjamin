"""Pydantic models for BioMCP PubMed Agent (Feature 005).

This module defines data models for research queries, PubMed articles,
and citation tracking with Czech translation support.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal

from pydantic import BaseModel, Field, field_validator
from pydantic_core.core_schema import ValidationInfo


class ResearchQuery(BaseModel):
    """Represents a user's research query with metadata for BioMCP search.

    Attributes:
        query_text: Original user query text (Czech)
        query_type: Type of research query ("search" or "pmid_lookup")
        filters: Optional search filters (date_range, article_type, journal, max_results)

    Example:
        >>> query = ResearchQuery(
        ...     query_text="Jaké jsou nejnovější studie o diabetu typu 2?",
        ...     query_type="search",
        ...     filters={"date_range": ("2023-01-01", "2026-01-20"), "max_results": 10}
        ... )
    """

    query_text: str = Field(..., min_length=1, description="Original user query text")
    query_type: Literal["search", "pmid_lookup"] = Field(
        default="search", description="Type of research query"
    )
    filters: Dict[str, Any] | None = Field(
        default=None,
        description="Optional search filters (date_range, article_type, journal, max_results)",
    )

    @field_validator("query_text")
    @classmethod
    def validate_query_text(cls, v: str) -> str:
        """Validate query text is not empty."""
        if not v or not v.strip():
            raise ValueError("query_text must not be empty")
        return v.strip()

    @field_validator("filters")
    @classmethod
    def validate_filters(
        cls, v: Dict[str, Any] | None, info: ValidationInfo
    ) -> Dict[str, Any] | None:
        """Validate filters structure and date format."""
        if v is None:
            return None

        # Validate date_range format if present
        if "date_range" in v:
            date_range = v["date_range"]
            if not isinstance(date_range, tuple) or len(date_range) != 2:
                raise ValueError("date_range must be a tuple of (start_date, end_date)")
            # Note: Date format validation (YYYY-MM-DD) could be added here if needed

        return v


class PubMedArticle(BaseModel):
    """Represents a PubMed article with metadata for citation and display.

    Attributes:
        pmid: PubMed unique identifier (8-digit)
        title: Article title (English)
        abstract: Article abstract (English)
        authors: Author names (Last, First format)
        publication_date: Publication date (YYYY-MM-DD or YYYY-MM)
        journal: Journal name
        doi: Digital Object Identifier
        pmc_id: PubMed Central ID (if free full-text available)

    Example:
        >>> article = PubMedArticle(
        ...     pmid="12345678",
        ...     title="Efficacy of Metformin in Type 2 Diabetes",
        ...     abstract="Background: Metformin is a first-line...",
        ...     authors=["Smith, John", "Doe, Jane"],
        ...     publication_date="2024-06-15",
        ...     journal="New England Journal of Medicine",
        ...     doi="10.1056/NEJMoa2401234",
        ...     pmc_id="PMC10123456"
        ... )
    """

    pmid: str = Field(
        ..., min_length=8, max_length=8, description="PubMed unique identifier"
    )
    title: str = Field(..., min_length=1, description="Article title")
    abstract: str | None = Field(default=None, description="Article abstract")
    authors: List[str] = Field(default_factory=list, description="Author names")
    publication_date: str | None = Field(
        default=None, description="Publication date"
    )
    journal: str | None = Field(default=None, description="Journal name")
    doi: str | None = Field(default=None, description="Digital Object Identifier")
    pmc_id: str | None = Field(default=None, description="PubMed Central ID")

    @field_validator("pmid")
    @classmethod
    def validate_pmid(cls, v: str) -> str:
        """Validate PMID is 8-digit numeric string."""
        if not v.isdigit() or len(v) != 8:
            raise ValueError("pmid must be 8-digit numeric string")
        return v

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Validate title is not empty."""
        if not v or not v.strip():
            raise ValueError("title must not be empty")
        return v.strip()

    @field_validator("doi")
    @classmethod
    def validate_doi(cls, v: str | None) -> str | None:
        """Validate DOI format if provided."""
        if v is None:
            return None
        # Basic DOI pattern validation: 10.xxxx/...
        if not v.startswith("10."):
            raise ValueError("doi must start with '10.'")
        return v

    @property
    def pubmed_url(self) -> str:
        """Generate PubMed URL for article."""
        return f"https://pubmed.ncbi.nlm.nih.gov/{self.pmid}/"

    @property
    def pmc_url(self) -> str | None:
        """Generate PMC URL if pmc_id exists."""
        if self.pmc_id:
            return f"https://www.ncbi.nlm.nih.gov/pmc/articles/{self.pmc_id}/"
        return None


class TranslatedArticle(PubMedArticle):
    """Extends PubMedArticle with Czech translation for user display.

    Inherits all fields from PubMedArticle and adds:
        abstract_cz: Czech translation of abstract
        translation_timestamp: When translation was generated (UTC)

    Example:
        >>> article = TranslatedArticle(
        ...     pmid="12345678",
        ...     title="Efficacy of Metformin in Type 2 Diabetes",
        ...     abstract="Background: Metformin is a first-line...",
        ...     authors=["Smith, John", "Doe, Jane"],
        ...     publication_date="2024-06-15",
        ...     journal="NEJM",
        ...     doi="10.1056/NEJMoa2401234",
        ...     pmc_id="PMC10123456",
        ...     abstract_cz="Úvod: Metformin je lék první volby...",
        ...     translation_timestamp=datetime(2026, 1, 20, 14, 30, 0, tzinfo=timezone.utc)
        ... )
    """

    abstract_cz: str = Field(
        ..., min_length=1, description="Czech translation of abstract"
    )
    translation_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When translation was generated (UTC)",
    )

    @field_validator("abstract_cz")
    @classmethod
    def validate_abstract_cz(cls, v: str, info: ValidationInfo) -> str:
        """Validate abstract_cz is not empty if abstract exists."""
        if not v or not v.strip():
            raise ValueError("abstract_cz must not be empty")
        return v.strip()

    @field_validator("translation_timestamp")
    @classmethod
    def validate_translation_timestamp(cls, v: datetime) -> datetime:
        """Ensure translation timestamp is in UTC."""
        if v.tzinfo is None:
            # Assume UTC if no timezone info
            return v.replace(tzinfo=timezone.utc)
        return v


class CitationReference(BaseModel):
    """Links a PubMed article to its citation number in conversation.

    Attributes:
        citation_num: Sequential citation number [1], [2], [3], ...
        pmid: PubMed ID of cited article
        short_citation: Formatted short citation for inline display (e.g., "Smith et al. (2024)")
        full_citation: Complete bibliographic entry
        url: PubMed URL for verification

    Example:
        >>> citation = CitationReference(
        ...     citation_num=1,
        ...     pmid="12345678",
        ...     short_citation="Smith et al. (2024)",
        ...     full_citation="Smith J, Doe J. Efficacy of Metformin. NEJM. 2024. PMID: 12345678. https://pubmed.ncbi.nlm.nih.gov/12345678/",
        ...     url="https://pubmed.ncbi.nlm.nih.gov/12345678/"
        ... )
    """

    citation_num: int = Field(..., gt=0, description="Sequential citation number")
    pmid: str = Field(..., min_length=8, max_length=8, description="PubMed ID")
    short_citation: str = Field(
        ..., min_length=1, description="Short citation for inline display"
    )
    full_citation: str = Field(
        ..., min_length=1, description="Complete bibliographic entry"
    )
    url: str = Field(..., min_length=1, description="PubMed URL")

    @field_validator("pmid")
    @classmethod
    def validate_pmid(cls, v: str) -> str:
        """Validate PMID is 8-digit numeric string."""
        if not v.isdigit() or len(v) != 8:
            raise ValueError("pmid must be 8-digit numeric string")
        return v

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL is valid PubMed format."""
        if not v.startswith("https://pubmed.ncbi.nlm.nih.gov/"):
            raise ValueError("url must be valid PubMed URL")
        return v
