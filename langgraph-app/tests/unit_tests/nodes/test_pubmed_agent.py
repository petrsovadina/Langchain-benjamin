"""Unit tests for pubmed_agent node (Feature 005 - Phase 3).

Tests PubMed search, document transformation, error handling, and PMID lookup.

TDD Workflow: These tests are written FIRST and should FAIL before implementation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.agent.graph import State, Context
from src.agent.nodes.pubmed_agent import (
    pubmed_agent_node,
    classify_research_query,
    article_to_document,
    format_citation,
)
from src.agent.models.research_models import ResearchQuery, PubMedArticle


class TestPubMedSearch:
    """Test PubMed search functionality."""

    @pytest.mark.asyncio
    async def test_pubmed_search_returns_documents(self, mock_biomcp_client, mock_runtime):
        """Test that PubMed search returns Documents in state.

        Verifies that pubmed_agent_node calls BioMCP and returns
        retrieved_docs with proper Document format.
        """
        # Arrange
        mock_runtime.context["biomcp_client"] = mock_biomcp_client

        state = State(
            messages=[
                {"role": "user", "content": "Jaké jsou nejnovější studie o diabetu typu 2?"}
            ],
            next="",
            retrieved_docs=[],
            research_query=ResearchQuery(
                query_text="What are the latest studies on type 2 diabetes?",
                query_type="search",
            ),
        )

        # Act
        result = await pubmed_agent_node(state, mock_runtime)

        # Assert
        assert "retrieved_docs" in result
        assert len(result["retrieved_docs"]) > 0
        # Check Document format
        doc = result["retrieved_docs"][0]
        assert doc.metadata["source"] == "PubMed"
        assert "pmid" in doc.metadata
        assert "url" in doc.metadata


class TestNoResults:
    """Test handling of queries with no results."""

    @pytest.mark.asyncio
    async def test_pubmed_handles_no_results(self, mock_runtime):
        """Test graceful handling when BioMCP returns no articles.

        Should return empty retrieved_docs and Czech error message.
        """
        # Arrange
        mock_client = MagicMock()
        mock_client.call_tool = AsyncMock()

        # Return empty results
        from src.agent.mcp import MCPResponse

        mock_client.call_tool.return_value = MCPResponse(
            success=True, data={"articles": [], "total_results": 0}
        )

        mock_runtime.context["biomcp_client"] = mock_client

        state = State(
            messages=[
                {"role": "user", "content": "Velmi specifický dotaz bez výsledků"}
            ],
            next="",
            retrieved_docs=[],
            research_query=ResearchQuery(
                query_text="Very specific query with no results", query_type="search"
            ),
        )

        # Act
        result = await pubmed_agent_node(state, mock_runtime)

        # Assert
        assert "retrieved_docs" in result
        assert len(result["retrieved_docs"]) == 0
        # Should have error message in Czech
        assert "messages" in result
        assert any(
            "nenalezeny" in msg.get("content", "").lower()
            or "not found" in msg.get("content", "").lower()
            for msg in result["messages"]
        )


class TestErrorHandling:
    """Test error handling in pubmed_agent_node."""

    @pytest.mark.asyncio
    async def test_pubmed_biomcp_timeout_fallback(self, mock_runtime):
        """Test graceful fallback when BioMCP times out.

        Should return empty retrieved_docs with Czech error message
        about service unavailability.
        """
        # Arrange
        mock_client = MagicMock()
        mock_client.call_tool = AsyncMock()

        # Simulate timeout
        from src.agent.mcp import MCPResponse

        mock_client.call_tool.return_value = MCPResponse(
            success=False, error="Connection timeout after 10s"
        )

        mock_runtime.context["biomcp_client"] = mock_client

        state = State(
            messages=[{"role": "user", "content": "Studie o diabetu"}],
            next="",
            retrieved_docs=[],
            research_query=ResearchQuery(
                query_text="Studies on diabetes", query_type="search"
            ),
        )

        # Act
        result = await pubmed_agent_node(state, mock_runtime)

        # Assert
        assert "retrieved_docs" in result
        assert len(result["retrieved_docs"]) == 0
        # Should have Czech error message about service unavailability
        assert "messages" in result
        assert any(
            "nedostupn" in msg.get("content", "").lower()
            or "unavailable" in msg.get("content", "").lower()
            for msg in result["messages"]
        )


class TestQueryClassification:
    """Test classify_research_query helper function."""

    def test_classify_detects_research_keywords(self):
        """Test that research keywords are detected.

        Czech keywords: studie, výzkum, pubmed, článek, literatura
        """
        # Test with "studie" keyword
        query = classify_research_query("Jaké jsou studie o diabetu?")
        assert query is not None
        assert query.query_type == "search"

        # Test with "výzkum" keyword
        query = classify_research_query("Najdi výzkum o hypertenzi")
        assert query is not None
        assert query.query_type == "search"

        # Test with "pubmed" keyword
        query = classify_research_query("Vyhledej v pubmed články o CHOPN")
        assert query is not None
        assert query.query_type == "search"

    def test_classify_detects_pmid_pattern(self):
        """Test that PMID pattern is detected and extracted.

        Patterns: "PMID:12345678", "pmid 12345678", "PMID 12345678"
        """
        # Test with colon
        query = classify_research_query("Ukaž mi článek PMID:12345678")
        assert query is not None
        assert query.query_type == "pmid_lookup"
        assert "12345678" in query.query_text

        # Test without colon
        query = classify_research_query("Najdi PMID 87654321")
        assert query is not None
        assert query.query_type == "pmid_lookup"

    def test_classify_returns_none_for_non_research(self):
        """Test that non-research queries return None.

        Queries without research keywords should not be classified.
        """
        query = classify_research_query("Jaká je cena Ibalginu?")
        assert query is None

        query = classify_research_query("Kolik stojí lék Metformin?")
        assert query is None


class TestDocumentTransformation:
    """Test article_to_document helper function."""

    def test_article_to_document_format(self, sample_pubmed_articles):
        """Test that PubMedArticle is transformed to correct Document format.

        Document should have:
        - page_content: "Title: ...\\n\\nAbstract (CZ): ..."
        - metadata: source, pmid, url, authors, journal, etc.
        """
        article = sample_pubmed_articles[0]
        czech_abstract = "Úvod: Metformin je lék první volby pro léčbu diabetes mellitus typu 2..."

        doc = article_to_document(article, czech_abstract)

        # Check page_content format
        assert "Title:" in doc.page_content
        assert article.title in doc.page_content
        assert "Abstract (CZ):" in doc.page_content or "Abstrakt (CZ):" in doc.page_content
        assert czech_abstract in doc.page_content

        # Check metadata
        assert doc.metadata["source"] == "PubMed"
        assert doc.metadata["pmid"] == article.pmid
        assert doc.metadata["url"] == article.pubmed_url
        assert doc.metadata.get("title") == article.title

    def test_article_to_document_preserves_all_fields(self, sample_pubmed_articles):
        """Test that all article fields are preserved in metadata.

        Metadata should include: authors, journal, publication_date, doi, pmc_id
        """
        article = sample_pubmed_articles[0]
        czech_abstract = "Test abstrakt v češtině"

        doc = article_to_document(article, czech_abstract)

        # All fields should be in metadata
        assert doc.metadata.get("authors") is not None
        assert doc.metadata.get("journal") == article.journal
        assert doc.metadata.get("publication_date") == article.publication_date
        assert doc.metadata.get("doi") == article.doi
        # Original English abstract should be preserved
        assert doc.metadata.get("abstract_en") == article.abstract


class TestCitationFormatting:
    """Test format_citation helper function."""

    def test_citation_short_format(self, sample_pubmed_articles):
        """Test short citation format generation.

        Format: "{first_author_last_name} et al. ({year})"
        Example: "Smith et al. (2024)"
        """
        article = sample_pubmed_articles[0]
        citation = format_citation(article, 1)

        assert citation.citation_num == 1
        assert "et al." in citation.short_citation
        assert "2024" in citation.short_citation
        # First author last name should be present
        assert "Smith" in citation.short_citation or article.authors[0].split(",")[0] in citation.short_citation

    def test_citation_full_format(self, sample_pubmed_articles):
        """Test full citation format generation.

        Format: "{authors}. {title}. {journal}. {year}. PMID: {pmid}. {url}"
        """
        article = sample_pubmed_articles[0]
        citation = format_citation(article, 1)

        # Full citation should include all key components
        assert article.title in citation.full_citation
        assert article.journal in citation.full_citation
        assert article.pmid in citation.full_citation
        assert article.pubmed_url in citation.full_citation
        assert "PMID:" in citation.full_citation

    def test_citation_url_validation(self, sample_pubmed_articles):
        """Test that citation URL is valid PubMed format.

        URL must be: https://pubmed.ncbi.nlm.nih.gov/{pmid}/
        """
        article = sample_pubmed_articles[0]
        citation = format_citation(article, 1)

        assert citation.url == article.pubmed_url
        assert citation.url.startswith("https://pubmed.ncbi.nlm.nih.gov/")
        assert citation.url.endswith("/")
