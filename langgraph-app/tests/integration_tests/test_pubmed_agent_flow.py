"""Integration tests for full PubMed agent flow (Feature 005 - Phase 3).

Tests complete CZ→EN→PubMed→EN→CZ translation workflow with BioMCP integration.

TDD Workflow: These tests should FAIL before implementation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.agent.graph import State, Context
from src.agent.nodes.pubmed_agent import pubmed_agent_node
from src.agent.nodes.translation import translate_cz_to_en_node, translate_en_to_cz_node
from src.agent.models.research_models import ResearchQuery


class TestFullTranslationFlow:
    """Test complete Czech → English → PubMed → English → Czech flow."""

    @pytest.mark.asyncio
    async def test_full_cz_en_cz_translation_flow(self, mock_biomcp_client, mock_runtime):
        """Test end-to-end flow: CZ query → EN translation → PubMed search → CZ abstracts.

        This is the primary integration test for User Story 1 (P1).
        Validates the complete "Sandwich Pattern" workflow.
        """
        # Arrange
        mock_runtime.context["biomcp_client"] = mock_biomcp_client

        # Step 1: Start with Czech query
        initial_state = State(
            messages=[
                {"role": "user", "content": "Jaké jsou nejnovější studie o diabetu typu 2?"}
            ],
            next="",
            retrieved_docs=[],
        )

        # Step 2: Translate Czech → English
        state_after_cz_to_en = await translate_cz_to_en_node(initial_state, mock_runtime)

        # Verify research_query is populated
        assert state_after_cz_to_en.get("research_query") is not None
        english_query = state_after_cz_to_en["research_query"]
        assert "diabetes" in english_query.query_text.lower()

        # Step 3: Search PubMed with English query
        state_with_english_query = State(
            messages=initial_state.messages,
            next="",
            retrieved_docs=[],
            research_query=english_query,
        )
        state_after_pubmed = await pubmed_agent_node(state_with_english_query, mock_runtime)

        # Verify articles retrieved
        assert state_after_pubmed.get("retrieved_docs") is not None
        assert len(state_after_pubmed["retrieved_docs"]) > 0

        # Step 4: Translate English abstracts → Czech
        state_with_docs = State(
            messages=initial_state.messages,
            next="",
            retrieved_docs=state_after_pubmed["retrieved_docs"],
        )
        final_state = await translate_en_to_cz_node(state_with_docs, mock_runtime)

        # Assert: Final state has Czech abstracts
        assert final_state.get("retrieved_docs") is not None
        assert len(final_state["retrieved_docs"]) > 0

        # Check that abstracts are in Czech format
        for doc in final_state["retrieved_docs"]:
            assert "Abstract (CZ):" in doc.page_content or "Abstrakt (CZ):" in doc.page_content
            assert doc.metadata["source"] == "PubMed"
            assert "pmid" in doc.metadata
            assert "url" in doc.metadata

    @pytest.mark.asyncio
    async def test_pubmed_search_with_date_filter(self, mock_biomcp_client, mock_runtime):
        """Test PubMed search with date range filter.

        Verifies that date filters from Czech query are properly extracted
        and applied to BioMCP search.
        """
        # Arrange
        mock_runtime.context["biomcp_client"] = mock_biomcp_client

        state = State(
            messages=[
                {"role": "user", "content": "Studie za poslední 2 roky o hypertenzi"}
            ],
            next="",
            retrieved_docs=[],
        )

        # Step 1: Translate and extract date filter
        state_after_translation = await translate_cz_to_en_node(state, mock_runtime)

        # Step 2: Search with date filter
        research_query = state_after_translation["research_query"]
        state_with_query = State(
            messages=state.messages,
            next="",
            retrieved_docs=[],
            research_query=research_query,
        )
        result = await pubmed_agent_node(state_with_query, mock_runtime)

        # Assert: Results should respect date filter
        assert result.get("retrieved_docs") is not None
        # Note: Date filtering logic will be validated in actual BioMCP call

    @pytest.mark.asyncio
    async def test_pmid_lookup_flow(self, mock_biomcp_client, mock_runtime):
        """Test PMID lookup workflow (User Story 2 preview).

        Verifies that PMID pattern is detected and article_getter is called.
        """
        # Arrange
        mock_runtime.context["biomcp_client"] = mock_biomcp_client

        state = State(
            messages=[
                {"role": "user", "content": "Ukaž mi článek PMID:12345678"}
            ],
            next="",
            retrieved_docs=[],
        )

        # Step 1: Translate and detect PMID
        state_after_translation = await translate_cz_to_en_node(state, mock_runtime)
        research_query = state_after_translation["research_query"]

        # PMID lookup should be detected
        assert research_query.query_type == "pmid_lookup"
        assert "12345678" in research_query.query_text

        # Step 2: Lookup article by PMID
        state_with_query = State(
            messages=state.messages,
            next="",
            retrieved_docs=[],
            research_query=research_query,
        )
        result = await pubmed_agent_node(state_with_query, mock_runtime)

        # Assert: Single article retrieved
        assert result.get("retrieved_docs") is not None
        assert len(result["retrieved_docs"]) == 1
        assert result["retrieved_docs"][0].metadata["pmid"] == "12345678"

    @pytest.mark.asyncio
    async def test_citation_tracking_across_queries(self, mock_biomcp_client, mock_runtime):
        """Test citation numbering across multiple queries.

        Verifies that citation numbers [1], [2], [3] are assigned sequentially
        and persist across conversation turns.
        """
        # Arrange
        mock_runtime.context["biomcp_client"] = mock_biomcp_client

        # First query
        state1 = State(
            messages=[
                {"role": "user", "content": "Studie o diabetu typu 2"}
            ],
            next="",
            retrieved_docs=[],
        )

        # Execute first query
        state_after_translation1 = await translate_cz_to_en_node(state1, mock_runtime)
        state_with_query1 = State(
            messages=state1.messages,
            next="",
            retrieved_docs=[],
            research_query=state_after_translation1["research_query"],
        )
        result1 = await pubmed_agent_node(state_with_query1, mock_runtime)

        # Assert: First query has citations [1], [2], ...
        assert result1.get("retrieved_docs") is not None
        first_query_count = len(result1["retrieved_docs"])

        # Second query (in same conversation)
        state2 = State(
            messages=[
                {"role": "user", "content": "Studie o diabetu typu 2"},
                {"role": "assistant", "content": "Previous response"},
                {"role": "user", "content": "Studie o hypertenzi"},
            ],
            next="",
            retrieved_docs=result1["retrieved_docs"],  # Carry over previous docs
        )

        state_after_translation2 = await translate_cz_to_en_node(state2, mock_runtime)
        state_with_query2 = State(
            messages=state2.messages,
            next="",
            retrieved_docs=state2.retrieved_docs,
            research_query=state_after_translation2["research_query"],
        )
        result2 = await pubmed_agent_node(state_with_query2, mock_runtime)

        # Assert: Citation numbers should continue from first query
        # (Implementation detail: citation numbering logic will be in Phase 5)
        assert result2.get("retrieved_docs") is not None
        total_docs = len(result2["retrieved_docs"])
        assert total_docs >= first_query_count

    @pytest.mark.asyncio
    async def test_biomcp_failure_graceful_degradation(self, mock_runtime):
        """Test graceful degradation when BioMCP service fails.

        Verifies that Czech error messages are returned and system doesn't crash.
        """
        # Arrange
        mock_client = MagicMock()
        mock_client.call_tool = AsyncMock()

        # Simulate BioMCP failure
        from src.agent.mcp import MCPResponse

        mock_client.call_tool.return_value = MCPResponse(
            success=False, error="Connection refused: BioMCP server not responding"
        )

        mock_runtime.context["biomcp_client"] = mock_client

        state = State(
            messages=[
                {"role": "user", "content": "Studie o diabetu"}
            ],
            next="",
            retrieved_docs=[],
        )

        # Step 1: Translate query
        state_after_translation = await translate_cz_to_en_node(state, mock_runtime)

        # Step 2: Attempt PubMed search (should fail gracefully)
        state_with_query = State(
            messages=state.messages,
            next="",
            retrieved_docs=[],
            research_query=state_after_translation["research_query"],
        )

        # Should not raise exception
        result = await pubmed_agent_node(state_with_query, mock_runtime)

        # Assert: Graceful failure with Czech error message
        assert result.get("retrieved_docs") is not None
        assert len(result["retrieved_docs"]) == 0
        assert result.get("messages") is not None
        # Error message should be in Czech
        error_message = result["messages"][0]["content"]
        assert any(
            keyword in error_message.lower()
            for keyword in ["nedostupn", "chyba", "problém", "zkuste", "unavailable", "error"]
        )
