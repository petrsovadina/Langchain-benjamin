"""General Agent node implementation.

LangGraph node for answering general medical questions using LLM.
Handles queries that don't match specific agent routing (drug/research/guidelines).

Constitution Compliance:
- Principle I: Async node function with proper signature
- Principle II: Typed state/context
- Principle IV: Logging at boundaries
- Principle V: Single responsibility (general queries only)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from agent.utils.message_utils import extract_message_content

if TYPE_CHECKING:
    from langgraph.runtime import Runtime

    from agent.graph import Context, State

logger = logging.getLogger(__name__)


async def general_agent_node(state: State, runtime: Runtime[Context]) -> dict[str, Any]:
    """Answer general medical questions using LLM.

    Handles queries that don't match specific agent routing (drug/research/guidelines).
    Uses Claude to provide helpful Czech medical responses.

    Args:
        state: Current agent state with message history.
        runtime: Runtime context with model configuration.

    Returns:
        Updated state dict with:
            - messages: list with new assistant message
            - next: "__end__"
    """
    from langchain_anthropic import ChatAnthropic
    from langchain_core.messages import HumanMessage, SystemMessage

    context = runtime.context or {}
    model_name = context.get("model_name", "claude-sonnet-4-5-20250929")

    logger.info("general_agent_node executing with model=%s", model_name)

    last_message = state.messages[-1] if state.messages else None
    if not last_message:
        return {
            "messages": [{"role": "assistant", "content": "Nebyl zadán žádný dotaz."}],
            "next": "__end__",
        }

    user_content = extract_message_content(last_message)

    try:
        llm = ChatAnthropic(
            model=model_name,
            temperature=0.0,
            timeout=None,
            stop=None,
            max_tokens=2048,
        )

        system_prompt = (
            "Jsi Czech MedAI, klinický rozhodovací asistent pro české lékaře. "
            "Odpovídáš vždy v češtině s korektní lékařskou terminologií. "
            "Poskytuj stručné, faktické a odborné odpovědi. "
            "Pokud dotaz nesouvisí s medicínou, zdvořile to uveď a nabídni pomoc "
            "s lékařským dotazem. "
            "NIKDY nevymýšlej citace ani zdroje, které nemáš k dispozici."
        )

        response = await llm.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_content),
        ])

        answer = (
            response.content
            if isinstance(response.content, str)
            else str(response.content)
        )

    except Exception as e:
        logger.error("general_agent_node LLM call failed: %s", e)
        answer = (
            "Omlouvám se, nepodařilo se zpracovat váš dotaz. "
            "Zkuste prosím specifičtější lékařský dotaz."
        )

    return {"messages": [{"role": "assistant", "content": answer}], "next": "__end__"}
