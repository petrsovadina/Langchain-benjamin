"""PubMed agent node for biomedical literature search (Feature 005).

This module implements the pubmed_agent_node and helper functions for:
- Query classification (research keyword detection, PMID pattern matching)
- BioMCP article search and retrieval
- Document transformation to LangChain format
- Citation tracking (implemented in Phase 5)
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, Dict, List

from langchain_core.documents import Document
from langgraph.runtime import Runtime

from agent.models.research_models import (
    CitationReference,
    PubMedArticle,
    ResearchQuery,
)

if TYPE_CHECKING:
    from agent.graph import Context, State

# Research keywords for query classification (Czech + English)
RESEARCH_KEYWORDS = {
    # Czech
    "studie",
    "výzkum",
    "pubmed",
    "článek",
    "články",
    "literatura",
    "pmid",
    "výzkumný",
    "klinická studie",
    # English fallback
    "study",
    "research",
    "article",
    "literature",
    "paper",
}


def classify_research_query(message: str) -> ResearchQuery | None:
    """Classify user message as research query.

    Detects research intent and extracts query parameters from user message.

    Detection logic:
        1. Check for PMID pattern → query_type="pmid_lookup"
        2. Check for research keywords → query_type="search"
        3. Extract date filter if present → filters.date_range

    Args:
        message: User message text (Czech).

    Returns:
        ResearchQuery if research intent detected, else None.

    Example:
        >>> query = classify_research_query("Jaké jsou studie za poslední 2 roky o diabetu?")
        >>> assert query is not None
        >>> assert query.query_type == "search"
    """
    if not message:
        return None

    message_lower = message.lower()

    # Check for PMID pattern first (highest priority)
    # Pattern matches exactly 8 digits (not 7, not 9)
    pmid_pattern = r"PMID:?\s*(\d{8})(?!\d)"
    pmid_match = re.search(pmid_pattern, message, re.IGNORECASE)

    if pmid_match:
        pmid = pmid_match.group(1)
        return ResearchQuery(
            query_text=pmid,
            query_type="pmid_lookup",
        )

    # Check for research keywords
    has_research_keyword = any(
        keyword in message_lower for keyword in RESEARCH_KEYWORDS
    )

    if not has_research_keyword:
        return None

    # Extract date filter if present
    # Pattern: "za poslední(ch) X rok(y/let)"
    date_pattern = r"(?:za\s+)?poslední(?:ch)?\s+(\d+)\s+(rok|roky|let)"
    date_match = re.search(date_pattern, message_lower)

    filters = None
    if date_match:
        years = int(date_match.group(1))
        # Calculate date range (simplified - just mark for now)
        filters = {"years_back": years}

    return ResearchQuery(
        query_text=message,
        query_type="search",
        filters=filters,
    )


def article_to_document(article: PubMedArticle, czech_abstract: str) -> Document:
    r"""Transform PubMedArticle + Czech translation to LangChain Document.

    Converts BioMCP article response to LangChain Document format with:
    - page_content: "Title: {title}\n\nAbstract (CZ): {czech_abstract}"
    - metadata: source="PubMed", pmid, url, authors, journal, publication_date, doi

    Args:
        article: PubMed article with English metadata.
        czech_abstract: Translated Czech abstract.

    Returns:
        Document with formatted content and complete metadata.

    Example:
        >>> article = PubMedArticle(pmid="12345678", title="Test Article", abstract="Test")
        >>> doc = article_to_document(article, "Český abstrakt...")
        >>> assert doc.metadata["source"] == "PubMed"
        >>> assert doc.metadata["pmid"] == "12345678"
    """
    # Format page_content
    page_content = f"Title: {article.title}\n\nAbstract (CZ): {czech_abstract}"

    # Build metadata
    metadata = {
        "source": "PubMed",
        "pmid": article.pmid,
        "url": article.pubmed_url,
        "title": article.title,
        "authors": ", ".join(article.authors) if article.authors else "Unknown",
        "journal": article.journal or "Unknown",
        "publication_date": article.publication_date or "Unknown",
        "abstract_en": article.abstract or "",
        "abstract_cz": czech_abstract,
    }

    # Add optional fields
    if article.doi:
        metadata["doi"] = article.doi
    if article.pmc_id:
        metadata["pmc_id"] = article.pmc_id
        if article.pmc_url:
            metadata["pmc_url"] = article.pmc_url

    return Document(page_content=page_content, metadata=metadata)


def format_citation(article: PubMedArticle, citation_num: int) -> CitationReference:
    """Generate citation reference for article.

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
        >>> assert "Smith" in citation.short_citation
        >>> assert "2024" in citation.short_citation
    """
    # Extract year from publication_date
    year = "Unknown"
    if article.publication_date:
        year = article.publication_date[:4]

    # Extract first author last name
    first_author = "Unknown"
    if article.authors and len(article.authors) > 0:
        # Format: "Last, First" → extract "Last"
        first_author = article.authors[0].split(",")[0].strip()

    # Create short citation
    short_citation = f"{first_author} et al. ({year})"

    # Create full citation
    authors_str = ", ".join(article.authors) if article.authors else "Unknown authors"
    full_citation = (
        f"{authors_str}. {article.title}. {article.journal or 'Unknown journal'}. "
        f"{year}. PMID: {article.pmid}. {article.pubmed_url}"
    )

    return CitationReference(
        citation_num=citation_num,
        pmid=article.pmid,
        short_citation=short_citation,
        full_citation=full_citation,
        url=article.pubmed_url,
    )


def _build_references_section(articles: List[PubMedArticle]) -> str:
    """Build References section with numbered citations.

    Creates formatted References section for response message with:
    - Sequential numbering [1], [2], [3], ...
    - Full bibliographic citations
    - Clickable PubMed URLs

    Args:
        articles: List of PubMed articles to cite.

    Returns:
        Formatted References section as string.

    Example:
        >>> articles = [article1, article2]
        >>> refs = _build_references_section(articles)
        >>> assert "## References" in refs
        >>> assert "[1]" in refs
        >>> assert "https://pubmed.ncbi.nlm.nih.gov/" in refs
    """
    if not articles:
        return ""

    refs = ["## References\n"]
    for i, article in enumerate(articles, 1):
        citation = format_citation(article, i)
        # Format: [N] Full citation
        refs.append(f"[{i}] {citation.full_citation}\n")

    return "\n".join(refs)


async def _search_pubmed_articles(
    query: ResearchQuery, biomcp_client: Any, max_results: int = 5
) -> List[PubMedArticle]:
    """Search PubMed via BioMCP article_searcher.

    Args:
        query: Research query with English query_text.
        biomcp_client: BioMCP client instance.
        max_results: Maximum number of articles to return (default: 5).

    Returns:
        List of PubMedArticle objects.

    Raises:
        Exception: If BioMCP call fails.
    """
    # Call BioMCP article_searcher tool
    response = await biomcp_client.call_tool(
        tool_name="article_searcher",
        parameters={"query": query.query_text, "max_results": max_results},
    )

    if not response.success:
        raise Exception(f"BioMCP search failed: {response.error}")

    # Parse articles from response
    articles_data = response.data.get("articles", [])
    if not articles_data:
        return []

    articles = []
    for article_dict in articles_data[:max_results]:
        article = PubMedArticle(
            pmid=article_dict.get("pmid", "00000000"),
            title=article_dict.get("title", "Untitled"),
            abstract=article_dict.get("abstract"),
            authors=article_dict.get("authors", []),
            publication_date=article_dict.get("publication_date"),
            journal=article_dict.get("journal"),
            doi=article_dict.get("doi"),
            pmc_id=article_dict.get("pmc_id"),
        )
        articles.append(article)

    return articles


async def _get_article_by_pmid(pmid: str, biomcp_client: Any) -> PubMedArticle | None:
    """Get article by PMID via BioMCP article_getter.

    Args:
        pmid: PubMed ID (8-digit).
        biomcp_client: BioMCP client instance.

    Returns:
        PubMedArticle if found, else None.
    """
    response = await biomcp_client.call_tool(
        tool_name="article_getter", parameters={"pmid": pmid}
    )

    if not response.success:
        return None

    article_dict = response.data
    return PubMedArticle(
        pmid=article_dict.get("pmid", pmid),
        title=article_dict.get("title", "Untitled"),
        abstract=article_dict.get("abstract"),
        authors=article_dict.get("authors", []),
        publication_date=article_dict.get("publication_date"),
        journal=article_dict.get("journal"),
        doi=article_dict.get("doi"),
        pmc_id=article_dict.get("pmc_id"),
    )


async def pubmed_agent_node(state: State, runtime: Runtime[Context]) -> Dict[str, Any]:
    """Search PubMed articles with BioMCP integration.

    Workflow:
        1. Use state.research_query (already populated by translation node)
        2. Call BioMCP article_searcher or article_getter based on query_type
        3. Transform articles to Documents with English abstracts
        4. Return documents (translation to Czech happens in separate node)

    Args:
        state: Current agent state with research_query.
        runtime: Runtime context with biomcp_client.

    Returns:
        Updated state dict with:
            - retrieved_docs: List[Document] with PubMed articles (English abstracts)
            - messages: Assistant message with search summary
            - next: "__end__"

    Example:
        >>> state = State(
        ...     messages=[{"role": "user", "content": "Studie o diabetu"}],
        ...     research_query=ResearchQuery(query_text="diabetes studies", query_type="search")
        ... )
        >>> result = await pubmed_agent_node(state, runtime)
        >>> assert "retrieved_docs" in result
    """
    print("[pubmed_agent] Starting PubMed search...")

    # Get research_query from state
    research_query = state.research_query

    if not research_query:
        # Fallback: classify from last message
        if state.messages:
            last_message = state.messages[-1]
            content = (
                last_message.get("content", "")
                if isinstance(last_message, dict)
                else getattr(last_message, "content", "")
            )
            research_query = classify_research_query(content)

    if not research_query:
        print("[pubmed_agent] No research query detected")
        return {
            "retrieved_docs": [],
            "messages": [
                {
                    "role": "assistant",
                    "content": "Nerozumím vašemu dotazu. Zkuste zadat dotaz typu 'Jaké jsou studie o diabetu?'",
                }
            ],
            "next": "__end__",
        }

    # Get BioMCP client
    context = runtime.context or {}
    biomcp_client = context.get("biomcp_client")

    if not biomcp_client:
        print("[pubmed_agent] ERROR: biomcp_client not found in context")
        return {
            "retrieved_docs": [],
            "messages": [
                {
                    "role": "assistant",
                    "content": "PubMed služba dočasně nedostupná. Zkuste to prosím později.",
                }
            ],
            "next": "__end__",
        }

    try:
        # Search or lookup based on query_type
        articles = []

        if research_query.query_type == "pmid_lookup":
            print(f"[pubmed_agent] PMID lookup: {research_query.query_text}")
            article = await _get_article_by_pmid(
                research_query.query_text, biomcp_client
            )
            if article:
                articles = [article]
        else:
            # Search
            max_results_raw = context.get("max_results", 5)
            max_results = (
                int(max_results_raw) if isinstance(max_results_raw, (int, str)) else 5
            )
            print(f"[pubmed_agent] Searching: {research_query.query_text[:100]}...")
            articles = await _search_pubmed_articles(
                research_query, biomcp_client, max_results
            )

        # Check if no results
        if not articles:
            print("[pubmed_agent] No articles found")
            return {
                "retrieved_docs": [],
                "messages": [
                    {
                        "role": "assistant",
                        "content": f"Nenalezeny žádné relevantní studie pro dotaz: {research_query.query_text}",
                    }
                ],
                "next": "__end__",
            }

        # Transform articles to Documents (with English abstracts)
        documents = []
        for article in articles:
            # Use English abstract for now (Czech translation happens in next node)
            english_abstract = article.abstract or "Abstract not available"

            doc = Document(
                page_content=f"Title: {article.title}\n\nAbstract (EN): {english_abstract}",
                metadata={
                    "source": "PubMed",
                    "pmid": article.pmid,
                    "url": article.pubmed_url,
                    "title": article.title,
                    "authors": ", ".join(article.authors)
                    if article.authors
                    else "Unknown",
                    "journal": article.journal or "Unknown",
                    "publication_date": article.publication_date or "Unknown",
                    "doi": article.doi,
                    "pmc_id": article.pmc_id,
                    "abstract_en": english_abstract,
                },
            )
            documents.append(doc)

        print(f"[pubmed_agent] Found {len(documents)} articles")

        # Create response message with inline citations and References section
        summary = f"Nalezeno {len(documents)} relevantních článků z PubMed:\n\n"
        for i, article in enumerate(articles, 1):
            # Include inline citation [N] after title
            summary += f"{i}. {article.title} [{i}]\n"
            if article.authors:
                summary += f"   Autoři: {', '.join(article.authors[:3])}{'...' if len(article.authors) > 3 else ''}\n"
            if article.journal:
                summary += f"   Časopis: {article.journal}\n"
            summary += f"   PMID: {article.pmid}\n\n"

        # Add References section with full citations
        references = _build_references_section(articles)
        if references:
            summary += f"\n{references}"

        return {
            "retrieved_docs": documents,
            "messages": [{"role": "assistant", "content": summary}],
            "next": "__end__",
        }

    except Exception as e:
        print(f"[pubmed_agent] ERROR: {str(e)}")
        return {
            "retrieved_docs": [],
            "messages": [
                {
                    "role": "assistant",
                    "content": f"Nastala chyba při vyhledávání: {str(e)}. Zkuste to prosím později.",
                }
            ],
            "next": "__end__",
        }
