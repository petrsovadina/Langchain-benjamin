"""Pydantic models for Czech MedAI agent state.

This module contains domain models:
- Drug-related models for SÚKL queries
- Research-related models for PubMed queries
"""

from __future__ import annotations

from agent.models.drug_models import (
    AvailabilityInfo,
    DrugDetails,
    DrugDocument,
    DrugQuery,
    DrugResult,
    QueryType,
    ReimbursementCategory,
    ReimbursementInfo,
)
from agent.models.research_models import (
    CitationReference,
    PubMedArticle,
    ResearchQuery,
    TranslatedArticle,
)

__all__: list[str] = [
    # Drug models (Feature 003)
    "QueryType",
    "DrugQuery",
    "DrugResult",
    "DrugDetails",
    "ReimbursementCategory",
    "ReimbursementInfo",
    "AvailabilityInfo",
    "DrugDocument",
    # Research models (Feature 005)
    "ResearchQuery",
    "PubMedArticle",
    "TranslatedArticle",
    "CitationReference",
]
