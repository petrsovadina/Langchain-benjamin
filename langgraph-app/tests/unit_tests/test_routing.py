"""Unit tests for route_query function with multimodal content support.

Tests ensure route_query handles both string and list (multimodal) message content.
"""

from agent.graph import State, route_query


def test_route_query_with_string_content():
    """Test route_query handles standard string content.

    Acceptance: Given State with string message content containing drug keyword,
    When route_query is invoked,
    Then it routes to drug_agent.
    """
    # Arrange
    state = State(
        messages=[{"role": "user", "content": "jaká je dávka léku ibuprofen"}], next=""
    )

    # Act
    result = route_query(state)

    # Assert
    assert result == "drug_agent"


def test_route_query_with_multimodal_list_content():
    """Test route_query handles multimodal list content (LangGraph Studio format).

    Acceptance: Given State with list message content (multimodal),
    When route_query is invoked,
    Then it extracts text and routes correctly without AttributeError.
    """
    # Arrange - Simulate LangGraph Studio multimodal message
    state = State(
        messages=[
            {
                "role": "user",
                "content": [{"type": "text", "text": "jaké jsou studie o hypertenzi"}],
            }
        ],
        next="",
    )

    # Act
    result = route_query(state)

    # Assert
    assert result == "translate_cz_to_en"  # Should route to research


def test_route_query_with_multimodal_simple_list():
    """Test route_query handles simple list of strings.

    Acceptance: Given State with list of strings as content,
    When route_query is invoked,
    Then it uses first string element for routing.
    """
    # Arrange
    state = State(
        messages=[{"role": "user", "content": ["lék na diabetes", "další info"]}],
        next="",
    )

    # Act
    result = route_query(state)

    # Assert
    assert result == "drug_agent"


def test_route_query_with_empty_list_content():
    """Test route_query handles empty list content gracefully.

    Acceptance: Given State with empty list as content,
    When route_query is invoked,
    Then it defaults to placeholder without crash.
    """
    # Arrange
    state = State(messages=[{"role": "user", "content": []}], next="")

    # Act
    result = route_query(state)

    # Assert
    assert result == "placeholder"


def test_route_query_with_research_keyword():
    """Test route_query routes research queries correctly.

    Acceptance: Given State with research keyword in content,
    When route_query is invoked,
    Then it routes to translate_cz_to_en (PubMed agent).
    """
    # Arrange
    state = State(
        messages=[{"role": "user", "content": "jaké jsou studie o metforminu"}], next=""
    )

    # Act
    result = route_query(state)

    # Assert
    assert result == "translate_cz_to_en"


def test_route_query_with_no_keywords():
    """Test route_query defaults to placeholder for generic queries.

    Acceptance: Given State with no drug/research keywords,
    When route_query is invoked,
    Then it routes to placeholder.
    """
    # Arrange
    state = State(messages=[{"role": "user", "content": "ahoj jak se máš"}], next="")

    # Act
    result = route_query(state)

    # Assert
    assert result == "placeholder"


def test_route_query_with_explicit_drug_query():
    """Test route_query uses explicit drug_query if set.

    Acceptance: Given State with explicit drug_query set,
    When route_query is invoked,
    Then it routes to drug_agent regardless of message content.
    """
    # Arrange
    from agent.models.drug_models import DrugQuery

    state = State(
        messages=[{"role": "user", "content": "nějaký dotaz"}],
        next="",
        drug_query=DrugQuery(query_text="ibuprofen", query_type="search"),
    )

    # Act
    result = route_query(state)

    # Assert
    assert result == "drug_agent"


def test_route_query_with_explicit_research_query():
    """Test route_query uses explicit research_query if set.

    Acceptance: Given State with explicit research_query set,
    When route_query is invoked,
    Then it routes to translate_cz_to_en regardless of message content.
    """
    # Arrange
    from agent.models.research_models import ResearchQuery

    state = State(
        messages=[{"role": "user", "content": "nějaký dotaz"}],
        next="",
        research_query=ResearchQuery(
            query_text="diabetes studies", query_type="search"
        ),
    )

    # Act
    result = route_query(state)

    # Assert
    assert result == "translate_cz_to_en"


# =============================================================================
# Guidelines Routing Tests (Feature 006)
# =============================================================================


def test_route_query_with_guidelines_keyword():
    """Test route_query routes to guidelines_agent based on GUIDELINES_KEYWORDS.

    Acceptance: Given State with guidelines keyword in content,
    When route_query is invoked,
    Then it routes to guidelines_agent.
    """
    # Arrange
    state = State(
        messages=[
            {"role": "user", "content": "Jaké jsou doporučené postupy pro hypertenzi?"}
        ],
        next="",
    )

    # Act
    result = route_query(state)

    # Assert
    assert result == "guidelines_agent"


def test_route_query_with_guidelines_keyword_english():
    """Test route_query routes to guidelines_agent with English guidelines keyword.

    Acceptance: Given State with English "guidelines" keyword (without research keywords),
    When route_query is invoked,
    Then it routes to guidelines_agent.
    """
    # Arrange - Use query without research keywords like "diabetes", "studie", etc.
    state = State(
        messages=[{"role": "user", "content": "guidelines pro bolest zad"}],
        next="",
    )

    # Act
    result = route_query(state)

    # Assert
    assert result == "guidelines_agent"


def test_route_query_with_cls_jep_keyword():
    """Test route_query routes to guidelines_agent with CLS JEP keyword.

    Acceptance: Given State with "CLS JEP" keyword,
    When route_query is invoked,
    Then it routes to guidelines_agent.
    """
    # Arrange
    state = State(
        messages=[{"role": "user", "content": "CLS JEP doporučení pro léčbu"}],
        next="",
    )

    # Act
    result = route_query(state)

    # Assert
    assert result == "guidelines_agent"


def test_route_query_with_esc_keyword():
    """Test route_query routes to guidelines_agent with ESC keyword.

    Acceptance: Given State with "ESC" keyword,
    When route_query is invoked,
    Then it routes to guidelines_agent.
    """
    # Arrange
    state = State(
        messages=[{"role": "user", "content": "ESC guidelines for heart failure"}],
        next="",
    )

    # Act
    result = route_query(state)

    # Assert
    assert result == "guidelines_agent"


def test_route_query_with_standardy_keyword():
    """Test route_query routes to guidelines_agent with "standardy" keyword.

    Acceptance: Given State with Czech "standardy" keyword,
    When route_query is invoked,
    Then it routes to guidelines_agent.
    """
    # Arrange
    state = State(
        messages=[{"role": "user", "content": "standardy péče o pacienty"}],
        next="",
    )

    # Act
    result = route_query(state)

    # Assert
    assert result == "guidelines_agent"


def test_route_query_with_explicit_guideline_query():
    """Test route_query uses explicit guideline_query if set.

    Acceptance: Given State with explicit guideline_query set,
    When route_query is invoked,
    Then it routes to guidelines_agent regardless of message content.
    """
    # Arrange
    from agent.models.guideline_models import GuidelineQuery, GuidelineQueryType

    state = State(
        messages=[{"role": "user", "content": "nějaký dotaz"}],
        next="",
        guideline_query=GuidelineQuery(
            query_text="léčba hypertenze",
            query_type=GuidelineQueryType.SEARCH,
        ),
    )

    # Act
    result = route_query(state)

    # Assert
    assert result == "guidelines_agent"


def test_route_query_research_priority_over_guidelines():
    """Test that research keywords have higher priority than guidelines keywords.

    Acceptance: Given State with both research and guidelines keywords,
    When route_query is invoked,
    Then it routes to translate_cz_to_en (research) because research has higher priority.
    """
    # Arrange - "studie" is a research keyword, "guidelines" is a guidelines keyword
    state = State(
        messages=[{"role": "user", "content": "studie o guidelines pro diabetes"}],
        next="",
    )

    # Act
    result = route_query(state)

    # Assert - Research keywords have highest priority
    assert result == "translate_cz_to_en"


def test_route_query_guidelines_priority_over_drug():
    """Test that drug keywords route to drug_agent, and guidelines to guidelines_agent.

    Updated 2026-02-09: Drug keywords now have highest priority (most common use case).
    Guidelines-only queries still route to guidelines_agent.
    """
    # Drug keywords should win
    state = State(
        messages=[
            {"role": "user", "content": "doporučené postupy pro prášky na bolest"}
        ],
        next="",
    )
    result = route_query(state)
    assert result == "drug_agent"  # "prášky" is a drug keyword, drug takes priority

    # Pure guidelines query (no drug keywords) goes to guidelines
    state2 = State(
        messages=[
            {"role": "user", "content": "doporučené postupy pro hypertenzi"}
        ],
        next="",
    )
    result2 = route_query(state2)
    assert result2 == "guidelines_agent"
