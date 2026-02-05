"""Unit tests for Synthesizer Node.

Tests for Feature 009 - Synthesizer Node implementation.
Follows TDD workflow per Constitution Principle III.

Test Organization:
- TestCitationExtraction: Citation parsing from agent messages
- TestCitationRenumbering: Global citation renumbering across agents
- TestCzechTerminologyValidation: Czech medical abbreviation validation
- TestResponseFormatting: Response formatting for different query types
- TestAgentTypeDetection: Agent type detection from message content
- TestSynthesizerNode: Main node function tests
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent.graph import State
from agent.nodes.synthesizer import (
    CitationInfo,
    _detect_agent_types,
    _structure_compound_response,
    extract_citations_from_message,
    format_response,
    renumber_citations,
    synthesizer_node,
    validate_czech_terminology,
)

# =============================================================================
# TestCitationExtraction
# =============================================================================


class TestCitationExtraction:
    """Test citation extraction from agent messages."""

    def test_extract_citations_from_single_agent_message(self) -> None:
        """Test parsing [1][2] and References section from message."""
        message = (
            "Ibalgin obsahuje ibuprofen [1]. Je to lék skupiny NSAID [2].\n\n"
            "## References\n"
            "[1] SUKL - Ibalgin 400\n"
            "[2] SUKL - ATC M01AE01"
        )

        msg_text, citations = extract_citations_from_message(message)

        assert "[1]" in msg_text
        assert "[2]" in msg_text
        assert "## References" not in msg_text
        assert len(citations) == 2
        assert citations[0].original_num == 1
        assert "SUKL - Ibalgin 400" in citations[0].citation_text
        assert citations[1].original_num == 2
        assert "ATC M01AE01" in citations[1].citation_text

    def test_extract_citations_handles_no_references(self) -> None:
        """Test message without citations returns empty list."""
        message = "Ibalgin je lék obsahující ibuprofen. Používá se proti bolesti."

        msg_text, citations = extract_citations_from_message(message)

        assert msg_text == message
        assert citations == []

    def test_extract_citations_handles_malformed_references(self) -> None:
        """Test message with non-standard reference format."""
        message = "Lék je dostupný.\n\n_Zdroj: SUKL - Státní ústav pro kontrolu léčiv_"

        msg_text, citations = extract_citations_from_message(message)

        assert "SUKL" not in msg_text or "Zdroj" not in msg_text
        assert len(citations) == 1
        assert "SUKL" in citations[0].citation_text

    def test_extract_citations_with_urls(self) -> None:
        """Test extraction of URLs from citations."""
        message = (
            "Studie prokázala účinnost [1].\n\n"
            "## References\n"
            "[1] Smith et al. 2024 - PMID: 12345678"
        )

        _, citations = extract_citations_from_message(message)

        assert len(citations) == 1
        assert "PMID: 12345678" in citations[0].url

    def test_extract_citations_with_doi(self) -> None:
        """Test extraction of DOI from citations."""
        message = (
            "Výsledky jsou pozitivní [1].\n\n"
            "## References\n"
            "[1] Smith et al. doi: 10.1056/NEJMoa2401234"
        )

        _, citations = extract_citations_from_message(message)

        assert len(citations) == 1
        assert "doi: 10.1056/NEJMoa2401234" in citations[0].url

    def test_extract_citations_czech_header(self) -> None:
        """Test extraction with Czech 'Zdroje' header."""
        message = "Informace o léku [1].\n\n## Zdroje\n[1] SUKL databáze"

        msg_text, citations = extract_citations_from_message(message)

        assert "## Zdroje" not in msg_text
        assert len(citations) == 1


# =============================================================================
# TestCitationRenumbering
# =============================================================================


class TestCitationRenumbering:
    """Test global citation renumbering across multiple agents."""

    def test_renumber_citations_from_two_agents(self) -> None:
        """Test drug [1][2] + pubmed [1][2] -> [1][2][3][4]."""
        messages = [
            "Drug info: Ibalgin [1] a Paralen [2].",
            "Studie o ibuprofenu [1] a paracetamolu [2].",
        ]
        citations = [
            [
                CitationInfo(1, "SUKL - Ibalgin 400"),
                CitationInfo(2, "SUKL - Paralen 500"),
            ],
            [
                CitationInfo(1, "PMID: 12345678"),
                CitationInfo(2, "PMID: 87654321"),
            ],
        ]

        updated, refs = renumber_citations(messages, citations)

        # First agent keeps [1][2]
        assert "[1]" in updated[0]
        assert "[2]" in updated[0]
        # Second agent gets [3][4]
        assert "[3]" in updated[1]
        assert "[4]" in updated[1]
        # Global references
        assert len(refs) == 4
        assert "[1] SUKL - Ibalgin 400" in refs[0]
        assert "[4] PMID: 87654321" in refs[3]

    def test_renumber_citations_updates_inline_refs(self) -> None:
        """Test that inline [1] -> [3] is updated correctly in text."""
        messages = [
            "First agent [1].",
            "Second agent mentions [1] and [2].",
        ]
        citations = [
            [CitationInfo(1, "Source A")],
            [CitationInfo(1, "Source B"), CitationInfo(2, "Source C")],
        ]

        updated, _ = renumber_citations(messages, citations)

        assert "First agent [1]." == updated[0]
        assert "Second agent mentions [2] and [3]." == updated[1]

    def test_renumber_citations_preserves_order(self) -> None:
        """Test that citation order is preserved across agents."""
        messages = ["A [1].", "B [1] [2].", "C [1]."]
        citations = [
            [CitationInfo(1, "Ref-A1")],
            [CitationInfo(1, "Ref-B1"), CitationInfo(2, "Ref-B2")],
            [CitationInfo(1, "Ref-C1")],
        ]

        _, refs = renumber_citations(messages, citations)

        assert len(refs) == 4
        assert refs[0] == "[1] Ref-A1"
        assert refs[1] == "[2] Ref-B1"
        assert refs[2] == "[3] Ref-B2"
        assert refs[3] == "[4] Ref-C1"

    def test_renumber_citations_empty_citations(self) -> None:
        """Test renumbering with agent having no citations."""
        messages = ["No citations here.", "Has citation [1]."]
        citations = [
            [],
            [CitationInfo(1, "Source X")],
        ]

        updated, refs = renumber_citations(messages, citations)

        assert updated[0] == "No citations here."
        assert "[1]" in updated[1]
        assert len(refs) == 1

    def test_renumber_citations_single_agent(self) -> None:
        """Test renumbering with single agent (no renumbering needed)."""
        messages = ["Info [1] a [2]."]
        citations = [
            [CitationInfo(1, "Ref A"), CitationInfo(2, "Ref B")],
        ]

        updated, refs = renumber_citations(messages, citations)

        assert "[1]" in updated[0]
        assert "[2]" in updated[0]
        assert len(refs) == 2


# =============================================================================
# TestCzechTerminologyValidation
# =============================================================================


class TestCzechTerminologyValidation:
    """Test Czech medical terminology validation."""

    def test_validate_czech_terminology_correct_returns_dict(self) -> None:
        """Test that correct Czech abbreviations produce empty warnings/suggestions."""
        text = "Pacient s DM2T (diabetes mellitus 2. typu) a ICHS (ischemická choroba srdeční)."
        result = validate_czech_terminology(text)
        assert isinstance(result, dict)
        assert "warnings" in result
        assert "suggestions" in result
        assert result["warnings"] == []

    def test_validate_czech_terminology_warns_on_english(self) -> None:
        """Test that English abbreviations produce warnings."""
        text = "Patient with T2DM and CHD has high CV risk."
        result = validate_czech_terminology(text)

        assert len(result["warnings"]) >= 3
        assert any("T2DM" in w for w in result["warnings"])
        assert any("CHD" in w for w in result["warnings"])
        assert any("CV" in w for w in result["warnings"])

    def test_validate_czech_terminology_handles_mixed(self) -> None:
        """Test mix of correct Czech and incorrect English abbreviations."""
        text = "Pacient s DM2T (diabetes mellitus 2. typu) (T2DM v anglické literatuře) a ICHS (ischemická choroba srdeční)."
        result = validate_czech_terminology(text)

        # Should warn about T2DM but not DM2T or ICHS
        assert len(result["warnings"]) == 1
        assert "T2DM" in result["warnings"][0]

    def test_validate_czech_terminology_empty_text(self) -> None:
        """Test empty text produces empty dict."""
        result = validate_czech_terminology("")
        assert result == {"warnings": [], "suggestions": []}

    def test_validate_czech_terminology_no_abbreviations(self) -> None:
        """Test text without any medical abbreviations."""
        text = "Pacient se cítí dobře po léčbě."
        result = validate_czech_terminology(text)
        assert result["warnings"] == []
        assert result["suggestions"] == []

    def test_validate_czech_terminology_suggests_expansion(self) -> None:
        """Test Czech abbreviation without expansion produces suggestion."""
        text = "Pacient s DM2T a ICHS má vysoký KV rizikový profil."
        result = validate_czech_terminology(text)

        # All three abbreviations are used without expansion
        assert len(result["suggestions"]) >= 3
        assert any("DM2T" in s for s in result["suggestions"])
        assert any("ICHS" in s for s in result["suggestions"])
        assert any("KV" in s for s in result["suggestions"])

    def test_validate_czech_terminology_no_suggestion_with_expansion(self) -> None:
        """Test Czech abbreviation with expansion produces no suggestion."""
        text = "Pacient s DM2T (diabetes mellitus 2. typu) byl léčen."
        result = validate_czech_terminology(text)

        # DM2T has expansion, so no suggestion for it
        assert not any("DM2T" in s for s in result["suggestions"])


# =============================================================================
# TestResponseFormatting
# =============================================================================


class TestResponseFormatting:
    """Test response formatting for different query types."""

    def test_format_response_quick_adds_footer(self) -> None:
        """Test quick format adds footer."""
        text = "Ibalgin je lék ze skupiny NSAID obsahující ibuprofen."
        result = format_response(text, "quick")

        assert text in result
        assert "Czech MedAI" in result
        assert "---" in result

    def test_format_response_quick_enforces_brevity(self) -> None:
        """Test quick format truncates to max 5 sentences."""
        sentences = [f"Věta číslo {i}." for i in range(1, 9)]
        text = " ".join(sentences)
        result = format_response(text, "quick")

        # Should contain first 5 sentences but not all 8
        assert "Věta číslo 1." in result
        assert "Věta číslo 5." in result
        assert "Věta číslo 6." not in result
        assert "Czech MedAI" in result

    def test_format_response_quick_preserves_short_text(self) -> None:
        """Test quick format preserves text with <= 5 sentences."""
        text = "Věta jedna. Věta dvě. Věta tři."
        result = format_response(text, "quick")

        assert "Věta jedna." in result
        assert "Věta dvě." in result
        assert "Věta tři." in result

    def test_format_response_compound_with_agent_types(self) -> None:
        """Test compound format uses fixed section headers."""
        text = (
            "## Informace o léku\n"
            "Ibalgin je SUKL registrovaný lék [1].\n\n"
            "## Vědecké studie\n"
            "PubMed studie prokázala účinnost [2]."
        )
        result = format_response(text, "compound", ["drug_agent", "pubmed_agent"])

        assert "**Lékové informace (SÚKL)**" in result
        assert "**Výzkum (PubMed)**" in result
        assert "Czech MedAI" in result

    def test_format_response_compound_without_agent_types(self) -> None:
        """Test compound format without agent_types falls through."""
        text = "### Léková informace\nIbalgin 400.\n\n### Studie\nÚčinnost prokázána."
        result = format_response(text, "compound")

        assert text in result
        assert "Czech MedAI" in result

    def test_format_response_adds_footer(self) -> None:
        """Test footer contains timestamp and disclaimer."""
        text = "Testovací odpověď."
        result = format_response(text, "quick")

        assert "Odpověď vygenerována:" in result
        assert "klinický rozhodovací nástroj" in result

    def test_format_response_preserves_content(self) -> None:
        """Test that original content is preserved."""
        text = "Důležitá informace [1] a další [2]."
        result = format_response(text, "compound")

        assert "[1]" in result
        assert "[2]" in result


# =============================================================================
# TestAgentTypeDetection
# =============================================================================


class TestAgentTypeDetection:
    """Test agent type detection from message content."""

    def test_detect_drug_agent(self) -> None:
        """Test detection of drug agent from SUKL keywords."""
        messages = [
            {"role": "assistant", "content": "Ibalgin je SÚKL registrovaný lék."},
        ]
        agent_types = _detect_agent_types(messages)
        assert "drug_agent" in agent_types

    def test_detect_pubmed_agent(self) -> None:
        """Test detection of PubMed agent from PMID keywords."""
        messages = [
            {"role": "assistant", "content": "Studie PMID: 12345678 prokázala."},
        ]
        agent_types = _detect_agent_types(messages)
        assert "pubmed_agent" in agent_types

    def test_detect_guidelines_agent(self) -> None:
        """Test detection of guidelines agent from ČLS JEP keywords."""
        messages = [
            {"role": "assistant", "content": "Doporučený postup ČLS JEP pro DM2T."},
        ]
        agent_types = _detect_agent_types(messages)
        assert "guidelines_agent" in agent_types

    def test_detect_multiple_agents(self) -> None:
        """Test detection of multiple agent types from multiple messages."""
        messages = [
            {"role": "assistant", "content": "SÚKL info o léku."},
            {"role": "assistant", "content": "PubMed studie prokázala."},
        ]
        agent_types = _detect_agent_types(messages)
        assert "drug_agent" in agent_types
        assert "pubmed_agent" in agent_types

    def test_detect_no_agents_generic_text(self) -> None:
        """Test generic text detects no specific agent types."""
        messages = [
            {
                "role": "assistant",
                "content": "Obecná odpověď bez specifických klíčových slov.",
            },
        ]
        agent_types = _detect_agent_types(messages)
        assert agent_types == []


# =============================================================================
# TestStructureCompoundResponse
# =============================================================================


class TestStructureCompoundResponse:
    """Test compound response structuring."""

    def test_structure_with_sukl_and_pubmed(self) -> None:
        """Test structuring with drug and pubmed sections."""
        text = (
            "Ibalgin je SUKL registrovaný lék.\n\n"
            "PubMed studie prokázala účinnost ibuprofenu."
        )
        result = _structure_compound_response(text, ["drug_agent", "pubmed_agent"])

        assert "**Lékové informace (SÚKL)**" in result
        assert "**Výzkum (PubMed)**" in result

    def test_structure_fallback_no_keywords(self) -> None:
        """Test fallback when no keywords match."""
        text = "Obecná odpověď bez specifických klíčových slov."
        result = _structure_compound_response(text, ["drug_agent"])

        # Falls through to original text since no keywords matched
        assert "Obecná odpověď" in result

    def test_structure_with_three_agents(self) -> None:
        """Test structuring with three agent types."""
        text = (
            "SÚKL info o léku.\n\n"
            "PubMed studie prokázala.\n\n"
            "ČLS JEP doporučení pro léčbu."
        )
        result = _structure_compound_response(
            text, ["drug_agent", "pubmed_agent", "guidelines_agent"]
        )

        assert "**Lékové informace (SÚKL)**" in result
        assert "**Výzkum (PubMed)**" in result
        assert "**Doporučení (Guidelines)**" in result


# =============================================================================
# TestSynthesizerNode
# =============================================================================


class TestSynthesizerNode:
    """Test main synthesizer_node function."""

    @pytest.mark.asyncio
    async def test_synthesizer_handles_no_agent_messages(
        self, sample_state: State
    ) -> None:
        """Test synthesizer with no assistant messages returns graceful message."""
        # Only user messages, no assistant messages
        sample_state.messages = [{"role": "user", "content": "test"}]

        mock_runtime = MagicMock()
        mock_runtime.context = {"model_name": "test-model"}

        result = await synthesizer_node(sample_state, mock_runtime)

        assert "messages" in result
        assert "Nebyly nalezeny" in result["messages"][0]["content"]
        assert result["next"] == "__end__"

    @pytest.mark.asyncio
    async def test_synthesizer_single_agent_passthrough(
        self, sample_state: State
    ) -> None:
        """Test single agent message passes through with formatting."""
        sample_state.messages = [
            {"role": "user", "content": "Najdi Ibalgin"},
            {
                "role": "assistant",
                "content": (
                    "Ibalgin obsahuje ibuprofen [1].\n\n"
                    "## References\n"
                    "[1] SUKL - Ibalgin 400"
                ),
            },
        ]

        mock_runtime = MagicMock()
        mock_runtime.context = {"model_name": "test-model"}

        result = await synthesizer_node(sample_state, mock_runtime)

        assert "messages" in result
        content = result["messages"][0]["content"]
        assert "ibuprofen" in content
        assert "[1]" in content
        assert "Czech MedAI" in content
        assert result["next"] == "__end__"

    @pytest.mark.asyncio
    async def test_synthesizer_single_agent_quick_brevity(
        self, sample_state: State
    ) -> None:
        """Test single agent applies quick brevity (max 5 sentences)."""
        long_text = ". ".join(f"Věta {i}" for i in range(1, 9)) + "."
        sample_state.messages = [
            {"role": "user", "content": "test"},
            {"role": "assistant", "content": long_text},
        ]

        mock_runtime = MagicMock()
        mock_runtime.context = {"model_name": "test-model"}

        result = await synthesizer_node(sample_state, mock_runtime)

        content = result["messages"][0]["content"]
        # Count sentences before footer
        main_content = content.split("---")[0].strip()
        sentence_count = len([s for s in main_content.split(". ") if s.strip()])
        assert sentence_count <= 5

    @pytest.mark.asyncio
    async def test_synthesizer_multiple_agents_with_llm(
        self, sample_state: State
    ) -> None:
        """Test multi-agent synthesis uses LLM for combining."""
        sample_state.messages = [
            {"role": "user", "content": "Metformin info"},
            {
                "role": "assistant",
                "content": (
                    "Metformin je lék [1].\n\n## References\n[1] SUKL - Metformin"
                ),
            },
            {
                "role": "assistant",
                "content": (
                    "Studie o metforminu [1].\n\n## References\n[1] PMID: 12345678"
                ),
            },
        ]

        mock_runtime = MagicMock()
        mock_runtime.context = {"model_name": "test-model"}

        # Mock ChatAnthropic
        mock_response = MagicMock()
        mock_response.content = "Metformin je lék [1] s prokázanou účinností [2]."

        with patch("agent.nodes.synthesizer.ChatAnthropic") as mock_llm_class:
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            mock_llm_class.return_value = mock_llm

            result = await synthesizer_node(sample_state, mock_runtime)

        content = result["messages"][0]["content"]
        assert "## Reference" in content
        assert "[1] SUKL - Metformin" in content
        assert "[2] PMID: 12345678" in content
        assert result["next"] == "__end__"

    @pytest.mark.asyncio
    async def test_synthesizer_llm_fallback_on_error(self, sample_state: State) -> None:
        """Test LLM failure falls back to concatenation."""
        sample_state.messages = [
            {"role": "user", "content": "test"},
            {"role": "assistant", "content": "Agent 1 response."},
            {"role": "assistant", "content": "Agent 2 response."},
        ]

        mock_runtime = MagicMock()
        mock_runtime.context = {"model_name": "test-model"}

        with patch("agent.nodes.synthesizer.ChatAnthropic") as mock_llm_class:
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock(side_effect=Exception("API error"))
            mock_llm_class.return_value = mock_llm

            result = await synthesizer_node(sample_state, mock_runtime)

        content = result["messages"][0]["content"]
        assert "Agent 1 response" in content
        assert "Agent 2 response" in content
        assert "Výsledky agenta" in content

    @pytest.mark.asyncio
    async def test_synthesizer_returns_empty_docs(self, sample_state: State) -> None:
        """Test synthesizer returns empty retrieved_docs (docs already in state)."""
        sample_state.messages = [
            {"role": "user", "content": "test"},
            {"role": "assistant", "content": "Response from agent."},
        ]

        mock_runtime = MagicMock()
        mock_runtime.context = {"model_name": "test-model"}

        result = await synthesizer_node(sample_state, mock_runtime)

        assert result["retrieved_docs"] == []

    @pytest.mark.asyncio
    async def test_synthesizer_handles_multimodal_content(
        self, sample_state: State
    ) -> None:
        """Test synthesizer handles list content blocks."""
        sample_state.messages = [
            {"role": "user", "content": "test"},
            {
                "role": "assistant",
                "content": [{"type": "text", "text": "Response text."}],
            },
        ]

        mock_runtime = MagicMock()
        mock_runtime.context = {"model_name": "test-model"}

        result = await synthesizer_node(sample_state, mock_runtime)

        assert "messages" in result
        assert result["next"] == "__end__"

    @pytest.mark.asyncio
    async def test_synthesizer_prepends_terminology_warnings(
        self, sample_state: State
    ) -> None:
        """Test that English abbreviation warnings are prepended to output."""
        sample_state.messages = [
            {"role": "user", "content": "test"},
            {
                "role": "assistant",
                "content": "Patient with T2DM and high CV risk.",
            },
        ]

        mock_runtime = MagicMock()
        mock_runtime.context = {"model_name": "test-model"}

        result = await synthesizer_node(sample_state, mock_runtime)

        content = result["messages"][0]["content"]
        assert "## Terminologické upozornění" in content
        assert "T2DM" in content
        assert "CV" in content

    @pytest.mark.asyncio
    async def test_synthesizer_compound_detects_agent_types(
        self, sample_state: State
    ) -> None:
        """Test multi-agent synthesis detects agent types and uses section headers."""
        sample_state.messages = [
            {"role": "user", "content": "Metformin info a studie"},
            {
                "role": "assistant",
                "content": (
                    "Metformin je SÚKL registrovaný lék [1].\n\n"
                    "## References\n[1] SUKL - Metformin"
                ),
            },
            {
                "role": "assistant",
                "content": (
                    "PubMed studie o metforminu [1].\n\n"
                    "## References\n[1] PMID: 12345678"
                ),
            },
        ]

        mock_runtime = MagicMock()
        mock_runtime.context = {"model_name": "test-model"}

        mock_response = MagicMock()
        mock_response.content = (
            "SÚKL registrovaný lék metformin [1].\n\n"
            "PubMed studie prokázala účinnost [2]."
        )

        with patch("agent.nodes.synthesizer.ChatAnthropic") as mock_llm_class:
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            mock_llm_class.return_value = mock_llm

            result = await synthesizer_node(sample_state, mock_runtime)

        content = result["messages"][0]["content"]
        assert "**Lékové informace (SÚKL)**" in content
        assert "**Výzkum (PubMed)**" in content
