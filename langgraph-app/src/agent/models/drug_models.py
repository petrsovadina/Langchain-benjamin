"""Pydantic models for SÚKL Drug Agent.

Domain models for drug queries and responses from SÚKL-mcp server.
Following data-model.md specification.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class QueryType(str, Enum):
    """Type of drug query for routing to appropriate SÚKL tool.

    Maps to SÚKL-mcp tools:
    - SEARCH → search_medicine
    - DETAILS → get_medicine_details
    - REIMBURSEMENT → get_reimbursement
    - AVAILABILITY → check_availability
    - ATC → get_atc_info
    - INGREDIENT → search_by_ingredient
    """

    SEARCH = "search"
    DETAILS = "details"
    REIMBURSEMENT = "reimbursement"
    AVAILABILITY = "availability"
    ATC = "atc"
    INGREDIENT = "ingredient"


class DrugQuery(BaseModel):
    """Input query for drug agent node.

    Attributes:
        query_text: Search text (drug name, ATC code, or ingredient).
        query_type: Type of query for routing.
        filters: Additional filters (e.g., limit, manufacturer).
        limit: Maximum number of results (1-100).

    Example:
        >>> query = DrugQuery(
        ...     query_text="Ibalgin",
        ...     query_type=QueryType.SEARCH,
        ...     limit=10
        ... )
    """

    query_text: str = Field(..., min_length=1, description="Search query text")
    query_type: QueryType = Field(
        default=QueryType.SEARCH, description="Query type for routing"
    )
    filters: dict[str, Any] | None = Field(
        default=None, description="Additional filters"
    )
    limit: int = Field(default=10, ge=1, le=100, description="Max results")

    @field_validator("query_text")
    @classmethod
    def validate_query_not_empty(cls, v: str) -> str:
        """Ensure query text is not just whitespace."""
        if not v.strip():
            raise ValueError("Query text cannot be empty or whitespace")
        return v.strip()


class DrugResult(BaseModel):
    """Search result for a drug (abbreviated form).

    Attributes:
        name: Drug name.
        atc_code: ATC classification code.
        registration_number: SÚKL registration number (unique ID).
        manufacturer: Drug manufacturer (optional).
        match_score: Fuzzy matching score 0.0-1.0 (optional).

    Example:
        >>> result = DrugResult(
        ...     name="Ibalgin 400",
        ...     atc_code="M01AE01",
        ...     registration_number="58/123/01-C"
        ... )
    """

    name: str = Field(..., description="Drug name")
    atc_code: str = Field(..., description="ATC classification code")
    registration_number: str = Field(..., description="SÚKL registration number")
    manufacturer: str | None = Field(default=None, description="Manufacturer")
    match_score: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Fuzzy match score"
    )

    @field_validator("atc_code")
    @classmethod
    def validate_atc_format(cls, v: str) -> str:
        """Validate ATC code format (e.g., M01AE01). Empty string allowed."""
        if v and len(v) < 3:
            raise ValueError(f"ATC code too short: {v}")
        return v.upper() if v else ""


class DrugDetails(BaseModel):
    """Complete drug information.

    Attributes:
        registration_number: SÚKL registration number.
        name: Drug name.
        active_ingredient: Primary active substance.
        composition: List of all ingredients.
        indications: What the drug is used for.
        contraindications: When not to use.
        dosage: Recommended dosage instructions.
        side_effects: Possible adverse effects.
        pharmaceutical_form: Form (tablets, syrup, etc.).
        atc_code: ATC classification code.
    """

    registration_number: str = Field(..., description="SÚKL registration number")
    name: str = Field(..., description="Drug name")
    active_ingredient: str = Field(..., description="Primary active substance")
    composition: list[str] = Field(
        default_factory=list, min_length=1, description="Ingredients list"
    )
    indications: list[str] = Field(
        default_factory=list, min_length=1, description="Indications"
    )
    contraindications: list[str] = Field(
        default_factory=list, description="Contraindications"
    )
    dosage: str = Field(..., description="Dosage instructions")
    side_effects: list[str] = Field(default_factory=list, description="Side effects")
    pharmaceutical_form: str | None = Field(
        default=None, description="Drug form (tablet, syrup, etc.)"
    )
    atc_code: str = Field(..., description="ATC code")


class ReimbursementCategory(str, Enum):
    """Czech healthcare reimbursement categories.

    - A: Fully reimbursed
    - B: Partially reimbursed (with copay)
    - D: Not reimbursed (patient pays full price)
    - N: Not yet evaluated
    """

    A = "A"
    B = "B"
    D = "D"
    N = "N"


class ReimbursementInfo(BaseModel):
    """Drug reimbursement information from VZP.

    Attributes:
        registration_number: SÚKL registration number.
        category: Reimbursement category (A/B/D/N).
        copay_amount: Patient copay in CZK (optional).
        max_price: Maximum price (optional).
        prescription_required: Whether prescription is needed.
        conditions: Reimbursement conditions.
    """

    registration_number: str = Field(..., description="SÚKL registration number")
    category: ReimbursementCategory = Field(..., description="Reimbursement category")
    copay_amount: float | None = Field(
        default=None, ge=0, description="Patient copay (CZK)"
    )
    max_price: float | None = Field(default=None, ge=0, description="Max price")
    prescription_required: bool = Field(
        default=True, description="Requires prescription"
    )
    conditions: list[str] = Field(
        default_factory=list, description="Reimbursement conditions"
    )


class AvailabilityInfo(BaseModel):
    """Drug availability information.

    Attributes:
        registration_number: SÚKL registration number.
        is_available: Whether drug is currently available.
        shortage_info: Information about shortage (if any).
        expected_availability: When availability is expected.
        alternatives: Alternative drugs with same active ingredient.
    """

    registration_number: str = Field(..., description="SÚKL registration number")
    is_available: bool = Field(..., description="Currently available")
    shortage_info: str | None = Field(default=None, description="Shortage info")
    expected_availability: str | None = Field(
        default=None, description="Expected availability date"
    )
    alternatives: list[DrugResult] = Field(
        default_factory=list, description="Alternative drugs"
    )


class DrugDocument(BaseModel):
    """Transformed drug data as Document-compatible format.

    Used for conversion to langchain_core.documents.Document.
    """

    page_content: str = Field(..., description="Formatted drug information")
    metadata: dict[str, Any] = Field(
        default_factory=lambda: {
            "source": "sukl",
            "source_type": "pharmaceutical_database",
            "retrieved_at": datetime.now().isoformat(),
        }
    )
