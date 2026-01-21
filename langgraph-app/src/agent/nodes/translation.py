"""Translation nodes for Czech ↔ English medical translation (Feature 005).

Implements LLM-based translation using Claude Sonnet 4.5 with specialized
medical prompts for PubMed queries and abstracts.
"""

from __future__ import annotations

from typing import Any, Dict, TYPE_CHECKING

from langchain_anthropic import ChatAnthropic
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage
from langgraph.runtime import Runtime

from agent.models.research_models import ResearchQuery
from agent.utils.translation_prompts import CZ_TO_EN_PROMPT, EN_TO_CZ_PROMPT

if TYPE_CHECKING:
    from agent.graph import State, Context


async def translate_cz_to_en_node(
    state: State, runtime: Runtime[Context]
) -> Dict[str, Any]:
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

    # Log translation
    print(f"[translate_cz_to_en] Translating: {czech_query[:100]}...")

    # Initialize LLM
    context = runtime.context or {}
    model_name = context.get("model_name", "claude-sonnet-4-5-20250929")
    llm = ChatAnthropic(model=model_name, temperature=0)  # temperature=0 for caching

    # Format prompt
    prompt = CZ_TO_EN_PROMPT.format(czech_query=czech_query)

    # Call LLM
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    english_query = response.content.strip()

    print(f"[translate_cz_to_en] English: {english_query[:100]}...")

    # Create ResearchQuery
    # Import classify_research_query for query type detection
    from agent.nodes.pubmed_agent import classify_research_query

    # Check if PMID pattern exists
    import re

    pmid_match = re.search(r"PMID:?\s*(\d{8})", czech_query, re.IGNORECASE)
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
) -> Dict[str, Any]:
    """Translate English abstracts to Czech for display.

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
        print("[translate_en_to_cz] No documents to translate")
        return {"retrieved_docs": []}

    print(f"[translate_en_to_cz] Translating {len(state.retrieved_docs)} abstracts...")

    # Initialize LLM
    context = runtime.context or {}
    model_name = context.get("model_name", "claude-sonnet-4-5-20250929")
    batch_size = context.get("batch_size", 5)
    llm = ChatAnthropic(model=model_name, temperature=0)

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
        czech_abstract = response.content.strip()

        print(f"[translate_en_to_cz] Doc {i+1}/{len(state.retrieved_docs)}: Translated {len(english_abstract)} → {len(czech_abstract)} chars")

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

    print(f"[translate_en_to_cz] Translation complete: {len(translated_docs)} documents")

    return {"retrieved_docs": translated_docs}
