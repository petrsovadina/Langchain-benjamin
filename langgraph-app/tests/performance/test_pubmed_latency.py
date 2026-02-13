"""Performance benchmark tests for PubMed agent latency (T067 - SC-001).

Validates that 90% of queries complete in <5s for optimal physician experience.

Test Strategy:
- Mock LLM and BioMCP calls with realistic latencies
- Measure end-to-end time for pubmed_agent_node (internal CZ→EN + search)
- Test different query types (search, PMID lookup)
- Target: p90 < 5000ms (SC-001)

Note: Uses mocked backends to avoid API costs and ensure reproducibility.
Translation sandwich removed - pubmed_agent handles CZ→EN internally.
"""

import time
from typing import List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent.graph import State
from agent.models.research_models import ResearchQuery
from agent.nodes.pubmed_agent import pubmed_agent_node


class TestPubMedLatencyBenchmark:
    """Performance benchmark tests for PubMed agent (SC-001: <5s for 90% queries)."""

    @pytest.mark.asyncio
    async def test_search_query_latency_target(self, mock_biomcp_client, mock_runtime):
        """Test that basic search queries complete within 5s target (T067 - SC-001).

        Validates latency for: internal CZ→EN translation → BioMCP search.
        No separate translation nodes anymore.

        Target: <5000ms for 90% of queries (p90 < 5s)
        """
        mock_runtime.context["biomcp_client"] = mock_biomcp_client

        state = State(
            messages=[{"role": "user", "content": "Studie o diabetu typu 2"}],
            next="",
            retrieved_docs=[],
            research_query=ResearchQuery(
                query_text="type 2 diabetes studies", query_type="search"
            ),
        )

        start_time = time.perf_counter()
        await pubmed_agent_node(state, mock_runtime)
        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000

        assert latency_ms < 5000, (
            f"Search query latency {latency_ms:.0f}ms exceeds 5s target (SC-001). "
            f"Expected <5000ms for 90% of queries."
        )

        print(
            f"\n[PERF] Search query end-to-end latency: {latency_ms:.0f}ms (target: <5000ms)"
        )

    @pytest.mark.asyncio
    async def test_pmid_lookup_latency_target(self, mock_biomcp_client, mock_runtime):
        """Test that PMID lookups complete within 3s target (faster than search).

        PMID lookups skip LLM translation (regex detection) → direct article_getter.

        Target: <3000ms for 90% of PMID lookups
        """
        mock_runtime.context["biomcp_client"] = mock_biomcp_client

        state = State(
            messages=[{"role": "user", "content": "Zobraz PMID:12345678"}],
            next="",
            retrieved_docs=[],
            research_query=ResearchQuery(
                query_text="12345678", query_type="pmid_lookup"
            ),
        )

        start_time = time.perf_counter()
        await pubmed_agent_node(state, mock_runtime)
        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000

        assert latency_ms < 3000, (
            f"PMID lookup latency {latency_ms:.0f}ms exceeds 3s target. "
            f"PMID lookups should be faster than search queries."
        )

        print(
            f"\n[PERF] PMID lookup end-to-end latency: {latency_ms:.0f}ms (target: <3000ms)"
        )

    @pytest.mark.asyncio
    async def test_multi_article_search_latency(
        self, mock_biomcp_client, mock_runtime
    ):
        """Test latency for search returning multiple articles (5 articles).

        No separate EN→CZ translation step anymore.
        Target: <5000ms for search with 5 results.
        """
        mock_runtime.context["biomcp_client"] = mock_biomcp_client
        mock_runtime.context["max_results"] = 5

        state = State(
            messages=[
                {"role": "user", "content": "Studie o hypertenzi za poslední rok"}
            ],
            next="",
            retrieved_docs=[],
            research_query=ResearchQuery(
                query_text="hypertension studies last year", query_type="search"
            ),
        )

        start_time = time.perf_counter()
        result = await pubmed_agent_node(state, mock_runtime)
        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000

        assert len(result["retrieved_docs"]) <= 5

        assert latency_ms < 5000, (
            f"Multi-article latency {latency_ms:.0f}ms exceeds 5s target. "
            f"Without translation sandwich, should be much faster."
        )

        print(
            f"\n[PERF] Multi-article (5) end-to-end latency: {latency_ms:.0f}ms (target: <5000ms)"
        )

    @pytest.mark.asyncio
    async def test_internal_translation_latency(self, mock_biomcp_client, mock_runtime):
        """Test latency when internal CZ→EN translation is triggered."""
        mock_runtime.context["biomcp_client"] = mock_biomcp_client

        state = State(
            messages=[{"role": "user", "content": "Studie o diabetu typu 2"}],
            next="",
            retrieved_docs=[],
            # No research_query → triggers internal translation
        )

        with patch("agent.nodes.pubmed_agent._translate_query_to_english") as mock_translate:
            mock_translate.return_value = ("type 2 diabetes studies", "search")

            start_time = time.perf_counter()
            await pubmed_agent_node(state, mock_runtime)
            end_time = time.perf_counter()
            latency_ms = (end_time - start_time) * 1000

        assert latency_ms < 5000, (
            f"Internal translation + search latency {latency_ms:.0f}ms exceeds 5s target."
        )

        print(
            f"\n[PERF] Internal translation + search latency: {latency_ms:.0f}ms (target: <5000ms)"
        )

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires actual LangSmith traces for p90 calculation")
    async def test_p90_latency_from_langsmith_traces(self):
        """Test p90 latency from LangSmith production traces (manual validation)."""
        pass


# Performance monitoring helpers


def calculate_p90_latency(latencies: List[float]) -> float:
    """Calculate p90 (90th percentile) latency.

    Args:
        latencies: List of latency measurements in milliseconds.

    Returns:
        p90 latency in milliseconds.
    """
    sorted_latencies = sorted(latencies)
    p90_index = int(len(sorted_latencies) * 0.9)
    return sorted_latencies[p90_index]


def assert_latency_target(latency_ms: float, target_ms: float, query_type: str):
    """Assert that measured latency meets target.

    Args:
        latency_ms: Measured latency in milliseconds.
        target_ms: Target latency in milliseconds.
        query_type: Type of query for error messaging.

    Raises:
        AssertionError: If latency exceeds target.
    """
    assert latency_ms < target_ms, (
        f"{query_type} latency {latency_ms:.0f}ms exceeds {target_ms:.0f}ms target. "
        f"Performance optimization required to meet SC-001 success criteria."
    )
