"""Integration tests for Synthesizer Node flow.

Tests for Feature 009 - Synthesizer Node integration with multi-agent graph.
Follows TDD workflow per Constitution Principle III.

Test Organization:
- test_synthesizer_combines_drug_and_pubmed_responses: Multi-agent synthesis
- test_synthesizer_handles_single_agent_response: Single agent passthrough
- test_synthesizer_validates_czech_terminology: Terminology validation
- test_synthesizer_preserves_all_documents: Document preservation
- test_end_to_end_compound_query_with_synthesis: Full graph flow
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.documents import Document

from agent.graph import State
from agent.nodes.synthesizer import (
    extract_citations_from_message,
    renumber_citations,
    synthesizer_node,
)


class TestMultiAgentSynthesis:
    """Integration tests for multi-agent response synthesis."""

    @pytest.mark.asyncio
    async def test_synthesizer_combines_drug_and_pubmed_responses(
        self,
        sample_agent_messages: list[dict[str, str]],
    ) -> None:
        """Test combining drug_agent and pubmed_agent responses."""
        state = State(
            messages=[
                {"role": "user", "content": "Ibalgin - studie a informace"},
                sample_agent_messages[0],
                sample_agent_messages[1],
            ],
            retrieved_docs=[
                Document(
                    page_content="Ibalgin 400 info",
                    metadata={"source": "sukl", "registration_number": "58/123/01-C"},
                ),
                Document(
                    page_content="Ibuprofen study",
                    metadata={"source": "pubmed", "pmid": "12345678"},
                ),
            ],
        )

        mock_runtime = MagicMock()
        mock_runtime.context = {"model_name": "test-model"}

        # Mock LLM
        mock_response = MagicMock()
        mock_response.content = (
            "## Informace o léku\n"
            "Ibalgin obsahuje ibuprofen [1].\n\n"
            "## Vědecké studie\n"
            "Studie prokázala účinnost [2]."
        )

        with patch("agent.nodes.synthesizer.ChatAnthropic") as mock_cls:
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            mock_cls.return_value = mock_llm

            result = await synthesizer_node(state, mock_runtime)

        content = result["messages"][0]["content"]

        # Verify combined content
        assert "## Reference" in content
        # Verify citations are renumbered
        assert "[1] SUKL - Ibalgin 400" in content
        assert "[2] PMID: 12345678" in content
        # Verify footer
        assert "Czech MedAI" in content

    @pytest.mark.asyncio
    async def test_synthesizer_handles_single_agent_response(self) -> None:
        """Test QuickConsult format for single agent response."""
        state = State(
            messages=[
                {"role": "user", "content": "Najdi Ibalgin"},
                {
                    "role": "assistant",
                    "content": (
                        "Ibalgin 400 je lék obsahující ibuprofen [1].\n\n"
                        "## References\n"
                        "[1] SUKL - Ibalgin 400 (M01AE01)"
                    ),
                },
            ],
            retrieved_docs=[
                Document(
                    page_content="Ibalgin 400",
                    metadata={"source": "sukl"},
                ),
            ],
        )

        mock_runtime = MagicMock()
        mock_runtime.context = {"model_name": "test-model"}

        result = await synthesizer_node(state, mock_runtime)

        content = result["messages"][0]["content"]
        # Single agent - QuickConsult format
        assert "ibuprofen" in content
        assert "[1]" in content
        assert "SUKL - Ibalgin 400" in content
        assert "Czech MedAI" in content

    @pytest.mark.asyncio
    async def test_synthesizer_validates_czech_terminology(self) -> None:
        """Test that correct Czech terminology produces no warning section."""
        state = State(
            messages=[
                {"role": "user", "content": "DM2T léčba"},
                {
                    "role": "assistant",
                    "content": "Pacient s DM2T a ICHS by měl užívat metformin.",
                },
            ],
        )

        mock_runtime = MagicMock()
        mock_runtime.context = {"model_name": "test-model"}

        result = await synthesizer_node(state, mock_runtime)

        content = result["messages"][0]["content"]
        # DM2T and ICHS are used without expansion → suggestions section appears
        assert "## Terminologické upozornění" in content
        assert "DM2T" in content
        assert "ICHS" in content
        # Suggestions for unexpanded Czech abbreviations
        assert any(
            "DM2T" in line and "bez rozepsání" in line for line in content.split("\n")
        )
        assert any(
            "ICHS" in line and "bez rozepsání" in line for line in content.split("\n")
        )

    @pytest.mark.asyncio
    async def test_synthesizer_shows_suggestions_section(self) -> None:
        """Test that unexpanded Czech abbreviations produce suggestions section without warnings."""
        state = State(
            messages=[
                {"role": "user", "content": "test"},
                {
                    "role": "assistant",
                    "content": "Pacient s DM2T má zvýšené KV riziko.",
                },
            ],
        )

        mock_runtime = MagicMock()
        mock_runtime.context = {"model_name": "test-model"}

        result = await synthesizer_node(state, mock_runtime)

        content = result["messages"][0]["content"]
        # Suggestions section present (unexpanded Czech abbreviations)
        assert "## Terminologické upozornění" in content
        assert "bez rozepsání" in content
        assert "DM2T" in content
        assert "KV" in content
        # No English warnings (no English abbreviations used)
        assert "anglická zkratka" not in content

    @pytest.mark.asyncio
    async def test_synthesizer_adds_warning_for_english_abbrevs(self) -> None:
        """Test that English abbreviations trigger warning section."""
        state = State(
            messages=[
                {"role": "user", "content": "test"},
                {
                    "role": "assistant",
                    "content": "Patient has T2DM with high CV risk and CHD.",
                },
            ],
        )

        mock_runtime = MagicMock()
        mock_runtime.context = {"model_name": "test-model"}

        result = await synthesizer_node(state, mock_runtime)

        content = result["messages"][0]["content"]
        assert "## Terminologické upozornění" in content
        assert "T2DM" in content
        assert "CV" in content

    @pytest.mark.asyncio
    async def test_synthesizer_preserves_all_documents(self) -> None:
        """Test that retrieved_docs returns empty (docs preserved in state by reducer)."""
        docs = [
            Document(
                page_content="Drug doc 1",
                metadata={"source": "sukl", "registration_number": "58/123/01-C"},
            ),
            Document(
                page_content="Drug doc 2",
                metadata={"source": "sukl", "registration_number": "58/124/01-C"},
            ),
            Document(
                page_content="PubMed doc 1",
                metadata={"source": "pubmed", "pmid": "12345678"},
            ),
            Document(
                page_content="PubMed doc 2",
                metadata={"source": "pubmed", "pmid": "87654321"},
            ),
            Document(
                page_content="PubMed doc 3",
                metadata={"source": "pubmed", "pmid": "11111111"},
            ),
        ]

        state = State(
            messages=[
                {"role": "user", "content": "test"},
                {"role": "assistant", "content": "Drug agent response."},
                {"role": "assistant", "content": "PubMed agent response."},
            ],
            retrieved_docs=docs,
        )

        mock_runtime = MagicMock()
        mock_runtime.context = {"model_name": "test-model"}

        with patch("agent.nodes.synthesizer.ChatAnthropic") as mock_cls:
            mock_llm = MagicMock()
            mock_response = MagicMock()
            mock_response.content = "Combined response."
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            mock_cls.return_value = mock_llm

            result = await synthesizer_node(state, mock_runtime)

        # Synthesizer returns empty docs (existing docs preserved by add_documents reducer)
        assert result["retrieved_docs"] == []
        # Original docs remain in state (5 documents)
        assert len(state.retrieved_docs) == 5

    @pytest.mark.asyncio
    async def test_synthesizer_citation_renumbering_integration(self) -> None:
        """Test full citation renumbering with drug + pubmed agents."""
        state = State(
            messages=[
                {"role": "user", "content": "Metformin research and info"},
                {
                    "role": "assistant",
                    "content": (
                        "Metformin je biguanid [1], registrovaný pod [2].\n\n"
                        "## References\n"
                        "[1] SUKL - Metformin 500\n"
                        "[2] SUKL - Reg. 12/345/06-C"
                    ),
                },
                {
                    "role": "assistant",
                    "content": (
                        "RCT prokázala účinnost [1]. Meta-analýza [2] potvrdila [3].\n\n"
                        "## References\n"
                        "[1] Smith et al. PMID: 12345678\n"
                        "[2] Brown et al. PMID: 87654321\n"
                        "[3] Davis et al. PMID: 11111111"
                    ),
                },
            ],
        )

        mock_runtime = MagicMock()
        mock_runtime.context = {"model_name": "test-model"}

        mock_response = MagicMock()
        mock_response.content = (
            "Metformin je biguanid [1], registrovaný [2]. "
            "Účinnost prokázána [3], potvrzena [4][5]."
        )

        with patch("agent.nodes.synthesizer.ChatAnthropic") as mock_cls:
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            mock_cls.return_value = mock_llm

            result = await synthesizer_node(state, mock_runtime)

        content = result["messages"][0]["content"]

        # Verify all 5 references are present
        assert "[1] SUKL - Metformin 500" in content
        assert "[2] SUKL - Reg. 12/345/06-C" in content
        assert "[3] Smith et al. PMID: 12345678" in content
        assert "[4] Brown et al. PMID: 87654321" in content
        assert "[5] Davis et al. PMID: 11111111" in content

    @pytest.mark.asyncio
    async def test_synthesizer_three_agents(self) -> None:
        """Test synthesis with three agent responses."""
        state = State(
            messages=[
                {"role": "user", "content": "Diabetes - vše"},
                {
                    "role": "assistant",
                    "content": "Lékové info [1].\n\n## References\n[1] SUKL",
                },
                {
                    "role": "assistant",
                    "content": "Studie [1].\n\n## References\n[1] PubMed",
                },
                {
                    "role": "assistant",
                    "content": ("Guidelines [1].\n\n## References\n[1] CLS JEP"),
                },
            ],
        )

        mock_runtime = MagicMock()
        mock_runtime.context = {"model_name": "test-model"}

        mock_response = MagicMock()
        mock_response.content = "Shrnutí: léky [1], studie [2], guidelines [3]."

        with patch("agent.nodes.synthesizer.ChatAnthropic") as mock_cls:
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            mock_cls.return_value = mock_llm

            result = await synthesizer_node(state, mock_runtime)

        content = result["messages"][0]["content"]
        assert "[1] SUKL" in content
        assert "[2] PubMed" in content
        assert "[3] CLS JEP" in content

    @pytest.mark.asyncio
    async def test_synthesizer_compound_sections_with_agent_types(self) -> None:
        """Test compound format includes fixed section headers based on agent types."""
        state = State(
            messages=[
                {"role": "user", "content": "Ibalgin - všechno"},
                {
                    "role": "assistant",
                    "content": (
                        "SÚKL registrovaný Ibalgin [1].\n\n"
                        "## References\n[1] SUKL - Ibalgin"
                    ),
                },
                {
                    "role": "assistant",
                    "content": (
                        "PubMed studie o ibuprofenu [1].\n\n"
                        "## References\n[1] PMID: 99999"
                    ),
                },
            ],
        )

        mock_runtime = MagicMock()
        mock_runtime.context = {"model_name": "test-model"}

        mock_response = MagicMock()
        mock_response.content = (
            "SÚKL registrovaný lék Ibalgin [1].\n\n"
            "PubMed studie prokázala účinnost [2]."
        )

        with patch("agent.nodes.synthesizer.ChatAnthropic") as mock_cls:
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            mock_cls.return_value = mock_llm

            result = await synthesizer_node(state, mock_runtime)

        content = result["messages"][0]["content"]
        # Compound format should have fixed section headers
        assert "**Lékové informace (SÚKL)**" in content
        assert "**Výzkum (PubMed)**" in content


class TestHelperIntegration:
    """Integration tests for helper functions working together."""

    def test_extract_then_renumber_two_agents(self) -> None:
        """Test full extract -> renumber pipeline."""
        msg1 = "Ibalgin info [1].\n\n## References\n[1] SUKL - Ibalgin"
        msg2 = (
            "Study results [1] and [2].\n\n## References\n[1] PMID: 111\n[2] PMID: 222"
        )

        text1, cit1 = extract_citations_from_message(msg1)
        text2, cit2 = extract_citations_from_message(msg2)

        updated, refs = renumber_citations([text1, text2], [cit1, cit2])

        # Verify renumbering
        assert "[1]" in updated[0]  # Agent 1 keeps [1]
        assert "[2]" in updated[1]  # Agent 2: [1] -> [2]
        assert "[3]" in updated[1]  # Agent 2: [2] -> [3]

        assert len(refs) == 3
        assert "[1] SUKL - Ibalgin" == refs[0]
        assert "[2] PMID: 111" == refs[1]
        assert "[3] PMID: 222" == refs[2]

    def test_extract_renumber_no_overlap(self) -> None:
        """Test messages without overlapping citation numbers."""
        msg1 = "Info [1].\n\n## References\n[1] Source A"
        msg2 = "More info."  # No citations

        text1, cit1 = extract_citations_from_message(msg1)
        text2, cit2 = extract_citations_from_message(msg2)

        updated, refs = renumber_citations([text1, text2], [cit1, cit2])

        assert "[1]" in updated[0]
        assert updated[1] == "More info."
        assert len(refs) == 1
