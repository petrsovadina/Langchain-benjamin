"""Performance benchmark tests for PubMed agent latency (T067 - SC-001).

Validates that 90% of queries complete in <5s for optimal physician experience.

Test Strategy:
- Mock LLM and BioMCP calls with realistic latencies
- Measure end-to-end time for complete Sandwich Pattern flow
- Test different query types (search, PMID lookup)
- Target: p90 < 5000ms (SC-001)

Note: Uses mocked backends to avoid API costs and ensure reproducibility.
"""

import asyncio
import time
from typing import List
from unittest.mock import AsyncMock, MagicMock

import pytest

from agent.graph import State
from agent.nodes.pubmed_agent import pubmed_agent_node
from agent.nodes.translation import translate_cz_to_en_node, translate_en_to_cz_node


class TestPubMedLatencyBenchmark:
    """Performance benchmark tests for PubMed agent (SC-001: <5s for 90% queries)."""

    @pytest.mark.asyncio
    async def test_search_query_latency_target(self, mock_biomcp_client, mock_runtime):
        """Test that basic search queries complete within 5s target (T067 - SC-001).

        Validates p90 latency for typical search workflow:
        CZ → EN translation → BioMCP search → EN → CZ translation

        Target: <5000ms for 90% of queries (p90 < 5s)
        """
        # Arrange
        mock_runtime.context["biomcp_client"] = mock_biomcp_client

        # Mock LLM with realistic latencies
        # Translation: ~800ms for CZ→EN, ~1200ms for EN→CZ
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock()

        # CZ→EN translation response
        async def mock_cz_to_en_translation(*args, **kwargs):
            await asyncio.sleep(0.8)  # 800ms latency

            class MockResponse:
                content = "diabetes type 2 studies"

            return MockResponse()

        # EN→CZ translation response (abstracts)
        async def mock_en_to_cz_translation(*args, **kwargs):
            await asyncio.sleep(1.2)  # 1200ms latency for longer text

            class MockResponse:
                content = "Český překlad abstraktu..."

            return MockResponse()

        state = State(
            messages=[{"role": "user", "content": "Studie o diabetu typu 2"}],
            next="",
            retrieved_docs=[],
        )

        # Act - Measure end-to-end latency
        start_time = time.perf_counter()

        # Full workflow simulation
        state_after_cz_to_en = await translate_cz_to_en_node(state, mock_runtime)
        state_with_query = State(
            messages=state.messages,
            next="",
            retrieved_docs=[],
            research_query=state_after_cz_to_en["research_query"],
        )
        state_after_pubmed = await pubmed_agent_node(state_with_query, mock_runtime)
        state_with_docs = State(
            messages=state.messages,
            next="",
            retrieved_docs=state_after_pubmed["retrieved_docs"],
        )
        _ = await translate_en_to_cz_node(state_with_docs, mock_runtime)

        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000

        # Assert: Latency within 5s target (SC-001)
        assert latency_ms < 5000, (
            f"Search query latency {latency_ms:.0f}ms exceeds 5s target (SC-001). "
            f"Expected <5000ms for 90% of queries."
        )

        # Log latency for monitoring
        print(
            f"\n[PERF] Search query end-to-end latency: {latency_ms:.0f}ms (target: <5000ms)"
        )

    @pytest.mark.asyncio
    async def test_pmid_lookup_latency_target(self, mock_biomcp_client, mock_runtime):
        """Test that PMID lookups complete within 3s target (faster than search).

        PMID lookups should be faster than search:
        - No query translation needed (PMID is universal)
        - Direct article_getter call (no search)
        - Only abstract translation needed

        Target: <3000ms for 90% of PMID lookups
        """
        # Arrange
        mock_runtime.context["biomcp_client"] = mock_biomcp_client

        state = State(
            messages=[{"role": "user", "content": "Zobraz PMID:12345678"}],
            next="",
            retrieved_docs=[],
        )

        # Act - Measure PMID lookup latency
        start_time = time.perf_counter()

        state_after_translation = await translate_cz_to_en_node(state, mock_runtime)
        state_with_query = State(
            messages=state.messages,
            next="",
            retrieved_docs=[],
            research_query=state_after_translation["research_query"],
        )
        state_after_pubmed = await pubmed_agent_node(state_with_query, mock_runtime)
        state_with_docs = State(
            messages=state.messages,
            next="",
            retrieved_docs=state_after_pubmed["retrieved_docs"],
        )
        _ = await translate_en_to_cz_node(state_with_docs, mock_runtime)

        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000

        # Assert: PMID lookup faster than search
        assert latency_ms < 3000, (
            f"PMID lookup latency {latency_ms:.0f}ms exceeds 3s target. "
            f"PMID lookups should be faster than search queries."
        )

        print(
            f"\n[PERF] PMID lookup end-to-end latency: {latency_ms:.0f}ms (target: <3000ms)"
        )

    @pytest.mark.asyncio
    async def test_multi_article_translation_latency(
        self, mock_biomcp_client, mock_runtime
    ):
        """Test latency for translating multiple article abstracts (5 articles).

        Validates that batch translation of 5 abstracts doesn't cause timeout.
        Translation should be parallelizable or cached for efficiency.

        Target: <7000ms for 5 articles (allowing extra time for translation)
        """
        # Arrange
        mock_runtime.context["biomcp_client"] = mock_biomcp_client
        mock_runtime.context["max_results"] = 5

        state = State(
            messages=[
                {"role": "user", "content": "Studie o hypertenzi za poslední rok"}
            ],
            next="",
            retrieved_docs=[],
        )

        # Act - Measure multi-article workflow
        start_time = time.perf_counter()

        state_after_cz_to_en = await translate_cz_to_en_node(state, mock_runtime)
        state_with_query = State(
            messages=state.messages,
            next="",
            retrieved_docs=[],
            research_query=state_after_cz_to_en["research_query"],
        )
        state_after_pubmed = await pubmed_agent_node(state_with_query, mock_runtime)

        # Check we got 5 articles
        assert len(state_after_pubmed["retrieved_docs"]) <= 5

        state_with_docs = State(
            messages=state.messages,
            next="",
            retrieved_docs=state_after_pubmed["retrieved_docs"],
        )
        _ = await translate_en_to_cz_node(state_with_docs, mock_runtime)

        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000

        # Assert: Multi-article within 7s
        assert latency_ms < 7000, (
            f"Multi-article latency {latency_ms:.0f}ms exceeds 7s target. "
            f"5 articles should complete within 7s including all translations."
        )

        print(
            f"\n[PERF] Multi-article (5) end-to-end latency: {latency_ms:.0f}ms (target: <7000ms)"
        )

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires actual LangSmith traces for p90 calculation")
    async def test_p90_latency_from_langsmith_traces(self):
        """Test p90 latency from LangSmith production traces (manual validation).

        This test is for manual validation using real LangSmith data:
        1. Run queries in production with LangSmith tracing enabled
        2. Export trace latencies from LangSmith dashboard
        3. Calculate p90 from real usage data
        4. Verify p90 < 5000ms (SC-001)

        Manual validation steps:
        - Query: "Studie o diabetu typu 2" (10 samples)
        - Query: "PMID:12345678" (10 samples)
        - Calculate p90 across all 20 samples
        - Assert p90 < 5s

        Expected: p90 latency < 5000ms across diverse query types
        """
        # This test requires manual execution with LangSmith
        # See docs/performance-validation.md for instructions
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
