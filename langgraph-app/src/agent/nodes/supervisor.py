"""Supervisor Intent Classifier for Czech MedAI.

This module implements the LLM-based intent classification for routing
user queries to appropriate specialized agents. It uses Claude function
calling for structured output.

The IntentClassifier supports 8 intent types:
- drug_info: Drug-related queries (SUKL database)
- guideline_lookup: Guidelines and recommendations (CLS JEP)
- research_query: Research and literature (PubMed)
- compound_query: Multi-agent queries
- clinical_question: Clinical diagnosis/treatment
- urgent_diagnostic: Urgent diagnostic queries
- general_medical: General medical questions
- out_of_scope: Non-medical queries

Example:
    >>> classifier = IntentClassifier()
    >>> result = await classifier.classify_intent("Jaké je složení Ibalginu?")
    >>> result.intent_type
    IntentType.DRUG_INFO
"""

import logging

from langchain_anthropic import ChatAnthropic

from agent.models.supervisor_models import (
    VALID_AGENT_NAMES,
    IntentResult,
    IntentType,
)
from agent.nodes.supervisor_prompts import (
    build_classification_prompt,
    build_function_schema,
)

logger = logging.getLogger(__name__)


class IntentClassifier:
    """LLM-based intent classifier using Claude function calling.

    This class classifies Czech medical queries into 8 intent types
    and determines which agents should handle the query.

    Attributes:
        model_name: Claude model name (default: claude-sonnet-4).
        temperature: Temperature for generation (default: 0.0).
        llm: ChatAnthropic instance for API calls.

    Example:
        >>> classifier = IntentClassifier()
        >>> result = await classifier.classify_intent("Jaké jsou guidelines pro hypertenzi?")
        >>> result.intent_type
        IntentType.GUIDELINE_LOOKUP
        >>> result.agents_to_call
        ['guidelines_agent']
    """

    def __init__(
        self,
        model_name: str = "claude-sonnet-4-20250514",
        temperature: float = 0.0,
        llm: ChatAnthropic | None = None,
    ) -> None:
        """Initialize the IntentClassifier.

        Args:
            model_name: Claude model name to use.
            temperature: Temperature for generation (0.0 for deterministic).
            llm: Optional pre-configured ChatAnthropic instance.
                 If None, ChatAnthropic is instantiated lazily on first
                 classify_intent call (avoids requiring ANTHROPIC_API_KEY
                 at import/construction time).
        """
        self.model_name = model_name
        self.temperature = temperature
        self.llm = llm

    async def classify_intent(self, message: str) -> IntentResult:
        """Classify user message intent using Claude function calling.

        This method sends the user query to Claude with a function calling
        schema and parses the structured response into an IntentResult.

        If the LLM call fails, it falls back to keyword-based routing.

        Args:
            message: User query text (Czech).

        Returns:
            IntentResult with intent_type, confidence, agents_to_call, reasoning.

        Raises:
            ValueError: If message is empty or whitespace-only.

        Example:
            >>> result = await classifier.classify_intent("Kolik stojí Paralen?")
            >>> result.intent_type
            IntentType.DRUG_INFO
            >>> result.confidence >= 0.9
            True
        """
        # Validate input
        if not message or not message.strip():
            raise ValueError("Message cannot be empty")

        message = message.strip()

        try:
            # Lazy-init LLM on first call (avoids requiring API key at construction)
            if self.llm is None:
                self.llm = ChatAnthropic(
                    model=self.model_name,
                    temperature=self.temperature,
                    timeout=None,
                    stop=None,
                )

            # Build prompt with few-shot examples
            prompt = build_classification_prompt(message, include_examples=True)

            # Build messages for Claude
            messages = [{"role": "user", "content": prompt}]

            # Call Claude with function calling
            response = await self.llm.ainvoke(
                messages,
                tools=[build_function_schema()],
                tool_choice={"type": "tool", "name": "classify_medical_intent"},
            )

            # Parse function call result
            if not response.tool_calls:
                logger.warning(
                    "[IntentClassifier] No tool calls in response, using fallback"
                )
                return fallback_to_keyword_routing(message)

            tool_call = response.tool_calls[0]
            args = tool_call.get("args", {})

            # Validate and create IntentResult
            result = IntentResult(
                intent_type=IntentType(args["intent_type"]),
                confidence=args["confidence"],
                agents_to_call=args["agents_to_call"],
                reasoning=args["reasoning"],
            )

            # Log low confidence warning
            if result.confidence < 0.5:
                logger.warning(
                    f"[IntentClassifier] Low confidence ({result.confidence:.2f}) "
                    f"for query: {message[:50]}..."
                )

            # Log classification
            log_intent_classification(result, message)

            return result

        except Exception as e:
            logger.error(f"[IntentClassifier] Classification failed: {e}")
            logger.info("[IntentClassifier] Falling back to keyword routing")
            return fallback_to_keyword_routing(message)


def validate_agent_names(agents: list[str]) -> list[str]:
    """Validate agent names against allowed list.

    Filters out invalid agent names and returns only valid ones.

    Args:
        agents: List of agent names from IntentResult.

    Returns:
        Filtered list of valid agent names.

    Example:
        >>> validate_agent_names(["drug_agent", "invalid_agent", "pubmed_agent"])
        ['drug_agent', 'pubmed_agent']
    """
    return [a for a in agents if a in VALID_AGENT_NAMES]


def fallback_to_keyword_routing(message: str) -> IntentResult:
    """Fallback to keyword-based routing if LLM classification fails.

    Uses existing DRUG_KEYWORDS, RESEARCH_KEYWORDS, GUIDELINES_KEYWORDS
    from graph.py for backward compatibility.

    Args:
        message: User query text.

    Returns:
        IntentResult with keyword-based classification.

    Example:
        >>> result = fallback_to_keyword_routing("Najdi lék Ibalgin")
        >>> result.intent_type
        IntentType.DRUG_INFO
        >>> "Fallback" in result.reasoning
        True
    """
    # Import keywords from graph.py (lazy import to avoid circular deps)
    from agent.graph import DRUG_KEYWORDS, GUIDELINES_KEYWORDS, RESEARCH_KEYWORDS

    message_lower = message.lower()

    # Check keywords (same logic as route_query in graph.py)
    # Research keywords first (most specific)
    if any(kw in message_lower for kw in RESEARCH_KEYWORDS):
        return IntentResult(
            intent_type=IntentType.RESEARCH_QUERY,
            confidence=0.6,
            agents_to_call=["pubmed_agent"],
            reasoning="Fallback: Research keywords detected",
        )

    # Guidelines keywords
    if any(kw in message_lower for kw in GUIDELINES_KEYWORDS):
        return IntentResult(
            intent_type=IntentType.GUIDELINE_LOOKUP,
            confidence=0.6,
            agents_to_call=["guidelines_agent"],
            reasoning="Fallback: Guidelines keywords detected",
        )

    # Drug keywords
    if any(kw in message_lower for kw in DRUG_KEYWORDS):
        return IntentResult(
            intent_type=IntentType.DRUG_INFO,
            confidence=0.6,
            agents_to_call=["drug_agent"],
            reasoning="Fallback: Drug keywords detected",
        )

    # Default: general medical
    return IntentResult(
        intent_type=IntentType.GENERAL_MEDICAL,
        confidence=0.5,
        agents_to_call=["placeholder"],
        reasoning="Fallback: No specific keywords detected",
    )


def log_intent_classification(result: IntentResult, message: str) -> None:
    """Log intent classification for observability.

    Logs the classification result at INFO level with a summary,
    and at DEBUG level with full reasoning.

    Args:
        result: IntentResult from classifier.
        message: Original user message.

    Example:
        >>> log_intent_classification(result, "Jaké je složení Ibalginu?")
        # Logs: [IntentClassifier] Intent: drug_info, Confidence: 0.95, ...
    """
    logger.info(
        f"[IntentClassifier] Intent: {result.intent_type.value}, "
        f"Confidence: {result.confidence:.2f}, "
        f"Agents: {result.agents_to_call}, "
        f"Query: {message[:50]}..."
    )
    logger.debug(f"[IntentClassifier] Reasoning: {result.reasoning}")


# Export public API
__all__ = [
    "IntentClassifier",
    "validate_agent_names",
    "fallback_to_keyword_routing",
    "log_intent_classification",
]
