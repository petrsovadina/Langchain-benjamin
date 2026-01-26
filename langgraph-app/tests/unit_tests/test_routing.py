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
                "content": [{"type": "text", "text": "jaké jsou studie o diabetu"}],
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
