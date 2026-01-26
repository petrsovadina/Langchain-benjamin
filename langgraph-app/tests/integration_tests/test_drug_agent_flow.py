"""Integration tests for SÚKL Drug Agent flow.

End-to-end tests for the drug agent node within the LangGraph execution context.
Tests T048-T051 from Feature 003 task list.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from agent.graph import State
from agent.mcp import MCPConnectionError, MCPResponse, MCPTimeoutError
from agent.models.drug_models import DrugQuery, QueryType
from agent.nodes.drug_agent import drug_agent_node

# =============================================================================
# T048: Integration test file created
# T049: Search → Details flow
# =============================================================================


class TestDrugAgentSearchDetailsFlow:
    """Integration tests for search → details workflow (T049)."""

    @pytest.mark.asyncio
    async def test_search_then_details_flow(self, mock_sukl_client: MagicMock) -> None:
        """Test complete flow: search for drug, then get details."""
        # Create state with search query
        state = State(
            messages=[{"role": "user", "content": "Najdi Ibalgin"}],
            next="drug_agent",
            retrieved_docs=[],
        )

        # Mock runtime
        mock_runtime = MagicMock()
        mock_runtime.context = {"sukl_mcp_client": mock_sukl_client}

        # Step 1: Search
        result = await drug_agent_node(state, mock_runtime)

        assert len(result["retrieved_docs"]) > 0
        assert "Ibalgin" in result["messages"][0]["content"]

        # Step 2: Get details for first result
        state_with_details = State(
            messages=[{"role": "user", "content": "Podrobnosti o Ibalginu"}],
            next="drug_agent",
            retrieved_docs=[],
        )

        result_details = await drug_agent_node(state_with_details, mock_runtime)

        # Verify details were retrieved
        assert len(result_details["retrieved_docs"]) > 0
        # Check document contains detail information
        doc_content = result_details["retrieved_docs"][0].page_content
        assert "ibuprofenum" in doc_content.lower() or "Ibalgin" in doc_content

    @pytest.mark.asyncio
    async def test_search_with_explicit_query(
        self, mock_sukl_client: MagicMock
    ) -> None:
        """Test search using explicit DrugQuery in state."""
        state = State(
            messages=[],
            next="drug_agent",
            retrieved_docs=[],
            drug_query=DrugQuery(
                query_text="Paralen",
                query_type=QueryType.SEARCH,
                limit=5,
            ),
        )

        mock_runtime = MagicMock()
        mock_runtime.context = {"sukl_mcp_client": mock_sukl_client}

        _ = await drug_agent_node(state, mock_runtime)

        # Verify search was executed with explicit query
        mock_sukl_client.call_tool.assert_called()
        call_args = mock_sukl_client.call_tool.call_args
        assert call_args[0][1]["query"] == "Paralen"
        assert call_args[0][1]["limit"] == 5

    @pytest.mark.asyncio
    async def test_reimbursement_flow(self, mock_sukl_client: MagicMock) -> None:
        """Test reimbursement query flow."""
        state = State(
            messages=[{"role": "user", "content": "Kolik stojí Ibalgin?"}],
            next="drug_agent",
            retrieved_docs=[],
        )

        mock_runtime = MagicMock()
        mock_runtime.context = {"sukl_mcp_client": mock_sukl_client}

        result = await drug_agent_node(state, mock_runtime)

        # Verify reimbursement info in response
        response_text = result["messages"][0]["content"]
        assert "Kategorie" in response_text or "úhrad" in response_text.lower()

    @pytest.mark.asyncio
    async def test_availability_flow(self, mock_sukl_client: MagicMock) -> None:
        """Test availability check flow."""
        state = State(
            messages=[{"role": "user", "content": "Je Ibalgin dostupný?"}],
            next="drug_agent",
            retrieved_docs=[],
        )

        mock_runtime = MagicMock()
        mock_runtime.context = {"sukl_mcp_client": mock_sukl_client}

        result = await drug_agent_node(state, mock_runtime)

        # Verify availability info in response
        response_text = result["messages"][0]["content"]
        assert (
            "dostupný" in response_text.lower()
            or "✅" in response_text
            or "❌" in response_text
        )

    @pytest.mark.asyncio
    async def test_atc_search_flow(self, mock_sukl_client: MagicMock) -> None:
        """Test ATC code search flow."""
        # Configure mock for ATC search
        mock_sukl_client.call_tool = AsyncMock(
            return_value=MCPResponse(
                success=True,
                data={
                    "drugs": [
                        {
                            "name": "Ibalgin 400",
                            "atc_code": "M01AE01",
                            "registration_number": "58/123/01-C",
                        },
                        {
                            "name": "Brufen 400",
                            "atc_code": "M01AE01",
                            "registration_number": "58/456/01-C",
                        },
                    ]
                },
            )
        )

        state = State(
            messages=[{"role": "user", "content": "Léky s kódem M01AE01"}],
            next="drug_agent",
            retrieved_docs=[],
        )

        mock_runtime = MagicMock()
        mock_runtime.context = {"sukl_mcp_client": mock_sukl_client}

        result = await drug_agent_node(state, mock_runtime)

        # Verify ATC search results
        assert len(result["retrieved_docs"]) >= 1
        response_text = result["messages"][0]["content"]
        assert "M01AE01" in response_text


# =============================================================================
# T050: Error handling integration tests
# =============================================================================


class TestDrugAgentErrorHandling:
    """Integration tests for error handling (T050)."""

    @pytest.mark.asyncio
    async def test_connection_error_handling(self) -> None:
        """Test graceful handling of MCP connection errors."""
        mock_client = MagicMock()
        mock_client.call_tool = AsyncMock(
            side_effect=MCPConnectionError("Connection refused")
        )

        state = State(
            messages=[{"role": "user", "content": "Najdi Ibalgin"}],
            next="drug_agent",
            retrieved_docs=[],
        )

        mock_runtime = MagicMock()
        mock_runtime.context = {"sukl_mcp_client": mock_client}

        result = await drug_agent_node(state, mock_runtime)

        # Verify error message is user-friendly (Czech)
        response_text = result["messages"][0]["content"]
        assert "připojit" in response_text.lower() or "chyb" in response_text.lower()
        assert result["retrieved_docs"] == []

    @pytest.mark.asyncio
    async def test_timeout_error_handling(self) -> None:
        """Test graceful handling of MCP timeout errors."""
        mock_client = MagicMock()
        mock_client.call_tool = AsyncMock(
            side_effect=MCPTimeoutError("Request timed out after 30s")
        )

        state = State(
            messages=[{"role": "user", "content": "Najdi Ibalgin"}],
            next="drug_agent",
            retrieved_docs=[],
        )

        mock_runtime = MagicMock()
        mock_runtime.context = {"sukl_mcp_client": mock_client}

        result = await drug_agent_node(state, mock_runtime)

        # Verify timeout message is user-friendly
        response_text = result["messages"][0]["content"]
        assert "dlouho" in response_text.lower() or "zkuste" in response_text.lower()

    @pytest.mark.asyncio
    async def test_mcp_failure_response_handling(self) -> None:
        """Test handling of MCP failure responses (success=False)."""
        mock_client = MagicMock()
        mock_client.call_tool = AsyncMock(
            return_value=MCPResponse(
                success=False,
                error="Internal server error",
            )
        )

        state = State(
            messages=[{"role": "user", "content": "Najdi XYZ123"}],
            next="drug_agent",
            retrieved_docs=[],
        )

        mock_runtime = MagicMock()
        mock_runtime.context = {"sukl_mcp_client": mock_client}

        result = await drug_agent_node(state, mock_runtime)

        # Should handle gracefully - no results but no crash
        assert "messages" in result
        assert result["retrieved_docs"] == []

    @pytest.mark.asyncio
    async def test_missing_client_error(self) -> None:
        """Test error when SÚKL client is not configured."""
        state = State(
            messages=[{"role": "user", "content": "Najdi Ibalgin"}],
            next="drug_agent",
            retrieved_docs=[],
        )

        mock_runtime = MagicMock()
        mock_runtime.context = {}  # No sukl_mcp_client

        result = await drug_agent_node(state, mock_runtime)

        # Verify configuration error message
        response_text = result["messages"][0]["content"]
        assert (
            "chyba" in response_text.lower() or "konfigurace" in response_text.lower()
        )

    @pytest.mark.asyncio
    async def test_empty_query_handling(self) -> None:
        """Test handling of empty/missing query."""
        state = State(
            messages=[],  # No messages
            next="drug_agent",
            retrieved_docs=[],
            drug_query=None,  # No explicit query
        )

        mock_client = MagicMock()
        mock_runtime = MagicMock()
        mock_runtime.context = {"sukl_mcp_client": mock_client}

        result = await drug_agent_node(state, mock_runtime)

        # Verify helpful error message
        response_text = result["messages"][0]["content"]
        assert "nezadali" in response_text.lower() or "dotaz" in response_text.lower()


# =============================================================================
# T051: Full graph execution with drug_agent_node
# =============================================================================


class TestFullGraphExecution:
    """Integration tests for full graph execution (T051)."""

    @pytest.mark.asyncio
    async def test_graph_state_includes_drug_query_field(self) -> None:
        """Verify State dataclass has drug_query field for graph execution."""
        state = State(
            messages=[{"role": "user", "content": "test"}],
            next="placeholder",
            retrieved_docs=[],
        )

        # Verify drug_query field exists and is None by default
        assert hasattr(state, "drug_query")
        assert state.drug_query is None

        # Can set drug_query
        state.drug_query = DrugQuery(query_text="Ibalgin", query_type=QueryType.SEARCH)
        assert state.drug_query is not None
        assert state.drug_query.query_text == "Ibalgin"

    @pytest.mark.asyncio
    async def test_drug_agent_node_returns_valid_state_update(
        self, mock_sukl_client: MagicMock
    ) -> None:
        """Verify drug_agent_node returns state compatible with graph."""
        state = State(
            messages=[{"role": "user", "content": "Najdi Ibalgin"}],
            next="drug_agent",
            retrieved_docs=[],
        )

        mock_runtime = MagicMock()
        mock_runtime.context = {"sukl_mcp_client": mock_sukl_client}

        result = await drug_agent_node(state, mock_runtime)

        # Verify result is dict with expected keys
        assert isinstance(result, dict)
        assert "messages" in result
        assert "retrieved_docs" in result
        assert "next" in result

        # Verify messages format
        assert isinstance(result["messages"], list)
        assert len(result["messages"]) > 0
        assert "role" in result["messages"][0]
        assert "content" in result["messages"][0]

        # Verify retrieved_docs format
        assert isinstance(result["retrieved_docs"], list)

        # Verify next is valid
        assert result["next"] == "__end__"

    @pytest.mark.asyncio
    async def test_multiple_queries_in_sequence(
        self, mock_sukl_client: MagicMock
    ) -> None:
        """Test multiple drug queries in sequence."""
        mock_runtime = MagicMock()
        mock_runtime.context = {"sukl_mcp_client": mock_sukl_client}

        queries = [
            "Najdi Ibalgin",
            "Složení Paralenu",
            "Kolik stojí Nurofen?",
            "Je Aspirin dostupný?",
        ]

        for query_text in queries:
            state = State(
                messages=[{"role": "user", "content": query_text}],
                next="drug_agent",
                retrieved_docs=[],
            )

            result = await drug_agent_node(state, mock_runtime)

            # Each query should return valid result
            assert "messages" in result
            assert len(result["messages"]) > 0
            assert result["messages"][0]["content"]  # Non-empty response

    @pytest.mark.asyncio
    async def test_document_metadata_for_citations(
        self, mock_sukl_client: MagicMock
    ) -> None:
        """Verify retrieved documents have proper metadata for citations."""
        state = State(
            messages=[{"role": "user", "content": "Najdi Ibalgin"}],
            next="drug_agent",
            retrieved_docs=[],
        )

        mock_runtime = MagicMock()
        mock_runtime.context = {"sukl_mcp_client": mock_sukl_client}

        result = await drug_agent_node(state, mock_runtime)

        # Verify documents have citation metadata
        for doc in result["retrieved_docs"]:
            assert hasattr(doc, "metadata")
            assert doc.metadata.get("source") == "sukl"
            assert "retrieved_at" in doc.metadata
            assert "source_type" in doc.metadata
