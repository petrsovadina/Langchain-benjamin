"""Translation nodes for Czech ↔ English medical translation (Feature 005).

Implements LLM-based translation using Claude Sonnet 4.5 with specialized
medical prompts for PubMed queries and abstracts.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from langchain_anthropic import ChatAnthropic
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage
from langgraph.runtime import Runtime

from agent.models.research_models import ResearchQuery
from agent.utils.translation_prompts import CZ_TO_EN_PROMPT, EN_TO_CZ_PROMPT

if TYPE_CHECKING:
    from agent.graph import Context, State

logger = logging.getLogger(__name__)


async def translate_cz_to_en_node(
    state: State, runtime: Runtime[Context]
) -> dict[str, Any]:
    """Translate Czech query to English for PubMed search.

    Uses LLM with specialized medical prompt to:
    - Preserve Latin medical terms unchanged
    - Expand Czech abbreviations (DM2 → type 2 diabetes)
    - Maintain medical precision

    Args:
        state: Current agent state with Czech query in messages.
        runtime: Runtime context with LLM configuration.

    Returns:
        Updated state dict with:
            - research_query: ResearchQuery with English query_text

    Raises:
        ValueError: If state.messages is empty.
        IndexError: If no user message found.

    Example:
        >>> state = State(messages=[{"role": "user", "content": "Studie o diabetu typu 2"}])
        >>> result = await translate_cz_to_en_node(state, runtime)
        >>> assert "diabetes" in result["research_query"].query_text.lower()
    """
    # Get last user message
    if not state.messages:
        raise ValueError("state.messages cannot be empty")

    last_message = state.messages[-1]
    czech_query = (
        last_message.get("content", "")
        if isinstance(last_message, dict)
        else getattr(last_message, "content", "")
    )

    if not czech_query:
        raise ValueError("Last message has no content")

    logger.info("Translating CZ→EN: %s...", czech_query[:100])

    # Initialize LLM
    context = runtime.context or {}
    model_name = context.get("model_name", "claude-sonnet-4-5-20250929")
    llm = ChatAnthropic(model_name=model_name, temperature=0, timeout=None, stop=None)

    # Format prompt
    prompt = CZ_TO_EN_PROMPT.format(czech_query=czech_query)

    # Call LLM
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    # Handle both str and list content types
    english_query_raw = response.content
    english_query = (
        english_query_raw.strip()
        if isinstance(english_query_raw, str)
        else str(english_query_raw).strip()
    )

    logger.info("Translated to EN: %s...", english_query[:100])

    # Create ResearchQuery
    # Import classify_research_query for query type detection

    # Check if PMID pattern exists
    import re
    from typing import Literal

    pmid_match = re.search(r"PMID:?\s*(\d{8})", czech_query, re.IGNORECASE)
    query_type: Literal["search", "pmid_lookup"]
    if pmid_match:
        query_type = "pmid_lookup"
        english_query = pmid_match.group(1)  # Just the PMID number
    else:
        query_type = "search"

    research_query = ResearchQuery(
        query_text=english_query,
        query_type=query_type,
    )

    return {"research_query": research_query}


async def translate_en_to_cz_node(
    state: State, runtime: Runtime[Context]
) -> dict[str, Any]:
    r"""Translate English abstracts to Czech for display.

    Processes all retrieved_docs and translates English abstracts to
    professional Czech suitable for physicians.

    Args:
        state: Current agent state with retrieved_docs (English abstracts).
        runtime: Runtime context with LLM configuration.

    Returns:
        Updated state dict with:
            - retrieved_docs: List[Document] with Czech abstracts in page_content

    Example:
        >>> docs = [Document(page_content="Title: Test\\n\\nAbstract (EN): Background...")]
        >>> state = State(messages=[...], retrieved_docs=docs)
        >>> result = await translate_en_to_cz_node(state, runtime)
        >>> assert "Abstract (CZ):" in result["retrieved_docs"][0].page_content
    """
    if not state.retrieved_docs:
        logger.info("No documents to translate")
        return {"retrieved_docs": []}

    logger.info("Translating %d abstracts EN→CZ", len(state.retrieved_docs))

    # Initialize LLM
    context = runtime.context or {}
    model_name = context.get("model_name", "claude-sonnet-4-5-20250929")
    _ = context.get("batch_size", 5)  # Reserved for future parallel translation
    llm = ChatAnthropic(model_name=model_name, temperature=0, timeout=None, stop=None)

    translated_docs = []

    # Process documents in batches (default: 5 at a time for parallel translation)
    for i, doc in enumerate(state.retrieved_docs):
        # Extract English abstract from metadata
        english_abstract = doc.metadata.get("abstract_en", "")

        if not english_abstract:
            # No abstract to translate, keep document as-is
            translated_docs.append(doc)
            continue

        # Format prompt
        prompt = EN_TO_CZ_PROMPT.format(english_abstract=english_abstract)

        # Call LLM
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        # Handle both str and list content types
        czech_abstract_raw = response.content
        czech_abstract = (
            czech_abstract_raw.strip()
            if isinstance(czech_abstract_raw, str)
            else str(czech_abstract_raw).strip()
        )

        logger.debug(
            "Doc %d/%d: Translated %d → %d chars",
            i + 1, len(state.retrieved_docs), len(english_abstract), len(czech_abstract),
        )

        # Update page_content with Czech abstract
        title = doc.metadata.get("title", "Untitled")
        new_page_content = f"Title: {title}\n\nAbstract (CZ): {czech_abstract}"

        # Create new document with Czech abstract
        translated_doc = Document(
            page_content=new_page_content,
            metadata={
                **doc.metadata,
                "abstract_cz": czech_abstract,
            },
        )

        translated_docs.append(translated_doc)

    logger.info("Translation complete: %d documents", len(translated_docs))

    return {"retrieved_docs": translated_docs}
