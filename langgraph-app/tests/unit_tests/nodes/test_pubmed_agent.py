"""Unit tests for pubmed_agent node (Feature 005 - Phase 3).

Tests PubMed search, document transformation, error handling, and PMID lookup.

TDD Workflow: These tests are written FIRST and should FAIL before implementation.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from agent.graph import State
from agent.models.research_models import PubMedArticle, ResearchQuery
from agent.nodes.pubmed_agent import (
    article_to_document,
    classify_research_query,
    format_citation,
    pubmed_agent_node,
)


class TestPubMedSearch:
    """Test PubMed search functionality."""

    @pytest.mark.asyncio
    async def test_pubmed_search_returns_documents(
        self, mock_biomcp_client, mock_runtime
    ):
        """Test that PubMed search returns Documents in state.

        Verifies that pubmed_agent_node calls BioMCP and returns
        retrieved_docs with proper Document format.
        """
        # Arrange
        mock_runtime.context["biomcp_client"] = mock_biomcp_client

        state = State(
            messages=[
                {
                    "role": "user",
                    "content": "Jaké jsou nejnovější studie o diabetu typu 2?",
                }
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
        from agent.mcp import MCPResponse

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
        from agent.mcp import MCPResponse

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
        czech_abstract = (
            "Úvod: Metformin je lék první volby pro léčbu diabetes mellitus typu 2..."
        )

        doc = article_to_document(article, czech_abstract)

        # Check page_content format
        assert "Title:" in doc.page_content
        assert article.title in doc.page_content
        assert (
            "Abstract (CZ):" in doc.page_content or "Abstrakt (CZ):" in doc.page_content
        )
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
        assert (
            "Smith" in citation.short_citation
            or article.authors[0].split(",")[0] in citation.short_citation
        )

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


class TestPMIDLookup:
    """Test PMID pattern detection and extraction (Phase 4 - T044)."""

    def test_pmid_pattern_with_colon(self):
        """Test PMID pattern detection with colon separator.

        Pattern: "PMID:12345678" should extract pmid and set query_type="pmid_lookup"
        """
        query = classify_research_query("Ukaž mi článek PMID:12345678")
        assert query is not None
        assert query.query_type == "pmid_lookup"
        assert query.query_text == "12345678"

    def test_pmid_pattern_without_colon(self):
        """Test PMID pattern detection without colon.

        Pattern: "PMID 12345678" should also be detected
        """
        query = classify_research_query("Najdi PMID 87654321")
        assert query is not None
        assert query.query_type == "pmid_lookup"
        assert query.query_text == "87654321"

    def test_pmid_pattern_case_insensitive(self):
        """Test PMID pattern is case-insensitive.

        Both "pmid", "PMID", "Pmid" should work
        """
        query = classify_research_query("Zobraz pmid:11223344")
        assert query is not None
        assert query.query_type == "pmid_lookup"
        assert query.query_text == "11223344"

    def test_pmid_pattern_requires_8_digits(self):
        """Test PMID pattern requires exactly 8 digits.

        7 or 9 digits should not match (PubMed PMIDs are 8 digits)
        """
        # 7 digits - should not match
        query = classify_research_query("PMID:1234567")
        assert query is None or query.query_type != "pmid_lookup"

        # 9 digits - should not match
        query = classify_research_query("PMID:123456789")
        assert query is None or query.query_type != "pmid_lookup"


class TestArticleGetter:
    """Test article_getter tool integration (Phase 4 - T045)."""

    @pytest.mark.asyncio
    async def test_get_article_by_pmid_success(self, mock_runtime):
        """Test successful article retrieval by PMID.

        Verifies _get_article_by_pmid() helper calls BioMCP article_getter
        and returns PubMedArticle object.
        """
        # Arrange
        from agent.mcp import MCPResponse
        from agent.nodes.pubmed_agent import _get_article_by_pmid

        # Create fresh mock client without side_effect
        mock_client = MagicMock()
        mock_client.call_tool = AsyncMock()

        # Mock article_getter response
        mock_client.call_tool.return_value = MCPResponse(
            success=True,
            data={
                "pmid": "12345678",
                "title": "Test Article",
                "abstract": "Background: Test abstract.",
                "authors": ["Smith, John", "Doe, Jane"],
                "publication_date": "2024-06-15",
                "journal": "NEJM",
                "doi": "10.1056/test",
            },
        )

        # Act
        article = await _get_article_by_pmid("12345678", mock_client)

        # Assert
        assert article is not None
        assert article.pmid == "12345678"
        assert article.title == "Test Article"
        assert article.abstract == "Background: Test abstract."
        # Verify article_getter was called with correct PMID
        mock_client.call_tool.assert_called_once_with(
            tool_name="article_getter", parameters={"pmid": "12345678"}
        )

    @pytest.mark.asyncio
    async def test_get_article_by_pmid_not_found(self, mock_runtime):
        """Test handling when article not found by PMID.

        Should return None gracefully without raising exception.
        """
        # Arrange
        from agent.mcp import MCPResponse
        from agent.nodes.pubmed_agent import _get_article_by_pmid

        mock_client = MagicMock()
        mock_client.call_tool = AsyncMock()
        mock_client.call_tool.return_value = MCPResponse(
            success=False, error="Article not found: PMID 99999999"
        )

        # Act
        article = await _get_article_by_pmid("99999999", mock_client)

        # Assert
        assert article is None


class TestPMCAccess:
    """Test PMC full-text link detection (Phase 4 - T046)."""

    def test_pmc_url_present_in_metadata(self, sample_pubmed_articles):
        """Test that PMC URL is included when pmc_id is available.

        Articles with pmc_id should have pmc_url in metadata.
        """
        # Find article with PMC ID
        article_with_pmc = next((a for a in sample_pubmed_articles if a.pmc_id), None)
        assert article_with_pmc is not None

        czech_abstract = "Test abstrakt v češtině"
        doc = article_to_document(article_with_pmc, czech_abstract)

        # Check PMC metadata
        assert "pmc_id" in doc.metadata
        assert doc.metadata["pmc_id"] == article_with_pmc.pmc_id
        assert "pmc_url" in doc.metadata
        assert doc.metadata["pmc_url"] == article_with_pmc.pmc_url
        assert "ncbi.nlm.nih.gov/pmc" in doc.metadata["pmc_url"]

    def test_pmc_url_absent_when_no_pmc_id(self):
        """Test that pmc_url is omitted when pmc_id is None.

        Not all articles have PMC full-text available.
        """
        article = PubMedArticle(
            pmid="12345678",
            title="Test Article",
            abstract="Background: Test.",
            authors=["Smith, John"],
            pmc_id=None,  # No PMC ID
        )

        czech_abstract = "Test abstrakt"
        doc = article_to_document(article, czech_abstract)

        # PMC fields should not be in metadata
        assert "pmc_id" not in doc.metadata or doc.metadata.get("pmc_id") is None
        assert "pmc_url" not in doc.metadata


class TestCitationNumbering:
    """Test citation numbering across multiple articles (Phase 5 - T056)."""

    def test_sequential_citation_numbers(self, sample_pubmed_articles):
        """Test that citations are numbered sequentially [1], [2], [3].

        Each article should receive a unique sequential citation number.
        """
        citations = []
        for i, article in enumerate(sample_pubmed_articles[:3], 1):
            citation = format_citation(article, i)
            citations.append(citation)

        # Check sequential numbering
        assert citations[0].citation_num == 1
        assert citations[1].citation_num == 2
        assert citations[2].citation_num == 3

    def test_citation_numbering_starts_at_one(self, sample_pubmed_articles):
        """Test that citation numbering starts at 1, not 0."""
        article = sample_pubmed_articles[0]
        citation = format_citation(article, 1)

        assert citation.citation_num == 1
        assert citation.citation_num > 0

    def test_citation_number_in_short_format(self, sample_pubmed_articles):
        """Test that citation number can be used for inline references.

        Short citation + citation_num enables "[1] Smith et al. (2024)" format.
        """
        article = sample_pubmed_articles[0]
        citation = format_citation(article, 2)

        # Should be able to format as "[2] Smith et al. (2024)"
        inline_ref = f"[{citation.citation_num}]"
        assert inline_ref == "[2]"

        # Full inline citation
        full_inline = f"[{citation.citation_num}] {citation.short_citation}"
        assert full_inline.startswith("[2]")
        assert "et al." in full_inline


class TestPaywallHandling:
    """Test paywall indication in responses (Phase 4 - T047)."""

    @pytest.mark.asyncio
    async def test_pubmed_url_always_present(self, sample_pubmed_articles):
        """Test that PubMed URL is always present for article access.

        Even paywalled articles should have pubmed_url for reference.
        """
        for article in sample_pubmed_articles:
            czech_abstract = "Test abstrakt"
            doc = article_to_document(article, czech_abstract)

            assert "url" in doc.metadata
            assert doc.metadata["url"] == article.pubmed_url
            assert "pubmed.ncbi.nlm.nih.gov" in doc.metadata["url"]

    def test_free_fulltext_indication_via_pmc(self, sample_pubmed_articles):
        """Test that PMC availability indicates free full-text access.

        Articles with pmc_id are freely accessible, paywalled ones are not.
        """
        # Find one article with PMC and one without
        article_with_pmc = next((a for a in sample_pubmed_articles if a.pmc_id), None)
        article_without_pmc = next(
            (a for a in sample_pubmed_articles if not a.pmc_id), None
        )

        assert article_with_pmc is not None
        assert article_without_pmc is not None

        # Article with PMC should have pmc_url (free access)
        doc_free = article_to_document(article_with_pmc, "Test")
        assert "pmc_url" in doc_free.metadata

        # Article without PMC should not have pmc_url (potentially paywalled)
        doc_paywalled = article_to_document(article_without_pmc, "Test")
        assert (
            "pmc_url" not in doc_paywalled.metadata
            or doc_paywalled.metadata.get("pmc_url") is None
        )
