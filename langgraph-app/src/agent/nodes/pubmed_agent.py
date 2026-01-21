"""PubMed agent node for biomedical literature search (Feature 005).

This module implements the pubmed_agent_node and helper functions for:
- Czech → English query translation
- BioMCP article search
- English → Czech abstract translation
- Citation tracking

Following TDD workflow: Stubs created first, tests written, then implementation.
"""

from typing import Any, Dict, Optional

from langchain_core.documents import Document
from langgraph.runtime import Runtime

from agent.graph import State, Context
from agent.models.research_models import (
    ResearchQuery,
    PubMedArticle,
    CitationReference,
)


def classify_research_query(message: str) -> Optional[ResearchQuery]:
    """Classify user message as research query (stub for TDD).

    Detects research intent and extracts query parameters from user message.

    Detection keywords (Czech):
        - "studie", "výzkum", "pubmed", "článek", "literatura", "pmid"

    Patterns:
        - PMID lookup: "PMID:?\\s*(\\d{8})"
        - Date filter: "(za )?poslední(ch)? (\\d+) (rok|roky|let)"

    Args:
        message: User message text (Czech).

    Returns:
        ResearchQuery if research intent detected, else None.

    Example:
        >>> query = classify_research_query("Jaké jsou studie za poslední 2 roky o diabetu?")
        >>> assert query is not None
        >>> assert query.query_type == "search"
    """
    # TODO: Implement keyword detection and PMID pattern matching (Phase 3, Task T031)
    raise NotImplementedError("classify_research_query stub - implement in Phase 3")


def article_to_document(
    article: PubMedArticle, czech_abstract: str
) -> Document:
    """Transform PubMedArticle + Czech translation to LangChain Document (stub for TDD).

    Converts BioMCP article response to LangChain Document format with:
    - page_content: "Title: {title}\\n\\nAbstract (CZ): {czech_abstract}"
    - metadata: source="PubMed", pmid, url, authors, journal, publication_date, doi

    Args:
        article: PubMed article with English metadata.
        czech_abstract: Translated Czech abstract.

    Returns:
        Document with formatted content and complete metadata.

    Example:
        >>> article = PubMedArticle(pmid="12345678", title="Test Article", ...)
        >>> doc = article_to_document(article, "Český abstrakt...")
        >>> assert doc.metadata["source"] == "PubMed"
        >>> assert doc.metadata["pmid"] == "12345678"
    """
    # TODO: Implement document transformation (Phase 3, Task T033)
    raise NotImplementedError("article_to_document stub - implement in Phase 3")


def format_citation(
    article: PubMedArticle, citation_num: int
) -> CitationReference:
    """Generate citation reference for article (stub for TDD).

    Creates both short and full citation formats:
    - Short: "{first_author_last_name} et al. ({year})"
    - Full: "{authors}. {title}. {journal}. {year}. PMID: {pmid}. {url}"

    Args:
        article: PubMed article to cite.
        citation_num: Sequential citation number [1], [2], [3], ...

    Returns:
        CitationReference with short_citation, full_citation, and url.

    Example:
        >>> article = PubMedArticle(
        ...     pmid="12345678",
        ...     title="Test Article",
        ...     authors=["Smith, John", "Doe, Jane"],
        ...     publication_date="2024-06-15",
        ...     journal="NEJM"
        ... )
        >>> citation = format_citation(article, 1)
        >>> assert citation.short_citation == "Smith et al. (2024)"
    """
    # TODO: Implement citation formatting (Phase 5, Task T059)
    raise NotImplementedError("format_citation stub - implement in Phase 5")


async def pubmed_agent_node(
    state: State, runtime: Runtime[Context]
) -> Dict[str, Any]:
    """Main node for PubMed article search with Czech ↔ English translation (stub for TDD).

    Workflow:
        1. Classify query from state.research_query or state.messages
        2. Translate Czech query → English (if needed)
        3. Call BioMCP article_searcher or article_getter
        4. Translate English abstracts → Czech
        5. Transform articles to Documents
        6. Return updated state with retrieved_docs

    Args:
        state: Current agent state with messages and optional research_query.
        runtime: Runtime context with biomcp_client.

    Returns:
        Updated state dict with:
            - retrieved_docs: List[Document] with PubMed articles
            - messages: Assistant message with article summaries
            - next: "__end__" or next node name

    Example:
        >>> state = State(
        ...     messages=[{"role": "user", "content": "Studie o diabetu typu 2"}],
        ...     research_query=None
        ... )
        >>> result = await pubmed_agent_node(state, runtime)
        >>> assert "retrieved_docs" in result
        >>> assert len(result["retrieved_docs"]) > 0
    """
    # TODO: Implement full PubMed search flow (Phase 3, Task T034)
    raise NotImplementedError("pubmed_agent_node stub - implement in Phase 3")
