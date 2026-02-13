"""Integration tests for parallel agent execution (Feature 007).

Tests compound queries that require multiple agents to run in parallel.
Verifies:
- Multiple agents execute in parallel via Send API
- Results are collected in state.retrieved_docs (append, not replace)
- Parallel execution is faster than sequential
- Timeout handling works correctly
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage
from langgraph.types import Send

from agent.graph import State, add_documents
from agent.mcp import MCPResponse
from agent.models.supervisor_models import IntentResult, IntentType
from agent.nodes.supervisor import supervisor_node

# =============================================================================
# Unit tests for add_documents reducer
# =============================================================================


class TestAddDocumentsReducer:
    """Tests for the add_documents reducer function."""

    def test_append_new_to_empty(self) -> None:
        """Test appending documents to empty list."""
        existing: list[Document] = []
        new = [Document(page_content="doc1", metadata={"source": "sukl"})]

        result = add_documents(existing, new)

        assert len(result) == 1
        assert result[0].page_content == "doc1"

    def test_append_new_to_existing(self) -> None:
        """Test appending documents to existing list."""
        existing = [Document(page_content="existing", metadata={"source": "sukl"})]
        new = [Document(page_content="new", metadata={"source": "cls_jep"})]

        result = add_documents(existing, new)

        assert len(result) == 2
        assert result[0].page_content == "existing"
        assert result[1].page_content == "new"

    def test_append_multiple_to_multiple(self) -> None:
        """Test appending multiple documents to multiple existing."""
        existing = [
            Document(page_content="doc1", metadata={"source": "sukl"}),
            Document(page_content="doc2", metadata={"source": "sukl"}),
        ]
        new = [
            Document(page_content="doc3", metadata={"source": "cls_jep"}),
            Document(page_content="doc4", metadata={"source": "pubmed"}),
        ]

        result = add_documents(existing, new)

        assert len(result) == 4
        sources = [doc.metadata["source"] for doc in result]
        assert sources == ["sukl", "sukl", "cls_jep", "pubmed"]

    def test_append_empty_to_existing(self) -> None:
        """Test appending empty list to existing documents."""
        existing = [Document(page_content="doc1", metadata={"source": "sukl"})]
        new: list[Document] = []

        result = add_documents(existing, new)

        assert len(result) == 1

    def test_both_empty(self) -> None:
        """Test appending empty to empty."""
        result = add_documents([], [])
        assert result == []


# =============================================================================
# Tests for supervisor_node Send API routing
# =============================================================================


class TestSupervisorNodeSendAPI:
    """Tests for supervisor_node returning Send commands."""

    @pytest.mark.asyncio
    async def test_single_agent_returns_single_send(
        self, mock_runtime: MagicMock
    ) -> None:
        """Test single agent query returns single Send command."""
        state = State(
            messages=[HumanMessage(content="Jaké je složení Ibalginu?")],
            next="__end__",
            retrieved_docs=[],
        )

        with patch("agent.nodes.supervisor.IntentClassifier") as mock_cls:
            mock_classifier = MagicMock()
            mock_classifier.classify_intent = AsyncMock(
                return_value=IntentResult(
                    intent_type=IntentType.DRUG_INFO,
                    confidence=0.95,
                    agents_to_call=["drug_agent"],
                    reasoning="Drug composition query",
                )
            )
            mock_cls.return_value = mock_classifier

            result = await supervisor_node(state, mock_runtime)

        assert isinstance(result, Send)
        assert result.node == "drug_agent"

    @pytest.mark.asyncio
    async def test_compound_query_returns_multiple_sends(
        self, mock_runtime: MagicMock
    ) -> None:
        """Test compound query returns list of Send commands for parallel execution."""
        state = State(
            messages=[HumanMessage(content="Metformin - guidelines a kontraindikace")],
            next="__end__",
            retrieved_docs=[],
        )

        with patch("agent.nodes.supervisor.IntentClassifier") as mock_cls:
            mock_classifier = MagicMock()
            mock_classifier.classify_intent = AsyncMock(
                return_value=IntentResult(
                    intent_type=IntentType.COMPOUND_QUERY,
                    confidence=0.92,
                    agents_to_call=["drug_agent", "guidelines_agent"],
                    reasoning="Compound query: drug info and guidelines",
                )
            )
            mock_cls.return_value = mock_classifier

            result = await supervisor_node(state, mock_runtime)

        assert isinstance(result, list)
        assert len(result) == 2
        node_names = {send.node for send in result}
        assert "drug_agent" in node_names
        assert "guidelines_agent" in node_names

    @pytest.mark.asyncio
    async def test_explicit_drug_query_returns_send(
        self, mock_runtime: MagicMock
    ) -> None:
        """Test explicit drug_query returns Send to drug_agent."""
        from agent.models.drug_models import DrugQuery, QueryType

        state = State(
            messages=[HumanMessage(content="anything")],
            next="__end__",
            retrieved_docs=[],
            drug_query=DrugQuery(query_text="Ibalgin", query_type=QueryType.SEARCH),
        )

        result = await supervisor_node(state, mock_runtime)

        assert isinstance(result, Send)
        assert result.node == "drug_agent"

    @pytest.mark.asyncio
    async def test_explicit_research_query_returns_send(
        self, mock_runtime: MagicMock
    ) -> None:
        """Test explicit research_query returns Send to pubmed_agent."""
        from agent.models.research_models import ResearchQuery

        state = State(
            messages=[HumanMessage(content="anything")],
            next="__end__",
            retrieved_docs=[],
            research_query=ResearchQuery(query_text="diabetes", query_type="search"),
        )

        result = await supervisor_node(state, mock_runtime)

        assert isinstance(result, Send)
        assert result.node == "pubmed_agent"

    @pytest.mark.asyncio
    async def test_explicit_guideline_query_returns_send(
        self, mock_runtime: MagicMock
    ) -> None:
        """Test explicit guideline_query returns Send to guidelines_agent."""
        from agent.models.guideline_models import GuidelineQuery, GuidelineQueryType

        state = State(
            messages=[HumanMessage(content="anything")],
            next="__end__",
            retrieved_docs=[],
            guideline_query=GuidelineQuery(
                query_text="hypertenze",
                query_type=GuidelineQueryType.SEARCH,
            ),
        )

        result = await supervisor_node(state, mock_runtime)

        assert isinstance(result, Send)
        assert result.node == "guidelines_agent"

    @pytest.mark.asyncio
    async def test_empty_messages_returns_general_agent_send(
        self, mock_runtime: MagicMock
    ) -> None:
        """Test empty messages returns Send to general_agent."""
        state = State(
            messages=[],
            next="__end__",
            retrieved_docs=[],
        )

        result = await supervisor_node(state, mock_runtime)

        assert isinstance(result, Send)
        assert result.node == "general_agent"

    @pytest.mark.asyncio
    async def test_classification_error_fallback_returns_send(
        self, mock_runtime: MagicMock
    ) -> None:
        """Test classification error fallback returns Send."""
        state = State(
            messages=[HumanMessage(content="Najdi lék Ibalgin")],
            next="__end__",
            retrieved_docs=[],
        )

        with patch("agent.nodes.supervisor.IntentClassifier") as mock_cls:
            mock_classifier = MagicMock()
            mock_classifier.classify_intent = AsyncMock(
                side_effect=Exception("API error")
            )
            mock_cls.return_value = mock_classifier

            result = await supervisor_node(state, mock_runtime)

        assert isinstance(result, Send)
        # "lék" keyword should route to drug_agent
        assert result.node == "drug_agent"

    @pytest.mark.asyncio
    async def test_out_of_scope_returns_general_agent_send(
        self, mock_runtime: MagicMock
    ) -> None:
        """Test out_of_scope intent returns Send to general_agent."""
        state = State(
            messages=[HumanMessage(content="Jaké je počasí?")],
            next="__end__",
            retrieved_docs=[],
        )

        with patch("agent.nodes.supervisor.IntentClassifier") as mock_cls:
            mock_classifier = MagicMock()
            mock_classifier.classify_intent = AsyncMock(
                return_value=IntentResult(
                    intent_type=IntentType.OUT_OF_SCOPE,
                    confidence=0.98,
                    agents_to_call=[],
                    reasoning="Non-medical query",
                )
            )
            mock_cls.return_value = mock_classifier

            result = await supervisor_node(state, mock_runtime)

        assert isinstance(result, Send)
        assert result.node == "general_agent"

    @pytest.mark.asyncio
    async def test_unavailable_agent_skipped_in_compound(
        self, mock_runtime: MagicMock
    ) -> None:
        """Test unavailable agent is skipped in compound query."""
        state = State(
            messages=[HumanMessage(content="Metformin - guidelines a studie")],
            next="__end__",
            retrieved_docs=[],
        )

        with patch("agent.nodes.supervisor.IntentClassifier") as mock_cls:
            mock_classifier = MagicMock()
            mock_classifier.classify_intent = AsyncMock(
                return_value=IntentResult(
                    intent_type=IntentType.COMPOUND_QUERY,
                    confidence=0.92,
                    agents_to_call=["drug_agent", "guidelines_agent"],
                    reasoning="Compound query",
                )
            )
            mock_cls.return_value = mock_classifier

            # SUKL client unavailable
            with patch(
                "agent.graph.get_mcp_clients",
                return_value=(None, None),
            ):
                result = await supervisor_node(state, mock_runtime)

        # drug_agent should be skipped, only guidelines_agent remains
        assert isinstance(result, Send)
        assert result.node == "guidelines_agent"

    @pytest.mark.asyncio
    async def test_all_agents_unavailable_returns_general_agent(
        self, mock_runtime: MagicMock
    ) -> None:
        """Test all MCP agents unavailable returns general_agent."""
        state = State(
            messages=[HumanMessage(content="Metformin - studie a léky")],
            next="__end__",
            retrieved_docs=[],
        )

        with patch("agent.nodes.supervisor.IntentClassifier") as mock_cls:
            mock_classifier = MagicMock()
            mock_classifier.classify_intent = AsyncMock(
                return_value=IntentResult(
                    intent_type=IntentType.COMPOUND_QUERY,
                    confidence=0.92,
                    agents_to_call=["drug_agent", "pubmed_agent"],
                    reasoning="Compound query",
                )
            )
            mock_cls.return_value = mock_classifier

            # Both MCP clients unavailable
            with patch(
                "agent.graph.get_mcp_clients",
                return_value=(None, None),
            ):
                result = await supervisor_node(state, mock_runtime)

        assert isinstance(result, Send)
        assert result.node == "general_agent"

    @pytest.mark.asyncio
    async def test_research_query_maps_to_translate_node(
        self, mock_runtime: MagicMock
    ) -> None:
        """Test pubmed_agent maps to pubmed_agent via AGENT_TO_NODE_MAP."""
        state = State(
            messages=[HumanMessage(content="Studie o diabetu")],
            next="__end__",
            retrieved_docs=[],
        )

        with patch("agent.nodes.supervisor.IntentClassifier") as mock_cls:
            mock_classifier = MagicMock()
            mock_classifier.classify_intent = AsyncMock(
                return_value=IntentResult(
                    intent_type=IntentType.RESEARCH_QUERY,
                    confidence=0.95,
                    agents_to_call=["pubmed_agent"],
                    reasoning="Research query",
                )
            )
            mock_cls.return_value = mock_classifier

            result = await supervisor_node(state, mock_runtime)

        assert isinstance(result, Send)
        assert result.node == "pubmed_agent"


# =============================================================================
# Tests for timeout wrapper
# =============================================================================


class TestTimeoutWrapper:
    """Tests for the with_timeout decorator."""

    @pytest.mark.asyncio
    async def test_normal_execution_within_timeout(self) -> None:
        """Test that normal execution completes within timeout."""
        from agent.utils.timeout import with_timeout

        @with_timeout(timeout_seconds=5.0)
        async def fast_agent() -> Dict[str, Any]:
            await asyncio.sleep(0.01)
            return {"messages": [{"role": "assistant", "content": "Done"}]}

        result = await fast_agent()
        assert result["messages"][0]["content"] == "Done"

    @pytest.mark.asyncio
    async def test_timeout_returns_degradation(self) -> None:
        """Test that timeout returns graceful degradation response."""
        from agent.utils.timeout import with_timeout

        @with_timeout(timeout_seconds=0.1)
        async def slow_agent() -> Dict[str, Any]:
            await asyncio.sleep(5.0)
            return {"messages": [{"role": "assistant", "content": "Never reached"}]}

        result = await slow_agent()

        assert "překročil časový limit" in result["messages"][0]["content"]
        assert result["retrieved_docs"] == []
        assert result["next"] == "__end__"

    @pytest.mark.asyncio
    async def test_timeout_preserves_function_name(self) -> None:
        """Test that wrapped function preserves original name."""
        from agent.utils.timeout import with_timeout

        @with_timeout(timeout_seconds=5.0)
        async def my_custom_agent() -> Dict[str, Any]:
            return {}

        assert my_custom_agent.__name__ == "my_custom_agent"

    @pytest.mark.asyncio
    async def test_timeout_message_contains_function_name(self) -> None:
        """Test timeout message includes the function name."""
        from agent.utils.timeout import with_timeout

        @with_timeout(timeout_seconds=0.1)
        async def named_agent() -> Dict[str, Any]:
            await asyncio.sleep(5.0)
            return {}

        result = await named_agent()

        assert "named_agent" in result["messages"][0]["content"]


# =============================================================================
# End-to-end integration tests for parallel execution via compiled graph
# =============================================================================


class TestEndToEndParallelExecution:
    """End-to-end tests invoking the compiled graph for compound queries.

    Verifies:
    - Both agents execute for compound queries
    - state.retrieved_docs contains documents from multiple sources (append, not replace)
    - Assistant messages include contributions from both agents
    - Parallel execution completes faster than sequential baseline
    """

    @staticmethod
    def _make_sukl_client() -> MagicMock:
        """Create mock SÚKL client with drug search/details responses."""
        client = MagicMock()

        async def call_tool_side_effect(
            tool_name: str, parameters: Dict[str, Any], retry_config: Any = None
        ) -> MCPResponse:
            if tool_name == "search_drugs":
                return MCPResponse(
                    success=True,
                    data={
                        "drugs": [
                            {
                                "name": "Metformin 500",
                                "atc_code": "A10BA02",
                                "registration_number": "58/001/01-C",
                                "manufacturer": "Zentiva",
                            }
                        ]
                    },
                )
            elif tool_name == "get_drug_details":
                return MCPResponse(
                    success=True,
                    data={
                        "registration_number": "58/001/01-C",
                        "name": "Metformin 500",
                        "active_ingredient": "metformini hydrochloridum",
                        "composition": ["metformini hydrochloridum 500 mg"],
                        "indications": ["Diabetes mellitus 2. typu"],
                        "contraindications": [
                            "Renální insuficience",
                            "Metabolická acidóza",
                        ],
                        "dosage": "500-1000 mg 2x denně",
                        "atc_code": "A10BA02",
                    },
                )
            return MCPResponse(success=False, error=f"Unknown tool: {tool_name}")

        client.call_tool = AsyncMock(side_effect=call_tool_side_effect)
        return client

    @staticmethod
    def _make_guideline_results() -> list[Dict[str, Any]]:
        """Create mock guideline search results."""
        return [
            {
                "id": 1,
                "guideline_id": "CLS-JEP-2024-001",
                "title": "Doporučené postupy pro diabetes",
                "section_name": "Kontraindikace metforminu",
                "content": "Hlavní kontraindikace metforminu zahrnují renální insuficienci a metabolickou acidózu.",
                "publication_date": "2024-01-15",
                "source": "cls_jep",
                "url": "https://www.cls.cz/guidelines/diabetes-2024.pdf",
                "metadata": {},
                "similarity_score": 0.85,
            }
        ]

    @pytest.mark.asyncio
    async def test_e2e_both_agents_execute(self, test_graph: Any) -> None:
        """Test compound query executes both drug and guidelines agents."""
        mock_sukl = self._make_sukl_client()
        mock_guidelines = self._make_guideline_results()

        with (
            patch("agent.nodes.supervisor.IntentClassifier") as mock_cls,
            patch("agent.graph.get_mcp_clients", return_value=(mock_sukl, None)),
            patch(
                "agent.nodes.guidelines_agent.search_guidelines_semantic",
                new_callable=AsyncMock,
                return_value=mock_guidelines,
            ),
        ):
            mock_classifier = MagicMock()
            mock_classifier.classify_intent = AsyncMock(
                return_value=IntentResult(
                    intent_type=IntentType.COMPOUND_QUERY,
                    confidence=0.92,
                    agents_to_call=["drug_agent", "guidelines_agent"],
                    reasoning="Compound query: drug info and guidelines",
                )
            )
            mock_cls.return_value = mock_classifier

            result = await test_graph.ainvoke(
                {
                    "messages": [
                        HumanMessage(content="Metformin - guidelines a kontraindikace")
                    ]
                },
            )

        # (a) Both agents ran - verified by documents from each source
        docs = result["retrieved_docs"]
        sources = {doc.metadata.get("source") for doc in docs}
        assert "sukl" in sources, "Drug agent should have produced SÚKL documents"
        assert "cls_jep" in sources, (
            "Guidelines agent should have produced CLS JEP documents"
        )

    @pytest.mark.asyncio
    async def test_e2e_docs_accumulate_from_multiple_sources(
        self, test_graph: Any
    ) -> None:
        """Test retrieved_docs accumulates documents (append, not replace)."""
        mock_sukl = self._make_sukl_client()
        mock_guidelines = self._make_guideline_results()

        with (
            patch("agent.nodes.supervisor.IntentClassifier") as mock_cls,
            patch("agent.graph.get_mcp_clients", return_value=(mock_sukl, None)),
            patch(
                "agent.nodes.guidelines_agent.search_guidelines_semantic",
                new_callable=AsyncMock,
                return_value=mock_guidelines,
            ),
        ):
            mock_classifier = MagicMock()
            mock_classifier.classify_intent = AsyncMock(
                return_value=IntentResult(
                    intent_type=IntentType.COMPOUND_QUERY,
                    confidence=0.92,
                    agents_to_call=["drug_agent", "guidelines_agent"],
                    reasoning="Compound query",
                )
            )
            mock_cls.return_value = mock_classifier

            result = await test_graph.ainvoke(
                {
                    "messages": [
                        HumanMessage(content="Metformin - guidelines a kontraindikace")
                    ]
                },
            )

        # Documents should accumulate from BOTH agents, not just the last one
        docs = result["retrieved_docs"]
        sukl_docs = [d for d in docs if d.metadata.get("source") == "sukl"]
        guideline_docs = [d for d in docs if d.metadata.get("source") == "cls_jep"]
        assert len(sukl_docs) >= 1, "Should have at least 1 SÚKL document"
        assert len(guideline_docs) >= 1, "Should have at least 1 guideline document"
        assert len(docs) >= 2, (
            "Total docs should be sum from both agents (append, not replace)"
        )

    @pytest.mark.asyncio
    async def test_e2e_messages_from_both_agents(self, test_graph: Any) -> None:
        """Test assistant messages include contributions from both agents."""
        mock_sukl = self._make_sukl_client()
        mock_guidelines = self._make_guideline_results()

        with (
            patch("agent.nodes.supervisor.IntentClassifier") as mock_cls,
            patch("agent.graph.get_mcp_clients", return_value=(mock_sukl, None)),
            patch(
                "agent.nodes.guidelines_agent.search_guidelines_semantic",
                new_callable=AsyncMock,
                return_value=mock_guidelines,
            ),
        ):
            mock_classifier = MagicMock()
            mock_classifier.classify_intent = AsyncMock(
                return_value=IntentResult(
                    intent_type=IntentType.COMPOUND_QUERY,
                    confidence=0.92,
                    agents_to_call=["drug_agent", "guidelines_agent"],
                    reasoning="Compound query",
                )
            )
            mock_cls.return_value = mock_classifier

            result = await test_graph.ainvoke(
                {
                    "messages": [
                        HumanMessage(content="Metformin - guidelines a kontraindikace")
                    ]
                },
            )

        # Collect all assistant message contents
        messages = result["messages"]
        assistant_contents = []
        for m in messages:
            content = m.content if hasattr(m, "content") else m.get("content", "")
            msg_type = getattr(m, "type", None) or m.get("role", "")
            if msg_type in ("assistant", "ai"):
                assistant_contents.append(content)

        all_text = " ".join(assistant_contents)

        # Drug agent includes SÚKL source citation or drug-related info
        has_drug_content = any(
            term in all_text for term in ["SÚKL", "Metformin", "A10BA02", "lék"]
        )
        # Guidelines agent includes guidelines-related info
        has_guideline_content = any(
            term in all_text
            for term in ["guidelines", "Guidelines", "ČLS JEP", "doporučen"]
        )

        assert has_drug_content, (
            f"Messages should include drug agent content. Got: {all_text[:500]}"
        )
        assert has_guideline_content, (
            f"Messages should include guidelines agent content. Got: {all_text[:500]}"
        )

    @pytest.mark.asyncio
    async def test_e2e_parallel_faster_than_sequential(self, test_graph: Any) -> None:
        """Test parallel execution completes faster than sequential baseline."""
        AGENT_DELAY = 0.3  # seconds each external call sleeps

        # Create mock SÚKL client with artificial delay
        mock_sukl = MagicMock()

        async def slow_sukl_call(
            tool_name: str,
            parameters: Dict[str, Any],
            retry_config: Any = None,
        ) -> MCPResponse:
            await asyncio.sleep(AGENT_DELAY)
            if tool_name == "search_drugs":
                return MCPResponse(
                    success=True,
                    data={
                        "drugs": [
                            {
                                "name": "Metformin 500",
                                "atc_code": "A10BA02",
                                "registration_number": "58/001/01-C",
                                "manufacturer": "Zentiva",
                            }
                        ]
                    },
                )
            elif tool_name == "get_drug_details":
                return MCPResponse(
                    success=True,
                    data={
                        "registration_number": "58/001/01-C",
                        "name": "Metformin 500",
                        "active_ingredient": "metformini hydrochloridum",
                        "composition": ["metformini hydrochloridum 500 mg"],
                        "indications": ["Diabetes mellitus 2. typu"],
                        "contraindications": ["Renální insuficience"],
                        "dosage": "500-1000 mg 2x denně",
                        "atc_code": "A10BA02",
                    },
                )
            return MCPResponse(success=False, error=f"Unknown tool: {tool_name}")

        mock_sukl.call_tool = AsyncMock(side_effect=slow_sukl_call)

        # Create mock guidelines search with artificial delay
        mock_guideline_results = self._make_guideline_results()

        async def slow_guidelines_search(
            query: Any, runtime: Any
        ) -> list[Dict[str, Any]]:
            await asyncio.sleep(AGENT_DELAY)
            return mock_guideline_results

        with (
            patch("agent.nodes.supervisor.IntentClassifier") as mock_cls,
            patch("agent.graph.get_mcp_clients", return_value=(mock_sukl, None)),
            patch(
                "agent.nodes.guidelines_agent.search_guidelines_semantic",
                side_effect=slow_guidelines_search,
            ),
        ):
            mock_classifier = MagicMock()
            mock_classifier.classify_intent = AsyncMock(
                return_value=IntentResult(
                    intent_type=IntentType.COMPOUND_QUERY,
                    confidence=0.92,
                    agents_to_call=["drug_agent", "guidelines_agent"],
                    reasoning="Compound query",
                )
            )
            mock_cls.return_value = mock_classifier

            start = time.monotonic()
            result = await test_graph.ainvoke(
                {
                    "messages": [
                        HumanMessage(content="Metformin - guidelines a kontraindikace")
                    ]
                },
            )
            elapsed = time.monotonic() - start

        # Drug agent makes 2 sequential calls (search + details), each 0.3s = 0.6s
        # Guidelines agent makes 1 call, 0.3s
        # Sequential baseline: 0.6 + 0.3 = 0.9s
        # Parallel: max(0.6, 0.3) = 0.6s + overhead
        sequential_baseline = AGENT_DELAY * 3  # 0.9s

        assert elapsed < sequential_baseline, (
            f"Parallel execution ({elapsed:.3f}s) should be faster than "
            f"sequential baseline ({sequential_baseline:.1f}s)"
        )

        # Verify both agents actually ran
        docs = result["retrieved_docs"]
        sources = {doc.metadata.get("source") for doc in docs}
        assert len(sources) >= 2, "Both agents should have contributed documents"
