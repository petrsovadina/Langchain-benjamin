"""Guidelines Agent node implementation (Feature 006).

LangGraph node for querying clinical guidelines via pgvector semantic search.
Implements guideline search and section lookup functionality.

Constitution Compliance:
- Principle I: Async node function with proper signature
- Principle II: Typed state/context, Pydantic models
- Principle IV: LangSmith tracing, logging at boundaries
- Principle V: Single responsibility, helper functions extracted
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List

from langchain_core.documents import Document

from agent.models.guideline_models import (
    GuidelineQuery,
    GuidelineQueryType,
    GuidelineSource,
)
from agent.utils.guidelines_storage import (
    GuidelineNotFoundError,
    GuidelineSearchError,
    GuidelinesStorageError,
    get_guideline_section,
    search_guidelines,
)
from agent.utils.timeout import with_timeout

if TYPE_CHECKING:
    from langgraph.runtime import Runtime

    from agent.graph import Context, State

logger = logging.getLogger(__name__)

# Similarity threshold for filtering low-relevance results
SIMILARITY_THRESHOLD = 0.7

# Search timeout in seconds
SEARCH_TIMEOUT = 10.0


# =============================================================================
# Helper Functions
# =============================================================================


def classify_guideline_query(query_text: str) -> GuidelineQueryType:
    """Classify guideline query based on text patterns.

    Detects query type for routing:
    - SECTION_LOOKUP: If query contains guideline ID pattern
    - SEARCH: Default for keyword/semantic search

    Args:
        query_text: User's query text.

    Returns:
        GuidelineQueryType: Classified query type for routing.

    Examples:
        >>> classify_guideline_query("CLS-JEP-2024-001")
        GuidelineQueryType.SECTION_LOOKUP
        >>> classify_guideline_query("léčba hypertenze guidelines")
        GuidelineQueryType.SEARCH
    """
    # Pattern for guideline ID (CLS-JEP-YYYY-NNN, ESC-YYYY-NNN, ERS-YYYY-NNN)
    guideline_id_pattern = r"\b(CLS-JEP|ESC|ERS)-\d{4}-\d{3}\b"

    if re.search(guideline_id_pattern, query_text, re.IGNORECASE):
        return GuidelineQueryType.SECTION_LOOKUP

    return GuidelineQueryType.SEARCH


def guideline_to_document(section: dict[str, Any]) -> Document:
    """Transform guideline section dict to LangChain Document.

    Args:
        section: Guideline section dict from search_guidelines().

    Returns:
        Document: Formatted document with metadata for citations.

    Example:
        >>> section = {"title": "Hypertenze", "section_name": "Léčba", ...}
        >>> doc = guideline_to_document(section)
        >>> assert doc.metadata["source"] == "cls_jep"
    """
    # Format page_content with title, section name, and content
    content = f"## {section['title']}\n\n### {section['section_name']}\n\n{section['content']}"

    return Document(
        page_content=content,
        metadata={
            "source": section["source"],
            "source_type": "clinical_guidelines",
            "guideline_id": section["guideline_id"],
            "url": section["url"],
            "publication_date": section["publication_date"],
            "similarity_score": section.get("similarity_score"),
            "retrieved_at": datetime.now().isoformat(),
        },
    )


def format_guidelines_error(error: Exception) -> str:
    """Format guidelines error as user-friendly Czech message.

    Args:
        error: Exception from guidelines storage.

    Returns:
        str: Czech error message for user.
    """
    if isinstance(error, GuidelineNotFoundError):
        return (
            "Požadovaná sekce guidelines nebyla nalezena. Zkontrolujte ID guidelines."
        )
    elif isinstance(error, GuidelineSearchError):
        return "Při vyhledávání guidelines došlo k chybě. Zkuste to prosím později."
    elif isinstance(error, GuidelinesStorageError):
        return "Databáze guidelines je dočasně nedostupná. Zkuste to za chvíli."
    elif isinstance(error, asyncio.TimeoutError):
        return "Vyhledávání trvalo příliš dlouho. Zkuste zúžit dotaz."
    else:
        return f"Při zpracování dotazu došlo k chybě: {str(error)}"


def _map_specialty_to_source(specialty: str | None) -> str | None:
    """Map specialty filter to guideline source.

    Args:
        specialty: Specialty name (cardiology, respiratory, etc.).

    Returns:
        Source filter string or None.
    """
    if not specialty:
        return None

    specialty_lower = specialty.lower()

    # Map common specialties to sources
    cardiology_keywords = ["cardiology", "kardiologie", "kardio", "srdce", "heart"]
    respiratory_keywords = ["respiratory", "pneumologie", "pneu", "plíce", "lung"]

    for kw in cardiology_keywords:
        if kw in specialty_lower:
            return GuidelineSource.ESC.value

    for kw in respiratory_keywords:
        if kw in specialty_lower:
            return GuidelineSource.ERS.value

    # Default: Czech guidelines
    return GuidelineSource.CLS_JEP.value


# =============================================================================
# Embedding Helper
# =============================================================================


async def _create_query_embedding(query_text: str, api_key: str) -> List[float]:
    """Create embedding for query text using OpenAI.

    Args:
        query_text: Query text to embed.
        api_key: OpenAI API key.

    Returns:
        List of 1536 floats (embedding vector).

    Raises:
        Exception: If OpenAI API call fails.
    """
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=api_key)
    response = await client.embeddings.create(
        model="text-embedding-ada-002",
        input=query_text,
    )
    return list(response.data[0].embedding)


# =============================================================================
# Semantic Search Helper
# =============================================================================


async def search_guidelines_semantic(
    query: GuidelineQuery,
    runtime: Runtime[Context],
) -> List[dict[str, Any]]:
    """Search guidelines using semantic similarity.

    Args:
        query: GuidelineQuery with query_text and filters.
        runtime: Runtime context with optional OpenAI API key.

    Returns:
        List of guideline sections matching the query.

    Raises:
        ValueError: If OpenAI API key is not available.
        GuidelinesStorageError: If search fails.
    """
    # Get OpenAI API key from runtime context, configurable, or environment
    # Priority: context > configurable > environment variable
    context = runtime.context or {}
    configurable = getattr(runtime, "configurable", {}) or {}
    api_key = (
        context.get("openai_api_key")
        or configurable.get("openai_api_key")
        or os.getenv("OPENAI_API_KEY")
    )

    if not api_key:
        raise ValueError(
            "OpenAI API key required for semantic search. "
            "Set OPENAI_API_KEY environment variable or provide in runtime context."
        )

    logger.debug(
        f"[guidelines_agent] Creating embedding for: {query.query_text[:100]}..."
    )

    # Create embedding for query
    embedding = await _create_query_embedding(query.query_text, api_key)

    # Map specialty to source filter
    source_filter = _map_specialty_to_source(query.specialty_filter)

    logger.debug(
        f"[guidelines_agent] Searching with source_filter={source_filter}, limit={query.limit}"
    )

    # Search with filters
    results = await search_guidelines(
        query=embedding,
        limit=query.limit,
        source_filter=source_filter,
    )

    return results


# =============================================================================
# Main Node Function
# =============================================================================


@with_timeout(timeout_seconds=10.0)
async def guidelines_agent_node(
    state: State,
    runtime: Runtime[Context],
) -> Dict[str, Any]:
    """Process guideline-related queries using pgvector semantic search.

    LangGraph node for querying clinical guidelines from ČLS JEP, ESC, ERS.
    Implements FR-001 through FR-010 for Feature 006.

    Workflow:
    1. Extract guideline query from state.guideline_query or parse from last message
    2. Classify query type (SEARCH vs SECTION_LOOKUP)
    3. Execute semantic search or direct lookup
    4. Transform response to Documents with citations
    5. Return updated state with retrieved_docs and assistant message

    Args:
        state: Current agent state with messages and optional guideline_query.
        runtime: Runtime context with OpenAI API key for embeddings.

    Returns:
        Updated state dict with:
            - messages: list with assistant response
            - retrieved_docs: list of Document objects with guideline info
            - next: routing indicator (default: __end__)

    Constitution Compliance:
        - Principle I: Async function, proper signature
        - Principle II: Typed state/context, validated with Pydantic
        - Principle IV: Entry/exit logging, LangSmith traceable
        - Principle V: Single responsibility (guideline queries only)
    """
    # Entry logging
    logger.info("[guidelines_agent_node] Starting guideline query processing")

    # Extract query
    query: GuidelineQuery | None = None

    # Priority 1: Explicit guideline_query in state
    if state.guideline_query:
        query = state.guideline_query
        logger.debug(
            f"[guidelines_agent_node] Using explicit query: {query.query_text}"
        )

    # Priority 2: Parse from last user message
    if not query and state.messages:
        last_message = state.messages[-1]
        raw_content = (
            last_message.get("content")
            if isinstance(last_message, dict)
            else last_message.content
        )
        # Ensure content is a string
        content: str | None = None
        if isinstance(raw_content, str):
            content = raw_content
        elif isinstance(raw_content, list) and raw_content:
            # Handle list of content blocks (e.g., multimodal)
            first_block = raw_content[0]
            if isinstance(first_block, str):
                content = first_block
            elif isinstance(first_block, dict) and "text" in first_block:
                content = str(first_block["text"])

        if content:
            query_type = classify_guideline_query(content)
            query = GuidelineQuery(query_text=content, query_type=query_type)
            logger.debug(
                f"[guidelines_agent_node] Parsed query from message: {content[:50]}..."
            )

    if not query:
        logger.warning("[guidelines_agent_node] No query found")
        return {
            "messages": [
                {
                    "role": "assistant",
                    "content": "Nezadali jste dotaz na guidelines. Zkuste zadat téma jako 'guidelines pro léčbu hypertenze'.",
                }
            ],
            "retrieved_docs": [],
            "next": "__end__",
        }

    # Process query based on type
    documents: List[Document] = []
    response_text = ""

    try:
        if query.query_type == GuidelineQueryType.SECTION_LOOKUP:
            # Direct lookup by guideline ID
            logger.debug(f"[guidelines_agent_node] Section lookup: {query.query_text}")

            # Extract guideline ID from query
            guideline_id_pattern = r"\b((?:CLS-JEP|ESC|ERS)-\d{4}-\d{3})\b"
            match = re.search(guideline_id_pattern, query.query_text, re.IGNORECASE)

            if match:
                guideline_id = match.group(1).upper()
                try:
                    # Get first section of the guideline
                    section = await get_guideline_section(
                        guideline_id=guideline_id,
                        section_name=None,
                        section_id=None,
                    )
                    documents = [guideline_to_document(section)]
                    response_text = f"Nalezena sekce guidelines {guideline_id}:\n\n"
                    response_text += (
                        f"**{section['title']}** - {section['section_name']}\n\n"
                    )
                    response_text += f"{section['content'][:500]}..."
                except GuidelineNotFoundError:
                    response_text = f"Guidelines s ID {guideline_id} nebyly nalezeny."
            else:
                response_text = "Nebyl rozpoznán platný ID guidelines ve vašem dotazu."

        else:
            # Semantic search
            logger.debug(
                f"[guidelines_agent_node] Semantic search: {query.query_text[:100]}..."
            )

            try:
                # Search with timeout
                results = await asyncio.wait_for(
                    search_guidelines_semantic(query, runtime),
                    timeout=SEARCH_TIMEOUT,
                )

                # Filter by similarity threshold
                filtered_results = [
                    r
                    for r in results
                    if r.get("similarity_score", 0) >= SIMILARITY_THRESHOLD
                ]

                if not filtered_results:
                    # Check if we had results but they were filtered out
                    if results:
                        logger.warning(
                            f"[guidelines_agent_node] {len(results)} results filtered out by threshold"
                        )
                        return {
                            "messages": [
                                {
                                    "role": "assistant",
                                    "content": "Nalezené guidelines nejsou dostatečně relevantní. Zkuste upřesnit dotaz.",
                                }
                            ],
                            "retrieved_docs": [],
                            "next": "__end__",
                        }
                    else:
                        logger.warning("[guidelines_agent_node] No guidelines found")
                        return {
                            "messages": [
                                {
                                    "role": "assistant",
                                    "content": f"Nenalezeny žádné guidelines odpovídající dotazu: {query.query_text}",
                                }
                            ],
                            "retrieved_docs": [],
                            "next": "__end__",
                        }

                # Transform to documents
                documents = [
                    guideline_to_document(section) for section in filtered_results
                ]

                # Build response with inline citations
                response_text = (
                    f"Nalezeno {len(filtered_results)} relevantních guidelines:\n\n"
                )
                for i, section in enumerate(filtered_results[:5], 1):  # Show top 5
                    score = section.get("similarity_score", 0)
                    source_name = _get_source_display_name(section["source"])
                    response_text += f"{i}. **{section['title']}** - {section['section_name']} [{i}]\n"
                    response_text += (
                        f"   Zdroj: {source_name} | Relevance: {score:.1%}\n"
                    )
                    response_text += f"   {section['content'][:150]}...\n\n"

                if len(filtered_results) > 5:
                    response_text += (
                        f"... a dalších {len(filtered_results) - 5} výsledků.\n"
                    )

                # Add References section
                response_text += "\n## Reference\n\n"
                for i, section in enumerate(filtered_results, 1):
                    source_name = _get_source_display_name(section["source"])
                    response_text += (
                        f"[{i}] {section['title']}. {section['section_name']}. "
                        f"{source_name}, {section['publication_date']}. "
                        f"URL: {section['url']}\n"
                    )

            except asyncio.TimeoutError:
                logger.error("[guidelines_agent_node] Search timeout")
                return {
                    "messages": [
                        {
                            "role": "assistant",
                            "content": "Vyhledávání trvalo příliš dlouho. Zkuste zúžit dotaz.",
                        }
                    ],
                    "retrieved_docs": [],
                    "next": "__end__",
                }

    except GuidelinesStorageError as e:
        logger.error(f"[guidelines_agent_node] Storage error: {e}")
        response_text = format_guidelines_error(e)

    except ValueError as e:
        # Missing OpenAI API key or invalid query
        logger.error(f"[guidelines_agent_node] Configuration error: {e}")
        response_text = str(e)

    except Exception as e:
        logger.exception(f"[guidelines_agent_node] Unexpected error: {e}")
        response_text = "Při zpracování dotazu došlo k neočekávané chybě."

    # Add citation footer if documents found
    if documents:
        response_text += "\n\n_Zdroj: Clinical Guidelines Database (ČLS JEP, ESC, ERS)_"

    # Exit logging
    logger.info(
        f"[guidelines_agent_node] Completed. Found {len(documents)} guidelines."
    )

    return {
        "messages": [{"role": "assistant", "content": response_text}],
        "retrieved_docs": documents,
        "next": "__end__",
    }


def _get_source_display_name(source: str) -> str:
    """Get display name for guideline source.

    Args:
        source: Source identifier (cls_jep, esc, ers).

    Returns:
        Human-readable source name.
    """
    source_names = {
        "cls_jep": "ČLS JEP",
        "esc": "European Society of Cardiology",
        "ers": "European Respiratory Society",
    }
    return source_names.get(source, source.upper())
