"""Integration tests for full PubMed agent flow (Feature 005).

Tests PubMed agent with internal CZ→EN translation and BioMCP integration.
Translation sandwich removed - pubmed_agent handles CZ→EN internally.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent.graph import State
from agent.models.research_models import ResearchQuery
from agent.nodes.pubmed_agent import pubmed_agent_node


class TestFullPubMedFlow:
    """Test complete PubMed search flow with internal translation."""

    @pytest.mark.asyncio
    async def test_czech_query_with_internal_translation(
        self, mock_biomcp_client, mock_runtime
    ):
        """Test end-to-end: Czech query → internal CZ→EN → PubMed search → results.

        pubmed_agent_node now handles CZ→EN translation internally when
        no research_query is provided in state.
        """
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
        )

        # Mock the LLM translation call inside pubmed_agent
        with patch("agent.nodes.pubmed_agent._translate_query_to_english") as mock_translate:
            mock_translate.return_value = ("type 2 diabetes studies", "search")

            result = await pubmed_agent_node(state, mock_runtime)

        # Verify articles retrieved
        assert result.get("retrieved_docs") is not None
        assert len(result["retrieved_docs"]) > 0

        # Documents should have PubMed metadata
        for doc in result["retrieved_docs"]:
            assert doc.metadata["source"] == "PubMed"
            assert "pmid" in doc.metadata
            assert "url" in doc.metadata

    @pytest.mark.asyncio
    async def test_pubmed_search_with_existing_research_query(
        self, mock_biomcp_client, mock_runtime
    ):
        """Test PubMed search when research_query is already set (no translation needed)."""
        mock_runtime.context["biomcp_client"] = mock_biomcp_client

        state = State(
            messages=[
                {"role": "user", "content": "Studie za poslední 2 roky o hypertenzi"}
            ],
            next="",
            retrieved_docs=[],
            research_query=ResearchQuery(
                query_text="hypertension studies last 2 years",
                query_type="search",
            ),
        )

        result = await pubmed_agent_node(state, mock_runtime)

        assert result.get("retrieved_docs") is not None
        assert len(result["retrieved_docs"]) > 0

    @pytest.mark.asyncio
    async def test_pmid_lookup_flow(self, mock_biomcp_client, mock_runtime):
        """Test PMID lookup workflow - internal PMID detection, no LLM call."""
        mock_runtime.context["biomcp_client"] = mock_biomcp_client

        state = State(
            messages=[{"role": "user", "content": "Ukaž mi článek PMID:12345678"}],
            next="",
            retrieved_docs=[],
        )

        # PMID detection happens inside _translate_query_to_english (regex, no LLM)
        with patch("agent.nodes.pubmed_agent._translate_query_to_english") as mock_translate:
            mock_translate.return_value = ("12345678", "pmid_lookup")

            result = await pubmed_agent_node(state, mock_runtime)

        # Single article retrieved
        assert result.get("retrieved_docs") is not None
        assert len(result["retrieved_docs"]) == 1
        assert result["retrieved_docs"][0].metadata["pmid"] == "12345678"

    @pytest.mark.asyncio
    async def test_pmid_lookup_with_pmc_availability(self, mock_runtime):
        """Test PMID lookup with PMC full-text detection."""
        from agent.mcp import MCPResponse

        mock_client = MagicMock()
        mock_client.call_tool = AsyncMock()

        mock_client.call_tool.return_value = MCPResponse(
            success=True,
            data={
                "pmid": "12345678",
                "title": "Metformin in Type 2 Diabetes",
                "abstract": "Background: Metformin is first-line therapy...",
                "authors": ["Smith, John A.", "Doe, Jane B."],
                "publication_date": "2024-06-15",
                "journal": "New England Journal of Medicine",
                "doi": "10.1056/NEJMoa2024001",
                "pmc_id": "PMC11234567",
            },
        )

        mock_runtime.context["biomcp_client"] = mock_client

        state = State(
            messages=[{"role": "user", "content": "Zobraz PMID:12345678"}],
            next="",
            retrieved_docs=[],
            research_query=ResearchQuery(
                query_text="12345678", query_type="pmid_lookup"
            ),
        )

        result = await pubmed_agent_node(state, mock_runtime)

        assert result.get("retrieved_docs") is not None
        assert len(result["retrieved_docs"]) == 1

        doc = result["retrieved_docs"][0]
        assert doc.metadata["pmid"] == "12345678"
        assert doc.metadata["title"] == "Metformin in Type 2 Diabetes"
        assert doc.metadata["source"] == "PubMed"
        assert "pmc_id" in doc.metadata
        assert doc.metadata["pmc_id"] == "PMC11234567"

    @pytest.mark.asyncio
    async def test_citation_tracking_across_queries(
        self, mock_biomcp_client, mock_runtime
    ):
        """Test citation numbering across multiple queries."""
        mock_runtime.context["biomcp_client"] = mock_biomcp_client

        # First query with existing research_query
        state1 = State(
            messages=[{"role": "user", "content": "Studie o diabetu typu 2"}],
            next="",
            retrieved_docs=[],
            research_query=ResearchQuery(
                query_text="type 2 diabetes studies", query_type="search"
            ),
        )

        result1 = await pubmed_agent_node(state1, mock_runtime)

        assert result1.get("retrieved_docs") is not None
        first_query_count = len(result1["retrieved_docs"])

        # Second query
        state2 = State(
            messages=[
                {"role": "user", "content": "Studie o diabetu typu 2"},
                {"role": "assistant", "content": "Previous response"},
                {"role": "user", "content": "Studie o hypertenzi"},
            ],
            next="",
            retrieved_docs=result1["retrieved_docs"],
            research_query=ResearchQuery(
                query_text="hypertension studies", query_type="search"
            ),
        )

        result2 = await pubmed_agent_node(state2, mock_runtime)

        assert result2.get("retrieved_docs") is not None
        total_docs = len(result2["retrieved_docs"])
        assert total_docs >= first_query_count

    @pytest.mark.asyncio
    async def test_inline_citations_in_response(self, mock_biomcp_client, mock_runtime):
        """Test inline citation format [1][2][3] in response message."""
        mock_runtime.context["biomcp_client"] = mock_biomcp_client

        state = State(
            messages=[{"role": "user", "content": "Studie o diabetu typu 2"}],
            next="",
            retrieved_docs=[],
            research_query=ResearchQuery(
                query_text="type 2 diabetes studies", query_type="search"
            ),
        )

        result = await pubmed_agent_node(state, mock_runtime)

        assert "messages" in result
        assert "retrieved_docs" in result
        docs = result["retrieved_docs"]
        for doc in docs:
            assert "url" in doc.metadata
            assert "pubmed.ncbi.nlm.nih.gov" in doc.metadata["url"]
            assert "pmid" in doc.metadata

    @pytest.mark.asyncio
    async def test_biomcp_failure_graceful_degradation(self, mock_runtime):
        """Test graceful degradation when BioMCP service fails."""
        mock_client = MagicMock()
        mock_client.call_tool = AsyncMock()

        from agent.mcp import MCPResponse

        mock_client.call_tool.return_value = MCPResponse(
            success=False, error="Connection refused: BioMCP server not responding"
        )

        mock_runtime.context["biomcp_client"] = mock_client

        state = State(
            messages=[{"role": "user", "content": "Studie o diabetu"}],
            next="",
            retrieved_docs=[],
            research_query=ResearchQuery(
                query_text="diabetes studies", query_type="search"
            ),
        )

        result = await pubmed_agent_node(state, mock_runtime)

        assert result.get("retrieved_docs") is not None
        assert len(result["retrieved_docs"]) == 0
        assert result.get("messages") is not None
        error_message = result["messages"][0]["content"]
        assert any(
            keyword in error_message.lower()
            for keyword in [
                "nedostupn",
                "chyba",
                "problém",
                "zkuste",
                "unavailable",
                "error",
            ]
        )
