"""Pydantic models for Supervisor Intent Classification.

This module defines the data models for intent classification in the
Czech MedAI supervisor agent. It includes:
- IntentType enum with 8 intent categories
- IntentResult model for classification results

Follows the same pattern as drug_models.py and guideline_models.py.
"""

from enum import Enum
from typing import List

from pydantic import BaseModel, Field, field_validator


class IntentType(str, Enum):
    """Intent types for Czech medical query classification.

    8 intent types covering the full spectrum of medical queries:
    - drug_info: Drug-related queries (SUKL database)
    - guideline_lookup: Guidelines and recommendations (CLS JEP)
    - research_query: Research and literature (PubMed)
    - compound_query: Multi-agent queries
    - clinical_question: Clinical diagnosis/treatment
    - urgent_diagnostic: Urgent diagnostic queries
    - general_medical: General medical questions
    - out_of_scope: Non-medical queries
    """

    DRUG_INFO = "drug_info"
    GUIDELINE_LOOKUP = "guideline_lookup"
    RESEARCH_QUERY = "research_query"
    COMPOUND_QUERY = "compound_query"
    CLINICAL_QUESTION = "clinical_question"
    URGENT_DIAGNOSTIC = "urgent_diagnostic"
    GENERAL_MEDICAL = "general_medical"
    OUT_OF_SCOPE = "out_of_scope"


# Valid agent names for validation
VALID_AGENT_NAMES = frozenset(
    {
        "drug_agent",
        "pubmed_agent",
        "guidelines_agent",
        "placeholder",
    }
)


class IntentResult(BaseModel):
    """Result of intent classification.

    Attributes:
        intent_type: Classified intent type (one of 8 categories).
        confidence: Confidence score (0.0-1.0).
        agents_to_call: List of agent names to invoke.
        reasoning: Explanation for the classification.

    Example:
        >>> result = IntentResult(
        ...     intent_type=IntentType.DRUG_INFO,
        ...     confidence=0.95,
        ...     agents_to_call=["drug_agent"],
        ...     reasoning="Query asks about drug composition"
        ... )
    """

    intent_type: IntentType = Field(description="Type of medical query intent")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score (0.0-1.0)")
    agents_to_call: List[str] = Field(
        default_factory=list, description="List of agent names to call"
    )
    reasoning: str = Field(min_length=1, description="Reasoning for classification")

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        """Validate confidence is between 0.0 and 1.0."""
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {v}")
        return v

    @field_validator("agents_to_call")
    @classmethod
    def validate_agents_to_call(cls, v: List[str]) -> List[str]:
        """Validate agent names against allowed list.

        Filters out invalid agent names and returns only valid ones.
        """
        valid_agents = [agent for agent in v if agent in VALID_AGENT_NAMES]
        return valid_agents

    @field_validator("reasoning")
    @classmethod
    def validate_reasoning(cls, v: str) -> str:
        """Validate reasoning is not empty or whitespace."""
        if not v or not v.strip():
            raise ValueError("Reasoning cannot be empty")
        return v.strip()

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "intent_type": "drug_info",
                    "confidence": 0.95,
                    "agents_to_call": ["drug_agent"],
                    "reasoning": "Query asks about drug composition (Ibalgin)",
                },
                {
                    "intent_type": "compound_query",
                    "confidence": 0.92,
                    "agents_to_call": ["drug_agent", "guidelines_agent"],
                    "reasoning": "Query requires both drug info and guidelines",
                },
            ]
        }
    }
