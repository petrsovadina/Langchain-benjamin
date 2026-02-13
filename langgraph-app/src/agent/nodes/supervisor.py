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

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import aiohttp
from langchain_anthropic import ChatAnthropic
from langgraph.types import Send

from agent.models.supervisor_models import (
    VALID_AGENT_NAMES,
    IntentResult,
    IntentType,
)
from agent.nodes.supervisor_prompts import (
    build_classification_prompt,
    build_function_schema,
)
from agent.utils.message_utils import extract_message_content

if TYPE_CHECKING:
    from langgraph.runtime import Runtime

    from agent.graph import Context, State

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
        model_name: str | None = None,
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
        import os
        self.model_name = model_name or os.getenv("DEFAULT_MODEL_NAME", "claude-sonnet-4-20250514")
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

        except (ValueError, KeyError, TypeError) as e:
            logger.warning("[IntentClassifier] Classification parse error: %s", e)
            return fallback_to_keyword_routing(message)
        except (aiohttp.ClientError, TimeoutError, OSError) as e:
            logger.error("[IntentClassifier] Network/timeout error: %s", e)
            return fallback_to_keyword_routing(message)
        except Exception as e:
            logger.exception("[IntentClassifier] Unexpected error: %s", e)
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

    # Check keywords (same priority as route_query in graph.py)
    # Drug keywords first (most common use case)
    if any(kw in message_lower for kw in DRUG_KEYWORDS):
        return IntentResult(
            intent_type=IntentType.DRUG_INFO,
            confidence=0.6,
            agents_to_call=["drug_agent"],
            reasoning="Fallback: Drug keywords detected",
        )

    # Research keywords (research-specific terms only)
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

    # Default: general medical
    return IntentResult(
        intent_type=IntentType.GENERAL_MEDICAL,
        confidence=0.5,
        agents_to_call=["general_agent"],
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


# Map conceptual agent names to graph node names
AGENT_TO_NODE_MAP: dict[str, str] = {
    "drug_agent": "drug_agent",
    "pubmed_agent": "pubmed_agent",  # PubMed with internal CZ→EN translation
    "guidelines_agent": "guidelines_agent",
    "general_agent": "general_agent",
}


async def supervisor_node(
    state: State,
    runtime: Runtime[Context],
) -> Send | list[Send]:
    """Route user query to appropriate agent(s) using LLM-based intent classification.

    Uses LangGraph Send API for dynamic routing, enabling parallel execution
    when multiple agents are needed (compound queries).

    Workflow:
        1. Check for explicit queries (drug_query, research_query, guideline_query)
        2. Extract last user message
        3. Classify intent using IntentClassifier
        4. Validate agents_to_call
        5. Check MCP client availability
        6. Return Send commands for parallel agent execution
        7. Fallback to keyword routing if classification fails

    Args:
        state: Current agent state with messages.
        runtime: Runtime context with model configuration.

    Returns:
        Send or list[Send] for dynamic routing to agent node(s).
    """
    logger.info("[supervisor_node] Starting intent classification")

    # Check explicit queries first (backward compatibility)
    if state.drug_query is not None:
        logger.info(
            "[supervisor_node] Explicit drug_query detected, routing to drug_agent"
        )
        return Send("drug_agent", state)
    if state.research_query is not None:
        logger.info(
            "[supervisor_node] Explicit research_query detected, "
            "routing to pubmed_agent"
        )
        return Send("pubmed_agent", state)
    if state.guideline_query is not None:
        logger.info(
            "[supervisor_node] Explicit guideline_query detected, "
            "routing to guidelines_agent"
        )
        return Send("guidelines_agent", state)

    # Extract last user message
    if not state.messages:
        logger.warning("[supervisor_node] No messages in state")
        return Send("general_agent", state)

    last_message = state.messages[-1]
    content = extract_message_content(last_message)

    if not content:
        logger.warning("[supervisor_node] Empty message content")
        return Send("general_agent", state)

    # Classify intent
    context = runtime.context or {}
    classifier = IntentClassifier(
        model_name=context.get("model_name", "claude-sonnet-4-20250514"),
        temperature=context.get("temperature", 0.0),
    )

    try:
        result = await classifier.classify_intent(content)
        logger.info(
            f"[supervisor_node] Intent: {result.intent_type.value}, "
            f"Confidence: {result.confidence:.2f}, "
            f"Agents: {result.agents_to_call}"
        )
    except (ValueError, KeyError, TypeError, OSError) as e:
        logger.error("[supervisor_node] Classification failed: %s", e)
        # Fallback to keyword routing
        from agent.graph import route_query

        fallback_node = route_query(state)
        logger.info("[supervisor_node] Fallback routing to: %s", fallback_node)
        return Send(fallback_node, state)
    except Exception as e:
        logger.exception("[supervisor_node] Unexpected classification error: %s", e)
        from agent.graph import route_query

        fallback_node = route_query(state)
        logger.info("[supervisor_node] Fallback routing to: %s", fallback_node)
        return Send(fallback_node, state)

    # Validate agents
    valid_agents = validate_agent_names(result.agents_to_call)

    if not valid_agents:
        logger.warning("[supervisor_node] No valid agents, routing to general_agent")
        return Send("general_agent", state)

    # Multi-agent routing with Send API (parallel execution)
    send_commands: list[Send] = []

    for agent_name in valid_agents:
        # Check agent availability (fallback if MCP client unavailable)
        if agent_name in ("drug_agent", "pubmed_agent"):
            from agent.graph import get_mcp_clients

            sukl_client, biomcp_client = get_mcp_clients(runtime)

            if agent_name == "drug_agent" and not sukl_client:
                logger.warning(
                    f"[supervisor_node] SUKL client unavailable, skipping {agent_name}"
                )
                continue
            elif agent_name == "pubmed_agent" and not biomcp_client:
                logger.warning(
                    f"[supervisor_node] BioMCP client unavailable, "
                    f"skipping {agent_name}"
                )
                continue

        # Map agent name to graph node name
        target_node = AGENT_TO_NODE_MAP.get(agent_name, "general_agent")

        # Create Send command for this agent
        send_commands.append(Send(target_node, state))
        logger.info(f"[supervisor_node] Scheduling agent: {target_node}")

    # Fallback if no valid agents after availability checks
    if not send_commands:
        logger.warning(
            "[supervisor_node] No valid agents available, routing to general_agent"
        )
        return Send("general_agent", state)

    logger.info(f"[supervisor_node] Parallel execution: {len(send_commands)} agent(s)")

    # Return single Send or list for parallel execution
    if len(send_commands) == 1:
        return send_commands[0]
    return send_commands


# Export public API
__all__ = [
    "IntentClassifier",
    "validate_agent_names",
    "fallback_to_keyword_routing",
    "log_intent_classification",
    "extract_message_content",
    "supervisor_node",
    "AGENT_TO_NODE_MAP",
]
