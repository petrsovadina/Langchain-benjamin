"""SÚKL Drug Agent node implementation.

LangGraph node for querying Czech pharmaceutical database via SÚKL-mcp server.
Implements Feature 003 specification.

Constitution Compliance:
- Principle I: Async node function with proper signature
- Principle II: Typed state/context, Pydantic models
- Principle IV: LangSmith tracing, logging at boundaries
- Principle V: Single responsibility, helper functions extracted
"""

from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List

from langchain_core.documents import Document

from agent.mcp import (
    MCPConnectionError,
    MCPServerError,
    MCPTimeoutError,
    SUKLMCPClient,
)
from agent.models.drug_models import (
    AvailabilityInfo,
    DrugDetails,
    DrugQuery,
    DrugResult,
    QueryType,
    ReimbursementCategory,
    ReimbursementInfo,
)

if TYPE_CHECKING:
    from langgraph.runtime import Runtime

    from agent.graph import Context, State

logger = logging.getLogger(__name__)


# =============================================================================
# Helper Functions (T018-T020)
# =============================================================================


def classify_drug_query(query_text: str) -> QueryType:
    """Classify drug query based on text patterns.

    Rule-based classification mapping query text to SÚKL tool type.

    Args:
        query_text: User's query text.

    Returns:
        QueryType: Classified query type for routing.

    Examples:
        >>> classify_drug_query("Najdi Ibalgin")
        QueryType.SEARCH
        >>> classify_drug_query("Složení Paralenu")
        QueryType.DETAILS
        >>> classify_drug_query("Kolik stojí ibuprofen?")
        QueryType.REIMBURSEMENT
    """
    query_lower = query_text.lower()

    # ATC code pattern (e.g., M01AE01)
    atc_pattern = r"\b[A-Z]\d{2}[A-Z]{2}\d{2}\b"
    if re.search(atc_pattern, query_text, re.IGNORECASE):
        return QueryType.ATC

    # Details keywords
    details_keywords = [
        "složení",
        "indikace",
        "kontraindikace",
        "dávkování",
        "podrobnosti",
        "detaily",
        "popis",
        "složka",
        "příbalový",
        "spc",
        "pil",
    ]
    if any(kw in query_lower for kw in details_keywords):
        return QueryType.DETAILS

    # Reimbursement keywords
    reimbursement_keywords = [
        "cena",
        "úhrada",
        "pojišťovna",
        "kategorie",
        "doplatek",
        "stojí",
        "kolik",
        "hrazeno",
        "vzp",
    ]
    if any(kw in query_lower for kw in reimbursement_keywords):
        return QueryType.REIMBURSEMENT

    # Availability keywords
    availability_keywords = [
        "dostupnost",
        "dostupný",
        "alternativa",
        "náhrada",
        "náhradní",
        "deficit",
        "nedostatek",
        "k dispozici",
    ]
    if any(kw in query_lower for kw in availability_keywords):
        return QueryType.AVAILABILITY

    # Ingredient keywords
    ingredient_keywords = [
        "účinná látka",
        "složka",
        "ingredient",
        "obsahuje",
        "s účinnou",
    ]
    if any(kw in query_lower for kw in ingredient_keywords):
        return QueryType.INGREDIENT

    # Default: search by name
    return QueryType.SEARCH


def drug_result_to_document(result: DrugResult) -> Document:
    """Transform DrugResult to LangChain Document.

    Args:
        result: Drug search result.

    Returns:
        Document: Formatted document with metadata for citations.
    """
    content = (
        f"{result.name} ({result.atc_code}) - Reg. č.: {result.registration_number}"
    )
    if result.manufacturer:
        content += f" - Výrobce: {result.manufacturer}"

    return Document(
        page_content=content,
        metadata={
            "source": "sukl",
            "source_type": "drug_search",
            "registration_number": result.registration_number,
            "atc_code": result.atc_code,
            "match_score": result.match_score,
            "retrieved_at": datetime.now().isoformat(),
        },
    )


def drug_details_to_document(details: DrugDetails) -> Document:
    """Transform DrugDetails to LangChain Document.

    Args:
        details: Complete drug information.

    Returns:
        Document: Formatted document with full drug details.
    """
    content = f"""## {details.name}
**Účinná látka**: {details.active_ingredient}
**ATC kód**: {details.atc_code}
**Léková forma**: {details.pharmaceutical_form or "Neuvedeno"}

### Indikace
{_format_list(details.indications)}

### Dávkování
{details.dosage}

### Kontraindikace
{_format_list(details.contraindications) if details.contraindications else "Nejsou známy"}

### Nežádoucí účinky
{_format_list(details.side_effects) if details.side_effects else "Viz příbalový leták"}
"""

    return Document(
        page_content=content.strip(),
        metadata={
            "source": "sukl",
            "source_type": "drug_details",
            "registration_number": details.registration_number,
            "atc_code": details.atc_code,
            "retrieved_at": datetime.now().isoformat(),
        },
    )


def reimbursement_to_document(info: ReimbursementInfo) -> Document:
    """Transform ReimbursementInfo to LangChain Document.

    Args:
        info: Reimbursement information.

    Returns:
        Document: Formatted document with pricing info.
    """
    category_desc = {
        ReimbursementCategory.A: "Plně hrazeno",
        ReimbursementCategory.B: "Částečně hrazeno",
        ReimbursementCategory.D: "Nehrazeno",
        ReimbursementCategory.N: "Nehodnoceno",
    }

    content = f"""## Úhrada léku (Reg. č.: {info.registration_number})
**Kategorie**: {info.category.value} - {category_desc.get(info.category, "Neznámá")}
**Doplatek**: {info.copay_amount:.2f} Kč
**Vyžaduje recept**: {"Ano" if info.prescription_required else "Ne"}

### Podmínky úhrady
{_format_list(info.conditions) if info.conditions else "Standardní podmínky"}
"""

    return Document(
        page_content=content.strip(),
        metadata={
            "source": "sukl",
            "source_type": "reimbursement",
            "registration_number": info.registration_number,
            "category": info.category.value,
            "retrieved_at": datetime.now().isoformat(),
        },
    )


def availability_to_document(info: AvailabilityInfo) -> Document:
    """Transform AvailabilityInfo to LangChain Document.

    Args:
        info: Availability information.

    Returns:
        Document: Formatted document with availability status.
    """
    status = "✅ Dostupný" if info.is_available else "❌ Nedostupný"

    content = f"""## Dostupnost léku (Reg. č.: {info.registration_number})
**Status**: {status}
"""

    if info.shortage_info:
        content += f"\n**Info o výpadku**: {info.shortage_info}"

    if info.expected_availability:
        content += f"\n**Očekávaná dostupnost**: {info.expected_availability}"

    if info.alternatives:
        content += "\n\n### Alternativní léky\n"
        for alt in info.alternatives:
            content += f"- {alt.name} ({alt.atc_code})\n"

    return Document(
        page_content=content.strip(),
        metadata={
            "source": "sukl",
            "source_type": "availability",
            "registration_number": info.registration_number,
            "is_available": info.is_available,
            "retrieved_at": datetime.now().isoformat(),
        },
    )


def format_mcp_error(error: Exception) -> str:
    """Format MCP error as user-friendly Czech message.

    Args:
        error: MCP exception.

    Returns:
        str: Czech error message for user.
    """
    if isinstance(error, MCPConnectionError):
        return "Nelze se připojit k databázi SÚKL. Zkuste to prosím později."
    elif isinstance(error, MCPTimeoutError):
        return "Dotaz trval příliš dlouho. Zkuste zúžit vyhledávání."
    elif isinstance(error, MCPServerError):
        return "Služba SÚKL je dočasně nedostupná. Zkuste to za chvíli."
    else:
        return f"Při zpracování dotazu došlo k chybě: {str(error)}"


def _format_list(items: List[str]) -> str:
    """Format list items as bullet points."""
    if not items:
        return "- Neuvedeno"
    return "\n".join(f"- {item}" for item in items)


# =============================================================================
# SÚKL Tool Helpers (T024, T030, T035, T040, T045-T046)
# =============================================================================


async def _search_drugs(client: SUKLMCPClient, query: DrugQuery) -> List[DrugResult]:
    """Search drugs by name using SÚKL MCP.

    Args:
        client: SÚKL MCP client.
        query: Drug query with search text.

    Returns:
        List of matching drug results.

    Raises:
        MCPConnectionError, MCPTimeoutError, MCPServerError: On MCP failures.
    """
    logger.debug(f"[drug_agent] Searching drugs: {query.query_text}")

    response = await client.call_tool(
        "search_drugs",
        {"query": query.query_text, "limit": query.limit},
    )

    if not response.success:
        logger.warning(f"[drug_agent] Search failed: {response.error}")
        return []

    results = []
    for drug_data in response.data.get("drugs", []):
        try:
            result = DrugResult(
                name=drug_data.get("name", ""),
                atc_code=drug_data.get("atc_code", ""),
                registration_number=drug_data.get("registration_number", ""),
                manufacturer=drug_data.get("manufacturer"),
                match_score=drug_data.get("match_score"),
            )
            results.append(result)
        except Exception as e:
            logger.warning(f"[drug_agent] Invalid drug data: {e}")
            continue

    logger.info(f"[drug_agent] Found {len(results)} drugs")
    return results


async def _get_drug_details(
    client: SUKLMCPClient, registration_number: str
) -> DrugDetails | None:
    """Get detailed drug information.

    Args:
        client: SÚKL MCP client.
        registration_number: SÚKL registration number.

    Returns:
        DrugDetails or None if not found.
    """
    logger.debug(f"[drug_agent] Getting details for: {registration_number}")

    response = await client.call_tool(
        "get_drug_details",
        {"registration_number": registration_number},
    )

    if not response.success:
        logger.warning(f"[drug_agent] Details lookup failed: {response.error}")
        return None

    data = response.data
    try:
        return DrugDetails(
            registration_number=data.get("registration_number", registration_number),
            name=data.get("name", ""),
            active_ingredient=data.get("active_ingredient", ""),
            composition=data.get("composition", []),
            indications=data.get("indications", []),
            contraindications=data.get("contraindications", []),
            dosage=data.get("dosage", ""),
            side_effects=data.get("side_effects", []),
            pharmaceutical_form=data.get("pharmaceutical_form"),
            atc_code=data.get("atc_code", ""),
        )
    except Exception as e:
        logger.warning(f"[drug_agent] Invalid details data: {e}")
        return None


async def _get_reimbursement(
    client: SUKLMCPClient, registration_number: str
) -> ReimbursementInfo | None:
    """Get reimbursement information for a drug.

    Args:
        client: SÚKL MCP client.
        registration_number: SÚKL registration number.

    Returns:
        ReimbursementInfo or None if not found.
    """
    logger.debug(f"[drug_agent] Getting reimbursement for: {registration_number}")

    response = await client.call_tool(
        "get_reimbursement",
        {"registration_number": registration_number},
    )

    if not response.success:
        return None

    data = response.data
    try:
        category = ReimbursementCategory(data.get("category", "N"))
        return ReimbursementInfo(
            registration_number=data.get("registration_number", registration_number),
            category=category,
            copay_amount=data.get("copay_amount"),
            max_price=data.get("max_price"),
            prescription_required=data.get("prescription_required", True),
            conditions=data.get("conditions", []),
        )
    except Exception as e:
        logger.warning(f"[drug_agent] Invalid reimbursement data: {e}")
        return None


async def _check_availability(
    client: SUKLMCPClient, registration_number: str
) -> AvailabilityInfo | None:
    """Check drug availability and get alternatives.

    Args:
        client: SÚKL MCP client.
        registration_number: SÚKL registration number.

    Returns:
        AvailabilityInfo or None if not found.
    """
    logger.debug(f"[drug_agent] Checking availability for: {registration_number}")

    response = await client.call_tool(
        "check_availability",
        {"registration_number": registration_number, "include_alternatives": True},
    )

    if not response.success:
        return None

    data = response.data
    try:
        alternatives = []
        for alt_data in data.get("alternatives", []):
            try:
                alt = DrugResult(
                    name=alt_data.get("name", ""),
                    atc_code=alt_data.get("atc_code", ""),
                    registration_number=alt_data.get("registration_number", ""),
                    manufacturer=alt_data.get("manufacturer"),
                )
                alternatives.append(alt)
            except Exception:
                continue

        return AvailabilityInfo(
            registration_number=data.get("registration_number", registration_number),
            is_available=data.get("is_available", False),
            shortage_info=data.get("shortage_info"),
            expected_availability=data.get("expected_availability"),
            alternatives=alternatives,
        )
    except Exception as e:
        logger.warning(f"[drug_agent] Invalid availability data: {e}")
        return None


async def _search_by_atc(
    client: SUKLMCPClient, atc_code: str, limit: int = 10
) -> List[DrugResult]:
    """Search drugs by ATC code.

    Args:
        client: SÚKL MCP client.
        atc_code: ATC classification code.
        limit: Maximum results.

    Returns:
        List of matching drug results.
    """
    logger.debug(f"[drug_agent] Searching by ATC: {atc_code}")

    response = await client.call_tool(
        "search_by_atc",
        {"atc_code": atc_code, "limit": limit},
    )

    if not response.success:
        return []

    results = []
    for drug_data in response.data.get("drugs", []):
        try:
            result = DrugResult(
                name=drug_data.get("name", ""),
                atc_code=drug_data.get("atc_code", atc_code),
                registration_number=drug_data.get("registration_number", ""),
                manufacturer=drug_data.get("manufacturer"),
            )
            results.append(result)
        except Exception:
            continue

    return results


async def _search_by_ingredient(
    client: SUKLMCPClient, ingredient: str, limit: int = 10
) -> List[DrugResult]:
    """Search drugs by active ingredient.

    Args:
        client: SÚKL MCP client.
        ingredient: Active ingredient name.
        limit: Maximum results.

    Returns:
        List of matching drug results.
    """
    logger.debug(f"[drug_agent] Searching by ingredient: {ingredient}")

    response = await client.call_tool(
        "search_by_ingredient",
        {"ingredient": ingredient, "limit": limit},
    )

    if not response.success:
        return []

    results = []
    for drug_data in response.data.get("drugs", []):
        try:
            result = DrugResult(
                name=drug_data.get("name", ""),
                atc_code=drug_data.get("atc_code", ""),
                registration_number=drug_data.get("registration_number", ""),
                manufacturer=drug_data.get("manufacturer"),
            )
            results.append(result)
        except Exception:
            continue

    return results


# =============================================================================
# Main Node Function (T025)
# =============================================================================


async def drug_agent_node(
    state: State,
    runtime: Runtime[Context],
) -> Dict[str, Any]:
    """Process drug-related queries using SÚKL MCP.

    LangGraph node for querying Czech pharmaceutical database.
    Implements FR-001 through FR-010.

    Workflow:
    1. Extract drug query from state.drug_query or parse from last message
    2. Classify query type (search, details, reimbursement, availability, atc, ingredient)
    3. Call appropriate SUKLMCPClient method
    4. Transform response to Documents with citations
    5. Return updated state with retrieved_docs and assistant message

    Args:
        state: Current agent state with messages and optional drug_query.
        runtime: Runtime context with sukl_mcp_client.

    Returns:
        Updated state dict with:
            - messages: list with assistant response
            - retrieved_docs: list of Document objects with drug info
            - next: routing indicator (default: __end__)

    Constitution Compliance:
        - Principle I: Async function, proper signature
        - Principle II: Typed state/context, validated with Pydantic
        - Principle IV: Entry/exit logging, LangSmith traceable
        - Principle V: Single responsibility (drug queries only)
    """
    # Entry logging
    logger.info("[drug_agent_node] Starting drug query processing")

    # Get context
    context = runtime.context or {}
    sukl_client: SUKLMCPClient | None = context.get("sukl_mcp_client")

    if not sukl_client:
        logger.error("[drug_agent_node] No SÚKL MCP client in context")
        return {
            "messages": [
                {
                    "role": "assistant",
                    "content": "Chyba konfigurace: SÚKL klient není dostupný.",
                }
            ],
            "retrieved_docs": [],
            "next": "__end__",
        }

    # Extract query
    query: DrugQuery | None = None

    # Priority 1: Explicit drug_query in state
    if state.drug_query:
        query = state.drug_query
        logger.debug(f"[drug_agent_node] Using explicit query: {query.query_text}")

    # Priority 2: Parse from last user message
    if not query and state.messages:
        last_message = state.messages[-1]
        raw_content = (
            last_message.get("content")
            if isinstance(last_message, dict)
            else last_message.content
        )
        # Ensure content is a string
        content: str | None = None
        if isinstance(raw_content, str):
            content = raw_content
        elif isinstance(raw_content, list) and raw_content:
            # Handle list of content blocks (e.g., multimodal)
            first_block = raw_content[0]
            if isinstance(first_block, str):
                content = first_block
            elif isinstance(first_block, dict) and "text" in first_block:
                content = str(first_block["text"])
        if content:
            query_type = classify_drug_query(content)
            query = DrugQuery(query_text=content, query_type=query_type)
            logger.debug(
                f"[drug_agent_node] Parsed query from message: {content[:50]}..."
            )

    if not query:
        logger.warning("[drug_agent_node] No query found")
        return {
            "messages": [
                {
                    "role": "assistant",
                    "content": "Nezadali jste dotaz na lék. Zkuste zadat název léku nebo ATC kód.",
                }
            ],
            "retrieved_docs": [],
            "next": "__end__",
        }

    # Process query based on type
    documents: List[Document] = []
    response_text = ""

    try:
        if query.query_type == QueryType.SEARCH:
            results = await _search_drugs(sukl_client, query)
            if results:
                documents = [drug_result_to_document(r) for r in results]
                response_text = f"Nalezeno {len(results)} léků odpovídajících dotazu '{query.query_text}':\n\n"
                for r in results[:5]:  # Show top 5 in message
                    response_text += f"- **{r.name}** (ATC: {r.atc_code}, Reg.: {r.registration_number})\n"
                if len(results) > 5:
                    response_text += f"\n... a dalších {len(results) - 5} výsledků."
            else:
                response_text = (
                    f"Žádný lék odpovídající '{query.query_text}' nebyl nalezen."
                )

        elif query.query_type == QueryType.DETAILS:
            # First search, then get details of first result
            results = await _search_drugs(sukl_client, query)
            if results:
                details = await _get_drug_details(
                    sukl_client, results[0].registration_number
                )
                if details:
                    documents = [drug_details_to_document(details)]
                    response_text = f"Detailní informace o léku {details.name}:\n\n"
                    response_text += f"**Účinná látka**: {details.active_ingredient}\n"
                    response_text += (
                        f"**Indikace**: {', '.join(details.indications[:3])}\n"
                    )
                    response_text += f"**Dávkování**: {details.dosage}\n"
                else:
                    response_text = "Detaily léku nebyly nalezeny."
            else:
                response_text = f"Lék '{query.query_text}' nebyl nalezen."

        elif query.query_type == QueryType.REIMBURSEMENT:
            results = await _search_drugs(sukl_client, query)
            if results:
                info = await _get_reimbursement(
                    sukl_client, results[0].registration_number
                )
                if info:
                    documents = [reimbursement_to_document(info)]
                    category_desc = {
                        ReimbursementCategory.A: "plně hrazeno",
                        ReimbursementCategory.B: "částečně hrazeno",
                        ReimbursementCategory.D: "nehrazeno",
                        ReimbursementCategory.N: "nehodnoceno",
                    }
                    response_text = "Informace o úhradě léku:\n\n"
                    response_text += f"**Kategorie**: {info.category.value} ({category_desc.get(info.category)})\n"
                    if info.copay_amount is not None:
                        response_text += f"**Doplatek**: {info.copay_amount:.2f} Kč\n"
                    response_text += f"**Vyžaduje recept**: {'Ano' if info.prescription_required else 'Ne'}\n"
                else:
                    response_text = "Informace o úhradě nebyly nalezeny."
            else:
                response_text = f"Lék '{query.query_text}' nebyl nalezen."

        elif query.query_type == QueryType.AVAILABILITY:
            results = await _search_drugs(sukl_client, query)
            if results:
                avail_info = await _check_availability(
                    sukl_client, results[0].registration_number
                )
                if avail_info:
                    documents = [availability_to_document(avail_info)]
                    status = (
                        "dostupný ✅" if avail_info.is_available else "nedostupný ❌"
                    )
                    response_text = f"Lék {results[0].name} je aktuálně {status}.\n"
                    if not avail_info.is_available and avail_info.alternatives:
                        response_text += "\n**Alternativy**:\n"
                        for alt in avail_info.alternatives[:3]:
                            response_text += f"- {alt.name} ({alt.atc_code})\n"
                else:
                    response_text = "Informace o dostupnosti nebyly nalezeny."
            else:
                response_text = f"Lék '{query.query_text}' nebyl nalezen."

        elif query.query_type == QueryType.ATC:
            # Extract ATC code from query
            atc_match = re.search(
                r"\b([A-Z]\d{2}[A-Z]{2}\d{2})\b", query.query_text, re.IGNORECASE
            )
            if atc_match:
                atc_code = atc_match.group(1).upper()
                results = await _search_by_atc(sukl_client, atc_code, query.limit)
                if results:
                    documents = [drug_result_to_document(r) for r in results]
                    response_text = (
                        f"Nalezeno {len(results)} léků s ATC kódem {atc_code}:\n\n"
                    )
                    for r in results[:5]:
                        response_text += (
                            f"- **{r.name}** (Reg.: {r.registration_number})\n"
                        )
                else:
                    response_text = (
                        f"Žádné léky s ATC kódem {atc_code} nebyly nalezeny."
                    )
            else:
                response_text = "Nebyl rozpoznán platný ATC kód ve vašem dotazu."

        elif query.query_type == QueryType.INGREDIENT:
            results = await _search_by_ingredient(
                sukl_client, query.query_text, query.limit
            )
            if results:
                documents = [drug_result_to_document(r) for r in results]
                response_text = (
                    f"Nalezeno {len(results)} léků obsahujících účinnou látku:\n\n"
                )
                for r in results[:5]:
                    response_text += f"- **{r.name}** (ATC: {r.atc_code})\n"
            else:
                response_text = (
                    f"Žádné léky s účinnou látkou '{query.query_text}' nebyly nalezeny."
                )

    except (MCPConnectionError, MCPTimeoutError, MCPServerError) as e:
        logger.error(f"[drug_agent_node] MCP error: {e}")
        response_text = format_mcp_error(e)

    except Exception as e:
        logger.exception(f"[drug_agent_node] Unexpected error: {e}")
        response_text = "Při zpracování dotazu došlo k neočekávané chybě."

    # Add citation reference if documents found
    if documents:
        response_text += "\n\n_Zdroj: SÚKL - Státní ústav pro kontrolu léčiv_"

    # Exit logging
    logger.info(f"[drug_agent_node] Completed. Found {len(documents)} documents.")

    return {
        "messages": [{"role": "assistant", "content": response_text}],
        "retrieved_docs": documents,
        "next": "__end__",
    }
