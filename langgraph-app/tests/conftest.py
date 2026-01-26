"""Pytest fixtures for Czech MedAI foundation tests."""

from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock

import pytest

from agent.graph import State, graph
from agent.mcp import MCPResponse
from agent.models.drug_models import (
    DrugDetails,
    DrugQuery,
    DrugResult,
    QueryType,
)
from agent.models.research_models import (
    PubMedArticle,
    ResearchQuery,
)


@pytest.fixture(scope="session")
def anyio_backend():
    """Configure asyncio backend for pytest-asyncio."""
    return "asyncio"


@pytest.fixture
def sample_state():
    """Provide a valid State instance for testing.

    Returns:
        State: Sample state with user message and default fields.
    """
    return State(
        messages=[{"role": "user", "content": "test message"}],
        next="placeholder",
        retrieved_docs=[],
    )


@pytest.fixture
def mock_runtime():
    """Provide a mock Runtime with complete context.

    Returns:
        MockRuntime: Runtime-like object with all Context fields.
    """

    class MockRuntime:
        def __init__(self):
            self.context = {
                # Core fields
                "model_name": "test-model",
                "temperature": 0.0,
                "langsmith_project": "test-project",
                "user_id": None,
                # MCP clients (None in foundation - implemented in Feature 002)
                "sukl_mcp_client": None,
                "biomcp_client": None,
                # Conversation persistence (None - implemented in Feature 013)
                "conversation_context": None,
                # Workflow mode (default: quick)
                "mode": "quick",
            }

    return MockRuntime()


@pytest.fixture
def test_graph():
    """Provide the compiled graph for integration tests.

    Returns:
        CompiledGraph: Czech MedAI Foundation graph instance.
    """
    return graph


# =============================================================================
# Feature 003: SÚKL Drug Agent Fixtures
# =============================================================================


@pytest.fixture
def mock_sukl_response() -> MCPResponse:
    """Provide a mock SÚKL MCP response for drug search.

    Returns:
        MCPResponse: Successful response with sample drug data.
    """
    return MCPResponse(
        success=True,
        data={
            "drugs": [
                {
                    "name": "Ibalgin 400",
                    "atc_code": "M01AE01",
                    "registration_number": "58/123/01-C",
                    "manufacturer": "Zentiva",
                },
                {
                    "name": "Ibalgin 200",
                    "atc_code": "M01AE01",
                    "registration_number": "58/124/01-C",
                    "manufacturer": "Zentiva",
                },
            ]
        },
        metadata={
            "latency_ms": 150,
            "server_url": "http://localhost:3000",
            "tool_name": "search_drugs",
        },
    )


@pytest.fixture
def mock_sukl_details_response() -> MCPResponse:
    """Provide a mock SÚKL MCP response for drug details.

    Returns:
        MCPResponse: Successful response with detailed drug information.
    """
    return MCPResponse(
        success=True,
        data={
            "registration_number": "58/123/01-C",
            "name": "Ibalgin 400",
            "active_ingredient": "ibuprofenum",
            "composition": ["ibuprofenum 400 mg", "pomocné látky"],
            "indications": [
                "Bolest hlavy",
                "Bolest zubů",
                "Bolesti svalů a kloubů",
            ],
            "contraindications": [
                "Přecitlivělost na ibuprofen",
                "Vředová choroba",
            ],
            "dosage": "1-2 tablety 3x denně po jídle",
            "side_effects": ["Nauzea", "Bolest žaludku"],
            "pharmaceutical_form": "Potahované tablety",
            "atc_code": "M01AE01",
        },
        metadata={"latency_ms": 200},
    )


@pytest.fixture
def mock_sukl_client(
    mock_sukl_response: MCPResponse, mock_sukl_details_response: MCPResponse
) -> MagicMock:
    """Provide a mock SUKLMCPClient for testing.

    Args:
        mock_sukl_response: Response for search queries.
        mock_sukl_details_response: Response for detail queries.

    Returns:
        MagicMock: Mock client with preconfigured responses.
    """
    client = MagicMock()
    client.call_tool = AsyncMock()

    # Configure responses based on tool_name
    async def call_tool_side_effect(
        tool_name: str, parameters: Dict[str, Any], retry_config: Any = None
    ) -> MCPResponse:
        if tool_name == "search_drugs":
            return mock_sukl_response
        elif tool_name == "get_drug_details":
            return mock_sukl_details_response
        elif tool_name == "get_reimbursement":
            return MCPResponse(
                success=True,
                data={
                    "registration_number": parameters.get("registration_number"),
                    "category": "B",
                    "copay_amount": 45.0,
                    "prescription_required": True,
                    "conditions": ["Pro chronickou bolest"],
                },
            )
        elif tool_name == "check_availability":
            return MCPResponse(
                success=True,
                data={
                    "registration_number": parameters.get("registration_number"),
                    "is_available": True,
                    "alternatives": [],
                },
            )
        else:
            return MCPResponse(success=False, error=f"Unknown tool: {tool_name}")

    client.call_tool.side_effect = call_tool_side_effect
    return client


@pytest.fixture
def sample_drug_query() -> DrugQuery:
    """Provide a sample DrugQuery for testing.

    Returns:
        DrugQuery: Search query for "Ibalgin".
    """
    return DrugQuery(
        query_text="Ibalgin",
        query_type=QueryType.SEARCH,
        limit=10,
    )


@pytest.fixture
def sample_drug_result() -> DrugResult:
    """Provide a sample DrugResult for testing.

    Returns:
        DrugResult: Sample drug search result.
    """
    return DrugResult(
        name="Ibalgin 400",
        atc_code="M01AE01",
        registration_number="58/123/01-C",
        manufacturer="Zentiva",
        match_score=0.95,
    )


@pytest.fixture
def sample_drug_details() -> DrugDetails:
    """Provide sample DrugDetails for testing.

    Returns:
        DrugDetails: Complete drug information.
    """
    return DrugDetails(
        registration_number="58/123/01-C",
        name="Ibalgin 400",
        active_ingredient="ibuprofenum",
        composition=["ibuprofenum 400 mg"],
        indications=["Bolest hlavy", "Bolest zubů"],
        contraindications=["Přecitlivělost na ibuprofen"],
        dosage="1-2 tablety 3x denně",
        atc_code="M01AE01",
    )


# =============================================================================
# Feature 005: BioMCP PubMed Agent Fixtures
# =============================================================================


@pytest.fixture
def mock_biomcp_article() -> Dict[str, Any]:
    """Provide a mock BioMCP article response.

    Returns:
        Dict: Sample PubMed article data from BioMCP.
    """
    return {
        "pmid": "12345678",
        "title": "Efficacy of Metformin in Type 2 Diabetes: A Randomized Trial",
        "abstract": "Background: Metformin is a first-line therapy for type 2 diabetes mellitus. This randomized controlled trial evaluated its efficacy in newly diagnosed patients. Methods: 200 patients were randomly assigned to metformin 1000mg twice daily or placebo. Results: HbA1c decreased by 1.5% in the metformin group vs 0.2% in placebo (p<0.001). Conclusion: Metformin is effective for glycemic control in type 2 diabetes.",
        "authors": ["Smith, John", "Doe, Jane", "Johnson, Peter"],
        "publication_date": "2024-06-15",
        "journal": "New England Journal of Medicine",
        "doi": "10.1056/NEJMoa2401234",
        "pmc_id": "PMC10123456",
    }


@pytest.fixture
def mock_biomcp_client() -> MagicMock:
    """Provide a mock BioMCPClient for testing.

    Returns:
        MagicMock: Mock client with preconfigured article responses.
    """
    client = MagicMock()
    client.call_tool = AsyncMock()

    # Configure responses based on tool_name
    async def call_tool_side_effect(
        tool_name: str, parameters: Dict[str, Any], retry_config: Any = None
    ) -> MCPResponse:
        if tool_name == "article_searcher":
            return MCPResponse(
                success=True,
                data={
                    "articles": [
                        {
                            "pmid": "12345678",
                            "title": "Efficacy of Metformin in Type 2 Diabetes",
                            "abstract": "Background: Metformin is a first-line therapy...",
                            "authors": ["Smith, John", "Doe, Jane"],
                            "publication_date": "2024-06-15",
                            "journal": "NEJM",
                            "doi": "10.1056/NEJMoa2401234",
                        },
                        {
                            "pmid": "87654321",
                            "title": "Guidelines for Diabetes Management 2024",
                            "abstract": "Updated clinical practice guidelines...",
                            "authors": ["Brown, Alice"],
                            "publication_date": "2024-01-10",
                            "journal": "Diabetes Care",
                            "doi": "10.2337/dc24-0001",
                        },
                    ],
                    "total_results": 2,
                },
                metadata={"latency_ms": 2500, "query": parameters.get("query", "")},
            )
        elif tool_name == "article_getter":
            # PMID lookup
            pmid = parameters.get("pmid", "12345678")
            return MCPResponse(
                success=True,
                data={
                    "pmid": pmid,
                    "title": "Efficacy of Metformin in Type 2 Diabetes",
                    "abstract": "Background: Metformin is a first-line therapy for type 2 diabetes mellitus...",
                    "authors": ["Smith, John", "Doe, Jane", "Johnson, Peter"],
                    "publication_date": "2024-06-15",
                    "journal": "New England Journal of Medicine",
                    "doi": "10.1056/NEJMoa2401234",
                    "pmc_id": "PMC10123456",
                },
                metadata={"latency_ms": 1500},
            )
        else:
            return MCPResponse(success=False, error=f"Unknown tool: {tool_name}")

    client.call_tool.side_effect = call_tool_side_effect
    return client


@pytest.fixture
def sample_research_query() -> ResearchQuery:
    """Provide a sample ResearchQuery for testing.

    Returns:
        ResearchQuery: Search query for diabetes studies.
    """
    return ResearchQuery(
        query_text="Jaké jsou nejnovější studie o diabetu typu 2?",
        query_type="search",
        filters={"date_range": ("2023-01-01", "2026-01-20"), "max_results": 5},
    )


@pytest.fixture
def sample_pubmed_articles() -> List[PubMedArticle]:
    """Provide sample PubMed articles for testing (5 articles).

    Returns:
        List[PubMedArticle]: List of 5 sample articles.
    """
    return [
        PubMedArticle(
            pmid="12345678",
            title="Efficacy of Metformin in Type 2 Diabetes: A Randomized Trial",
            abstract="Background: Metformin is a first-line therapy for type 2 diabetes mellitus. This RCT evaluated its efficacy in newly diagnosed patients.",
            authors=["Smith, John", "Doe, Jane", "Johnson, Peter"],
            publication_date="2024-06-15",
            journal="New England Journal of Medicine",
            doi="10.1056/NEJMoa2401234",
            pmc_id="PMC10123456",
        ),
        PubMedArticle(
            pmid="87654321",
            title="Guidelines for Diabetes Management 2024",
            abstract="Updated clinical practice guidelines for comprehensive diabetes care.",
            authors=["Brown, Alice", "Wilson, Robert"],
            publication_date="2024-01-10",
            journal="Diabetes Care",
            doi="10.2337/dc24-0001",
        ),
        PubMedArticle(
            pmid="11111111",
            title="SGLT2 Inhibitors in Heart Failure with Type 2 Diabetes",
            abstract="Cardiovascular outcomes with SGLT2 inhibitors in patients with heart failure and diabetes.",
            authors=["Taylor, Emma", "Davis, Michael"],
            publication_date="2023-11-20",
            journal="Circulation",
            doi="10.1161/CIRCULATIONAHA.123.12345",
        ),
        PubMedArticle(
            pmid="22222222",
            title="Dietary Interventions for Type 2 Diabetes: A Meta-Analysis",
            abstract="Systematic review and meta-analysis of dietary approaches for glycemic control.",
            authors=["Martinez, Sofia"],
            publication_date="2023-08-05",
            journal="The Lancet Diabetes & Endocrinology",
            doi="10.1016/S2213-8587(23)00234-5",
        ),
        PubMedArticle(
            pmid="33333333",
            title="GLP-1 Receptor Agonists: Mechanism and Clinical Applications",
            abstract="Comprehensive review of GLP-1 agonists in diabetes and obesity management.",
            authors=["Anderson, James", "Lee, Christine", "Garcia, Maria"],
            publication_date="2023-05-12",
            journal="Nature Reviews Endocrinology",
            doi="10.1038/s41574-023-00456-7",
        ),
    ]
