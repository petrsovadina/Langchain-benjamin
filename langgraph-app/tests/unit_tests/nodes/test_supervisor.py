"""Unit tests for Supervisor Intent Classifier.

This module contains comprehensive tests for the IntentClassifier class
and helper functions, covering all 8 intent types and edge cases.

Test classes:
- TestIntentType: Tests for IntentType enum
- TestIntentResult: Tests for IntentResult model validation
- TestIntentClassification: Tests for all 8 intent types
- TestEdgeCases: Tests for error handling and edge cases
- TestHelperFunctions: Tests for helper functions

Coverage target: ≥90%
"""

from unittest.mock import MagicMock, patch

import pytest

from agent.models.supervisor_models import (
    VALID_AGENT_NAMES,
    IntentResult,
    IntentType,
)
from agent.nodes.supervisor import (
    IntentClassifier,
    fallback_to_keyword_routing,
    log_intent_classification,
    validate_agent_names,
)


class TestIntentType:
    """Tests for IntentType enum."""

    def test_intent_type_has_8_values(self):
        """Test that IntentType has exactly 8 values."""
        assert len(IntentType) == 8

    def test_intent_type_values(self):
        """Test all IntentType enum values."""
        expected = {
            "drug_info",
            "guideline_lookup",
            "research_query",
            "compound_query",
            "clinical_question",
            "urgent_diagnostic",
            "general_medical",
            "out_of_scope",
        }
        actual = {e.value for e in IntentType}
        assert actual == expected

    def test_intent_type_is_string_enum(self):
        """Test that IntentType values are strings."""
        for intent in IntentType:
            assert isinstance(intent.value, str)


class TestIntentResult:
    """Tests for IntentResult model validation."""

    def test_valid_intent_result(self):
        """Test creating valid IntentResult."""
        result = IntentResult(
            intent_type=IntentType.DRUG_INFO,
            confidence=0.95,
            agents_to_call=["drug_agent"],
            reasoning="Drug query detected",
        )

        assert result.intent_type == IntentType.DRUG_INFO
        assert result.confidence == 0.95
        assert result.agents_to_call == ["drug_agent"]
        assert result.reasoning == "Drug query detected"

    def test_confidence_validation_min(self):
        """Test confidence minimum bound validation."""
        with pytest.raises(ValueError):
            IntentResult(
                intent_type=IntentType.DRUG_INFO,
                confidence=-0.1,  # Invalid: below 0
                agents_to_call=["drug_agent"],
                reasoning="Test",
            )

    def test_confidence_validation_max(self):
        """Test confidence maximum bound validation."""
        with pytest.raises(ValueError):
            IntentResult(
                intent_type=IntentType.DRUG_INFO,
                confidence=1.5,  # Invalid: above 1.0
                agents_to_call=["drug_agent"],
                reasoning="Test",
            )

    def test_agents_to_call_filters_invalid(self):
        """Test that invalid agent names are filtered out."""
        result = IntentResult(
            intent_type=IntentType.DRUG_INFO,
            confidence=0.9,
            agents_to_call=["drug_agent", "invalid_agent", "pubmed_agent"],
            reasoning="Test",
        )

        # Invalid agent should be filtered out
        assert result.agents_to_call == ["drug_agent", "pubmed_agent"]

    def test_reasoning_cannot_be_empty(self):
        """Test that reasoning cannot be empty."""
        with pytest.raises(ValueError):
            IntentResult(
                intent_type=IntentType.DRUG_INFO,
                confidence=0.9,
                agents_to_call=["drug_agent"],
                reasoning="",  # Invalid: empty
            )

    def test_reasoning_cannot_be_whitespace(self):
        """Test that reasoning cannot be whitespace only."""
        with pytest.raises(ValueError):
            IntentResult(
                intent_type=IntentType.DRUG_INFO,
                confidence=0.9,
                agents_to_call=["drug_agent"],
                reasoning="   ",  # Invalid: whitespace only
            )

    def test_empty_agents_to_call_allowed(self):
        """Test that empty agents_to_call is allowed (for out_of_scope)."""
        result = IntentResult(
            intent_type=IntentType.OUT_OF_SCOPE,
            confidence=0.98,
            agents_to_call=[],
            reasoning="Out of scope query",
        )

        assert result.agents_to_call == []


class TestIntentClassification:
    """Test intent classification for all 8 intent types."""

    @pytest.mark.asyncio
    async def test_classify_drug_info_intent(
        self, mock_llm: MagicMock, create_mock_tool_call
    ):
        """Test classification of drug info query."""
        classifier = IntentClassifier(llm=mock_llm)

        # Mock Claude response
        mock_llm.ainvoke.return_value = create_mock_tool_call(
            intent_type="drug_info",
            confidence=0.95,
            agents_to_call=["drug_agent"],
            reasoning="Query asks about drug composition",
        )

        result = await classifier.classify_intent("Jaké je složení Ibalginu?")

        assert result.intent_type == IntentType.DRUG_INFO
        assert result.confidence >= 0.9
        assert "drug_agent" in result.agents_to_call

    @pytest.mark.asyncio
    async def test_classify_guideline_lookup_intent(
        self, mock_llm: MagicMock, create_mock_tool_call
    ):
        """Test classification of guideline lookup query."""
        classifier = IntentClassifier(llm=mock_llm)

        mock_llm.ainvoke.return_value = create_mock_tool_call(
            intent_type="guideline_lookup",
            confidence=0.95,
            agents_to_call=["guidelines_agent"],
            reasoning="Query asks about guidelines",
        )

        result = await classifier.classify_intent(
            "Jaké jsou guidelines pro hypertenzi?"
        )

        assert result.intent_type == IntentType.GUIDELINE_LOOKUP
        assert "guidelines_agent" in result.agents_to_call

    @pytest.mark.asyncio
    async def test_classify_research_query_intent(
        self, mock_llm: MagicMock, create_mock_tool_call
    ):
        """Test classification of research query."""
        classifier = IntentClassifier(llm=mock_llm)

        mock_llm.ainvoke.return_value = create_mock_tool_call(
            intent_type="research_query",
            confidence=0.95,
            agents_to_call=["pubmed_agent"],
            reasoning="Query asks about research studies",
        )

        result = await classifier.classify_intent(
            "Jaké jsou nejnovější studie o diabetu?"
        )

        assert result.intent_type == IntentType.RESEARCH_QUERY
        assert "pubmed_agent" in result.agents_to_call

    @pytest.mark.asyncio
    async def test_classify_compound_query_intent(
        self, mock_llm: MagicMock, create_mock_tool_call
    ):
        """Test classification of compound query (multiple agents)."""
        classifier = IntentClassifier(llm=mock_llm)

        mock_llm.ainvoke.return_value = create_mock_tool_call(
            intent_type="compound_query",
            confidence=0.92,
            agents_to_call=["drug_agent", "guidelines_agent"],
            reasoning="Compound query: drug info and guidelines",
        )

        result = await classifier.classify_intent(
            "Jaké jsou guidelines pro metformin a jaká je jeho cena?"
        )

        assert result.intent_type == IntentType.COMPOUND_QUERY
        assert len(result.agents_to_call) >= 2
        assert "drug_agent" in result.agents_to_call
        assert "guidelines_agent" in result.agents_to_call

    @pytest.mark.asyncio
    async def test_classify_clinical_question_intent(
        self, mock_llm: MagicMock, create_mock_tool_call
    ):
        """Test classification of clinical question."""
        classifier = IntentClassifier(llm=mock_llm)

        mock_llm.ainvoke.return_value = create_mock_tool_call(
            intent_type="clinical_question",
            confidence=0.90,
            agents_to_call=["guidelines_agent", "pubmed_agent"],
            reasoning="Clinical treatment question",
        )

        result = await classifier.classify_intent("Jak léčit hypertenzi u diabetika?")

        assert result.intent_type == IntentType.CLINICAL_QUESTION
        assert "guidelines_agent" in result.agents_to_call

    @pytest.mark.asyncio
    async def test_classify_urgent_diagnostic_intent(
        self, mock_llm: MagicMock, create_mock_tool_call
    ):
        """Test classification of urgent diagnostic query."""
        classifier = IntentClassifier(llm=mock_llm)

        mock_llm.ainvoke.return_value = create_mock_tool_call(
            intent_type="urgent_diagnostic",
            confidence=0.95,
            agents_to_call=["guidelines_agent"],
            reasoning="Urgent diagnostic query detected",
        )

        result = await classifier.classify_intent(
            "Urgentní: diferenciální diagnostika bolesti na hrudi"
        )

        assert result.intent_type == IntentType.URGENT_DIAGNOSTIC
        assert result.confidence >= 0.8

    @pytest.mark.asyncio
    async def test_classify_general_medical_intent(
        self, mock_llm: MagicMock, create_mock_tool_call
    ):
        """Test classification of general medical query."""
        classifier = IntentClassifier(llm=mock_llm)

        mock_llm.ainvoke.return_value = create_mock_tool_call(
            intent_type="general_medical",
            confidence=0.85,
            agents_to_call=["placeholder"],
            reasoning="General medical question",
        )

        result = await classifier.classify_intent("Co je to diabetes?")

        assert result.intent_type == IntentType.GENERAL_MEDICAL

    @pytest.mark.asyncio
    async def test_classify_out_of_scope_intent(
        self, mock_llm: MagicMock, create_mock_tool_call
    ):
        """Test classification of out-of-scope query."""
        classifier = IntentClassifier(llm=mock_llm)

        mock_llm.ainvoke.return_value = create_mock_tool_call(
            intent_type="out_of_scope",
            confidence=0.98,
            agents_to_call=[],
            reasoning="Non-medical query (weather)",
        )

        result = await classifier.classify_intent("Jaké je dnes počasí?")

        assert result.intent_type == IntentType.OUT_OF_SCOPE
        assert len(result.agents_to_call) == 0


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_classify_empty_message_raises_error(self):
        """Test that empty message raises ValueError."""
        classifier = IntentClassifier()

        with pytest.raises(ValueError, match="empty"):
            await classifier.classify_intent("")

    @pytest.mark.asyncio
    async def test_classify_whitespace_message_raises_error(self):
        """Test that whitespace-only message raises ValueError."""
        classifier = IntentClassifier()

        with pytest.raises(ValueError, match="empty"):
            await classifier.classify_intent("   \n  ")

    @pytest.mark.asyncio
    async def test_fallback_on_llm_error(self, mock_llm: MagicMock):
        """Test fallback to keyword routing on LLM error."""
        classifier = IntentClassifier(llm=mock_llm)
        mock_llm.ainvoke.side_effect = Exception("API error")

        result = await classifier.classify_intent("Najdi lék Ibalgin")

        # Should fallback to keyword routing
        assert result.intent_type == IntentType.DRUG_INFO
        assert result.confidence < 0.7  # Lower confidence for fallback
        assert "Fallback" in result.reasoning

    @pytest.mark.asyncio
    async def test_fallback_on_no_tool_calls(self, mock_llm: MagicMock):
        """Test fallback when response has no tool calls."""
        classifier = IntentClassifier(llm=mock_llm)

        # Mock response without tool_calls
        mock_response = MagicMock()
        mock_response.tool_calls = []
        mock_llm.ainvoke.return_value = mock_response

        result = await classifier.classify_intent("Najdi lék Ibalgin")

        # Should fallback to keyword routing
        assert "Fallback" in result.reasoning

    @pytest.mark.asyncio
    async def test_low_confidence_warning(
        self, mock_llm: MagicMock, create_mock_tool_call, caplog
    ):
        """Test that low confidence triggers warning log."""
        classifier = IntentClassifier(llm=mock_llm)

        mock_llm.ainvoke.return_value = create_mock_tool_call(
            intent_type="general_medical",
            confidence=0.4,  # Low confidence
            agents_to_call=["placeholder"],
            reasoning="Unclear query",
        )

        with caplog.at_level("WARNING"):
            result = await classifier.classify_intent("Něco nejasného")

        assert result.confidence < 0.5
        # Check that warning was logged
        assert any(
            "low confidence" in record.message.lower() for record in caplog.records
        )


class TestHelperFunctions:
    """Test helper functions."""

    def test_validate_agent_names_filters_invalid(self):
        """Test that validate_agent_names filters invalid agents."""
        agents = ["drug_agent", "invalid_agent", "pubmed_agent", "fake_agent"]

        valid = validate_agent_names(agents)

        assert valid == ["drug_agent", "pubmed_agent"]

    def test_validate_agent_names_all_valid(self):
        """Test with all valid agent names."""
        agents = ["drug_agent", "pubmed_agent", "guidelines_agent"]

        valid = validate_agent_names(agents)

        assert valid == agents

    def test_validate_agent_names_empty_list(self):
        """Test with empty list."""
        valid = validate_agent_names([])

        assert valid == []

    def test_validate_agent_names_all_invalid(self):
        """Test with all invalid agent names."""
        agents = ["invalid1", "invalid2", "invalid3"]

        valid = validate_agent_names(agents)

        assert valid == []

    def test_valid_agent_names_set(self):
        """Test that VALID_AGENT_NAMES contains expected agents."""
        expected = {"drug_agent", "pubmed_agent", "guidelines_agent", "placeholder"}
        assert VALID_AGENT_NAMES == expected

    def test_fallback_to_keyword_routing_drug(self):
        """Test keyword fallback for drug query."""
        # Use query with actual drug keyword ("lék")
        result = fallback_to_keyword_routing("Najdi lék Ibalgin")

        assert result.intent_type == IntentType.DRUG_INFO
        assert "drug_agent" in result.agents_to_call
        assert "Fallback" in result.reasoning
        assert result.confidence < 0.7

    def test_fallback_to_keyword_routing_research(self):
        """Test keyword fallback for research query."""
        result = fallback_to_keyword_routing("Jaké jsou studie o diabetu?")

        assert result.intent_type == IntentType.RESEARCH_QUERY
        assert "pubmed_agent" in result.agents_to_call
        assert "Fallback" in result.reasoning

    def test_fallback_to_keyword_routing_guidelines(self):
        """Test keyword fallback for guidelines query."""
        result = fallback_to_keyword_routing("Doporučení pro léčbu hypertenze")

        assert result.intent_type == IntentType.GUIDELINE_LOOKUP
        assert "guidelines_agent" in result.agents_to_call
        assert "Fallback" in result.reasoning

    def test_fallback_to_keyword_routing_general(self):
        """Test keyword fallback for general query (no keywords)."""
        result = fallback_to_keyword_routing("Zdravím vás")

        assert result.intent_type == IntentType.GENERAL_MEDICAL
        assert "placeholder" in result.agents_to_call
        assert "Fallback" in result.reasoning

    def test_log_intent_classification(
        self, sample_intent_result: IntentResult, caplog
    ):
        """Test that log_intent_classification logs correctly."""
        with caplog.at_level("INFO"):
            log_intent_classification(sample_intent_result, "Jaké je složení Ibalginu?")

        # Check INFO level log
        assert any(
            "IntentClassifier" in record.message and "drug_info" in record.message
            for record in caplog.records
        )

    def test_log_intent_classification_debug(
        self, sample_intent_result: IntentResult, caplog
    ):
        """Test that log_intent_classification logs reasoning at DEBUG."""
        with caplog.at_level("DEBUG"):
            log_intent_classification(sample_intent_result, "Test query")

        # Check DEBUG level has reasoning
        assert any("Reasoning" in record.message for record in caplog.records)


class TestIntentClassifierInit:
    """Test IntentClassifier initialization."""

    def test_default_initialization(self):
        """Test IntentClassifier with default parameters (lazy LLM init)."""
        classifier = IntentClassifier()

        assert classifier.model_name == "claude-sonnet-4-20250514"
        assert classifier.temperature == 0.0
        # LLM is lazily initialized - None until first classify_intent call
        assert classifier.llm is None

    def test_custom_initialization(self):
        """Test IntentClassifier with custom parameters."""
        classifier = IntentClassifier(
            model_name="claude-3-5-sonnet-20241022",
            temperature=0.5,
        )

        assert classifier.model_name == "claude-3-5-sonnet-20241022"
        assert classifier.temperature == 0.5

    def test_initialization_with_provided_llm(self, mock_llm: MagicMock):
        """Test IntentClassifier with pre-configured LLM."""
        classifier = IntentClassifier(llm=mock_llm)

        assert classifier.llm is mock_llm

    @pytest.mark.asyncio
    async def test_lazy_init_uses_model_kwarg(self, create_mock_tool_call):
        """Test lazy init passes model= (not model_name=) to ChatAnthropic."""
        classifier = IntentClassifier(
            model_name="claude-sonnet-4-20250514",
            temperature=0.0,
        )
        assert classifier.llm is None

        mock_chat = MagicMock()
        mock_chat.ainvoke.return_value = create_mock_tool_call(
            intent_type="general_medical",
            confidence=0.9,
            agents_to_call=["placeholder"],
            reasoning="Test lazy init",
        )

        with patch(
            "agent.nodes.supervisor.ChatAnthropic", return_value=mock_chat
        ) as mock_cls:
            await classifier.classify_intent("Test query")

            mock_cls.assert_called_once_with(
                model="claude-sonnet-4-20250514",
                temperature=0.0,
                timeout=None,
                stop=None,
            )
        assert classifier.llm is mock_chat


class TestPromptBuilding:
    """Test prompt building functions."""

    def test_build_classification_prompt_with_examples(self):
        """Test prompt building with few-shot examples."""
        from agent.nodes.supervisor_prompts import build_classification_prompt

        prompt = build_classification_prompt("Test query", include_examples=True)

        assert "KLASIFIKUJ TENTO DOTAZ" in prompt
        assert "Test query" in prompt
        assert "PŘÍKLADY KLASIFIKACE" in prompt
        assert "drug_info" in prompt

    def test_build_classification_prompt_without_examples(self):
        """Test prompt building without few-shot examples."""
        from agent.nodes.supervisor_prompts import build_classification_prompt

        prompt = build_classification_prompt("Test query", include_examples=False)

        assert "KLASIFIKUJ TENTO DOTAZ" in prompt
        assert "Test query" in prompt
        assert "PŘÍKLADY KLASIFIKACE" not in prompt

    def test_build_function_schema(self):
        """Test function schema building."""
        from agent.nodes.supervisor_prompts import build_function_schema

        schema = build_function_schema()

        assert schema["name"] == "classify_medical_intent"
        assert "input_schema" in schema
        assert "intent_type" in schema["input_schema"]["properties"]
        assert "confidence" in schema["input_schema"]["properties"]
        assert "agents_to_call" in schema["input_schema"]["properties"]
        assert "reasoning" in schema["input_schema"]["properties"]

    def test_function_schema_enum_values(self):
        """Test that function schema has all intent types."""
        from agent.nodes.supervisor_prompts import build_function_schema

        schema = build_function_schema()
        enum_values = schema["input_schema"]["properties"]["intent_type"]["enum"]

        assert len(enum_values) == 8
        assert "drug_info" in enum_values
        assert "out_of_scope" in enum_values
