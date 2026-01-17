"""Unit tests for SÚKL Drug Agent node.

Tests for Feature 003 - SÚKL Drug Agent implementation.
Follows TDD workflow per Constitution Principle III.

Test Organization:
- TestDrugSearch: T021 - Drug search functionality
- TestFuzzyMatching: T022 - Fuzzy matching behavior
- TestNoResults: T023 - Empty results handling
"""

from __future__ import annotations

from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent.graph import State
from agent.models.drug_models import (
    DrugQuery,
    DrugResult,
    DrugDetails,
    QueryType,
    ReimbursementCategory,
    ReimbursementInfo,
    AvailabilityInfo,
)
from agent.mcp import MCPResponse, MCPConnectionError, MCPTimeoutError
from agent.nodes.drug_agent import (
    classify_drug_query,
    drug_result_to_document,
    drug_details_to_document,
    reimbursement_to_document,
    availability_to_document,
    format_mcp_error,
    drug_agent_node,
    _search_drugs,
    _get_drug_details,
)


# =============================================================================
# T021: Unit tests for drug search
# =============================================================================


class TestDrugSearch:
    """Test drug search functionality (T021)."""

    @pytest.mark.asyncio
    async def test_search_drugs_returns_results(
        self, mock_sukl_client: MagicMock
    ) -> None:
        """Test that _search_drugs returns DrugResult list on success."""
        query = DrugQuery(query_text="Ibalgin", query_type=QueryType.SEARCH)

        results = await _search_drugs(mock_sukl_client, query)

        assert len(results) == 2
        assert all(isinstance(r, DrugResult) for r in results)
        assert results[0].name == "Ibalgin 400"
        assert results[0].atc_code == "M01AE01"
        assert results[0].registration_number == "58/123/01-C"

    @pytest.mark.asyncio
    async def test_search_drugs_respects_limit(
        self, mock_sukl_client: MagicMock
    ) -> None:
        """Test that search query includes limit parameter."""
        query = DrugQuery(query_text="Paralen", query_type=QueryType.SEARCH, limit=5)

        await _search_drugs(mock_sukl_client, query)

        # Verify call_tool was called with correct parameters
        mock_sukl_client.call_tool.assert_called_once()
        call_args = mock_sukl_client.call_tool.call_args
        assert call_args[0][0] == "search_drugs"
        assert call_args[0][1]["limit"] == 5

    @pytest.mark.asyncio
    async def test_drug_agent_node_search_flow(
        self, mock_sukl_client: MagicMock, sample_state: State
    ) -> None:
        """Test complete drug_agent_node search workflow."""
        # Setup: state with user message about drug search
        sample_state.messages = [
            {"role": "user", "content": "Najdi lék Ibalgin"}
        ]

        # Mock runtime with sukl_mcp_client
        mock_runtime = MagicMock()
        mock_runtime.context = {"sukl_mcp_client": mock_sukl_client}

        result = await drug_agent_node(sample_state, mock_runtime)

        # Verify response structure
        assert "messages" in result
        assert "retrieved_docs" in result
        assert result["next"] == "__end__"

        # Verify message content
        assert len(result["messages"]) == 1
        assert "Ibalgin" in result["messages"][0]["content"]

        # Verify documents were created
        assert len(result["retrieved_docs"]) > 0

    @pytest.mark.asyncio
    async def test_drug_agent_node_uses_explicit_query(
        self, mock_sukl_client: MagicMock, sample_state: State
    ) -> None:
        """Test that drug_agent_node prioritizes state.drug_query."""
        # Setup: explicit drug_query in state
        sample_state.drug_query = DrugQuery(
            query_text="Paralen",
            query_type=QueryType.SEARCH,
            limit=5
        )
        sample_state.messages = [
            {"role": "user", "content": "Something completely different"}
        ]

        mock_runtime = MagicMock()
        mock_runtime.context = {"sukl_mcp_client": mock_sukl_client}

        await drug_agent_node(sample_state, mock_runtime)

        # Verify search was performed with explicit query, not message
        call_args = mock_sukl_client.call_tool.call_args
        assert call_args[0][1]["query"] == "Paralen"


class TestQueryClassification:
    """Test query classification helper function."""

    def test_classify_search_query(self) -> None:
        """Test default classification as SEARCH."""
        assert classify_drug_query("Ibalgin") == QueryType.SEARCH
        assert classify_drug_query("najdi Paralen") == QueryType.SEARCH

    def test_classify_details_query(self) -> None:
        """Test classification of detail queries."""
        assert classify_drug_query("složení Ibalginu") == QueryType.DETAILS
        assert classify_drug_query("indikace Paralenu") == QueryType.DETAILS
        assert classify_drug_query("kontraindikace léku") == QueryType.DETAILS
        assert classify_drug_query("podrobnosti o léku") == QueryType.DETAILS

    def test_classify_reimbursement_query(self) -> None:
        """Test classification of reimbursement queries."""
        assert classify_drug_query("kolik stojí Ibalgin") == QueryType.REIMBURSEMENT
        assert classify_drug_query("cena léku") == QueryType.REIMBURSEMENT
        assert classify_drug_query("kategorie úhrady") == QueryType.REIMBURSEMENT
        assert classify_drug_query("doplatek na lék") == QueryType.REIMBURSEMENT

    def test_classify_availability_query(self) -> None:
        """Test classification of availability queries."""
        assert classify_drug_query("dostupnost Ibalginu") == QueryType.AVAILABILITY
        assert classify_drug_query("je lék dostupný") == QueryType.AVAILABILITY
        assert classify_drug_query("alternativa k léku") == QueryType.AVAILABILITY

    def test_classify_atc_query(self) -> None:
        """Test classification of ATC code queries."""
        assert classify_drug_query("M01AE01") == QueryType.ATC
        assert classify_drug_query("léky s kódem N02BE01") == QueryType.ATC

    def test_classify_ingredient_query(self) -> None:
        """Test classification of ingredient queries."""
        assert classify_drug_query("účinná látka ibuprofen") == QueryType.INGREDIENT
        assert classify_drug_query("léky s účinnou látkou paracetamol") == QueryType.INGREDIENT


# =============================================================================
# T022: Unit tests for fuzzy matching
# =============================================================================


class TestFuzzyMatching:
    """Test fuzzy matching behavior (T022)."""

    @pytest.mark.asyncio
    async def test_search_handles_typos(
        self, mock_sukl_client: MagicMock
    ) -> None:
        """Test that search handles minor typos via SÚKL fuzzy matching."""
        # The actual fuzzy matching happens in SÚKL-mcp server
        # This test verifies we pass the query correctly and handle results
        query = DrugQuery(query_text="Ibalgn", query_type=QueryType.SEARCH)  # typo

        results = await _search_drugs(mock_sukl_client, query)

        # SÚKL-mcp should return results even with typo (threshold 80)
        # Our mock returns standard results for any query
        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_search_with_partial_name(
        self, mock_sukl_client: MagicMock
    ) -> None:
        """Test search with partial drug name."""
        query = DrugQuery(query_text="Ibal", query_type=QueryType.SEARCH)

        results = await _search_drugs(mock_sukl_client, query)

        assert len(results) > 0

    def test_document_includes_match_score(
        self, sample_drug_result: DrugResult
    ) -> None:
        """Test that document metadata includes match score."""
        doc = drug_result_to_document(sample_drug_result)

        assert "match_score" in doc.metadata
        assert doc.metadata["match_score"] == 0.95


# =============================================================================
# T023: Unit tests for empty results
# =============================================================================


class TestNoResults:
    """Test empty results handling (T023)."""

    @pytest.mark.asyncio
    async def test_search_returns_empty_list_on_no_results(self) -> None:
        """Test that _search_drugs returns empty list when no matches."""
        mock_client = MagicMock()
        mock_client.call_tool = AsyncMock(
            return_value=MCPResponse(
                success=True,
                data={"drugs": []},
            )
        )

        query = DrugQuery(query_text="NonexistentDrug123", query_type=QueryType.SEARCH)
        results = await _search_drugs(mock_client, query)

        assert results == []

    @pytest.mark.asyncio
    async def test_drug_agent_node_handles_no_results(
        self, sample_state: State
    ) -> None:
        """Test drug_agent_node returns appropriate message when no results."""
        mock_client = MagicMock()
        mock_client.call_tool = AsyncMock(
            return_value=MCPResponse(success=True, data={"drugs": []})
        )

        sample_state.messages = [
            {"role": "user", "content": "Najdi lék XYZ123456"}
        ]

        mock_runtime = MagicMock()
        mock_runtime.context = {"sukl_mcp_client": mock_client}

        result = await drug_agent_node(sample_state, mock_runtime)

        assert "nebyl nalezen" in result["messages"][0]["content"].lower()
        assert len(result["retrieved_docs"]) == 0

    @pytest.mark.asyncio
    async def test_search_returns_empty_on_failure(self) -> None:
        """Test _search_drugs returns empty list on MCP failure."""
        mock_client = MagicMock()
        mock_client.call_tool = AsyncMock(
            return_value=MCPResponse(
                success=False,
                error="Connection failed",
            )
        )

        query = DrugQuery(query_text="Ibalgin", query_type=QueryType.SEARCH)
        results = await _search_drugs(mock_client, query)

        assert results == []


# =============================================================================
# Additional Helper Function Tests
# =============================================================================


class TestDocumentTransformers:
    """Test document transformation functions."""

    def test_drug_result_to_document(
        self, sample_drug_result: DrugResult
    ) -> None:
        """Test DrugResult to Document transformation."""
        doc = drug_result_to_document(sample_drug_result)

        assert "Ibalgin 400" in doc.page_content
        assert "M01AE01" in doc.page_content
        assert "58/123/01-C" in doc.page_content

        # Check metadata
        assert doc.metadata["source"] == "sukl"
        assert doc.metadata["source_type"] == "drug_search"
        assert doc.metadata["registration_number"] == "58/123/01-C"

    def test_drug_details_to_document(
        self, sample_drug_details: DrugDetails
    ) -> None:
        """Test DrugDetails to Document transformation."""
        doc = drug_details_to_document(sample_drug_details)

        assert "Ibalgin 400" in doc.page_content
        assert "ibuprofenum" in doc.page_content
        assert "Bolest hlavy" in doc.page_content

        assert doc.metadata["source_type"] == "drug_details"

    def test_reimbursement_to_document(self) -> None:
        """Test ReimbursementInfo to Document transformation."""
        info = ReimbursementInfo(
            registration_number="58/123/01-C",
            category=ReimbursementCategory.B,
            copay_amount=45.0,
            prescription_required=True,
            conditions=["Pro chronickou bolest"],
        )

        doc = reimbursement_to_document(info)

        assert "B" in doc.page_content
        assert "45.00 Kč" in doc.page_content
        assert "Ano" in doc.page_content
        assert doc.metadata["category"] == "B"

    def test_availability_to_document_available(self) -> None:
        """Test AvailabilityInfo to Document for available drug."""
        info = AvailabilityInfo(
            registration_number="58/123/01-C",
            is_available=True,
        )

        doc = availability_to_document(info)

        assert "✅ Dostupný" in doc.page_content
        assert doc.metadata["is_available"] is True

    def test_availability_to_document_unavailable_with_alternatives(self) -> None:
        """Test AvailabilityInfo with unavailable status and alternatives."""
        # Create alternative as dict (how it comes from MCP response)
        alternative = DrugResult(
            name="Ibalgin 400",
            atc_code="M01AE01",
            registration_number="58/123/01-C",
            manufacturer="Zentiva",
            match_score=0.95,
        )
        info = AvailabilityInfo(
            registration_number="58/123/01-C",
            is_available=False,
            shortage_info="Dočasný výpadek",
            expected_availability="2026-02-01",
            alternatives=[alternative],
        )

        doc = availability_to_document(info)

        assert "❌ Nedostupný" in doc.page_content
        assert "Dočasný výpadek" in doc.page_content
        assert "Ibalgin 400" in doc.page_content


class TestErrorHandling:
    """Test error handling functions."""

    def test_format_mcp_connection_error(self) -> None:
        """Test formatting of connection error."""
        error = MCPConnectionError("Connection refused")
        message = format_mcp_error(error)

        assert "připojit" in message.lower()
        assert "súkl" in message.lower()

    def test_format_mcp_timeout_error(self) -> None:
        """Test formatting of timeout error."""
        error = MCPTimeoutError("Request timed out")
        message = format_mcp_error(error)

        assert "dlouho" in message.lower()

    def test_format_generic_error(self) -> None:
        """Test formatting of generic error."""
        error = Exception("Unknown error")
        message = format_mcp_error(error)

        assert "chybě" in message.lower()

    @pytest.mark.asyncio
    async def test_drug_agent_node_handles_missing_client(
        self, sample_state: State
    ) -> None:
        """Test drug_agent_node handles missing SÚKL client gracefully."""
        sample_state.messages = [
            {"role": "user", "content": "Najdi Ibalgin"}
        ]

        mock_runtime = MagicMock()
        mock_runtime.context = {}  # No sukl_mcp_client

        result = await drug_agent_node(sample_state, mock_runtime)

        assert "chyba" in result["messages"][0]["content"].lower()
        assert result["retrieved_docs"] == []

    @pytest.mark.asyncio
    async def test_drug_agent_node_handles_no_query(
        self, mock_sukl_client: MagicMock, sample_state: State
    ) -> None:
        """Test drug_agent_node handles empty messages gracefully."""
        sample_state.messages = []
        sample_state.drug_query = None

        mock_runtime = MagicMock()
        mock_runtime.context = {"sukl_mcp_client": mock_sukl_client}

        result = await drug_agent_node(sample_state, mock_runtime)

        assert "nezadali" in result["messages"][0]["content"].lower()


class TestDrugDetails:
    """Test drug details retrieval."""

    @pytest.mark.asyncio
    async def test_get_drug_details_returns_details(
        self, mock_sukl_client: MagicMock
    ) -> None:
        """Test _get_drug_details returns DrugDetails on success."""
        details = await _get_drug_details(mock_sukl_client, "58/123/01-C")

        assert details is not None
        assert isinstance(details, DrugDetails)
        assert details.name == "Ibalgin 400"
        assert details.active_ingredient == "ibuprofenum"
        assert "Bolest hlavy" in details.indications

    @pytest.mark.asyncio
    async def test_get_drug_details_returns_none_on_failure(self) -> None:
        """Test _get_drug_details returns None on failure."""
        mock_client = MagicMock()
        mock_client.call_tool = AsyncMock(
            return_value=MCPResponse(success=False, error="Not found")
        )

        details = await _get_drug_details(mock_client, "INVALID")

        assert details is None
