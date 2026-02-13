"""Synthesizer Node for combining multi-agent responses.

LangGraph node that combines responses from multiple agents into a coherent
Czech medical response with unified citation numbering.
Implements Feature 009 specification.

Constitution Compliance:
- Principle I: Async node function with proper signature
- Principle II: Typed state/context, dataclass models
- Principle IV: LangSmith tracing, logging at boundaries
- Principle V: Single responsibility (response synthesis only)
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage

from agent.utils.timeout import with_timeout

if TYPE_CHECKING:
    from langgraph.runtime import Runtime

    from agent.graph import Context, State

logger = logging.getLogger(__name__)


# =============================================================================
# Czech Medical Abbreviation Dictionary
# =============================================================================

CZECH_MEDICAL_ABBREVIATIONS: dict[str, str] = {
    "DM2T": "diabetes mellitus 2. typu",
    "DM1T": "diabetes mellitus 1. typu",
    "ICHS": "ischemická choroba srdeční",
    "CMP": "cévní mozková příhoda",
    "IM": "infarkt myokardu",
    "TK": "krevní tlak",
    "BMI": "body mass index",
    "GFR": "glomerulární filtrace",
    "HbA1c": "glykovaný hemoglobin",
    "ACEI": "inhibitor angiotensin konvertujícího enzymu",
    "ARB": "blokátor receptorů pro angiotensin",
    "BB": "betablokátor",
    "KV": "kardiovaskulární",
    "GIT": "gastrointestinální trakt",
}

# English abbreviations that should be replaced with Czech equivalents
_ENGLISH_TO_CZECH: dict[str, str] = {
    "T2DM": "DM2T",
    "T1DM": "DM1T",
    "CHD": "ICHS",
    "CVA": "CMP",
    "MI": "IM",
    "BP": "TK",
    "GI": "GIT",
    "CV": "KV",
}

# Agent type detection keywords for compound query section mapping
_AGENT_TYPE_KEYWORDS: dict[str, list[str]] = {
    "drug_agent": ["SÚKL", "SUKL", "registrační", "ATC"],
    "pubmed_agent": ["PubMed", "PMID", "studie", "RCT", "meta-analýz"],
    "guidelines_agent": ["ČLS JEP", "doporučený postup", "guidelines"],
}

# Fixed section headers for compound responses
_AGENT_SECTION_HEADERS: dict[str, str] = {
    "drug_agent": "**Lékové informace (SÚKL)**",
    "pubmed_agent": "**Výzkum (PubMed)**",
    "guidelines_agent": "**Doporučení (Guidelines)**",
}

# Keywords for splitting LLM combined text into agent-specific parts
_AGENT_CONTENT_KEYWORDS: dict[str, list[str]] = {
    "drug_agent": ["SÚKL", "SUKL", "lék", "registr", "ATC"],
    "pubmed_agent": ["PubMed", "PMID", "studie", "člán", "RCT"],
    "guidelines_agent": ["ČLS JEP", "guidelines", "doporučení", "klinick"],
}


# =============================================================================
# Data Models
# =============================================================================


@dataclass
class CitationInfo:
    """Information about a single citation extracted from agent message.

    Attributes:
        original_num: Original citation number in agent's message.
        citation_text: Full citation text (e.g., "SUKL - Ibalgin 400").
        url: URL or identifier (e.g., PMID, SUKL registration number).
    """

    original_num: int
    citation_text: str
    url: str = ""


# =============================================================================
# Helper Functions
# =============================================================================


def extract_citations_from_message(message: str) -> tuple[str, list[CitationInfo]]:
    r"""Parse message and extract inline citations and References section.

    Extracts [N] inline references and parses the References/Zdroj section
    at the end of the message.

    Args:
        message: Agent response message text.

    Returns:
        Tuple of (message_without_references, list_of_citations).

    Examples:
        >>> text = "Ibalgin contains ibuprofen [1].\n\n## References\n[1] SUKL - Ibalgin 400"
        >>> msg, citations = extract_citations_from_message(text)
        >>> len(citations)
        1
    """
    citations: list[CitationInfo] = []

    # Find References section (## References, ## Zdroje, ## Reference, or _Zdroj:)
    references_pattern = (
        r"(?:\n\n)?(?:##\s*(?:References|Zdroje|Reference|Zdroj)\s*\n|_Zdroj:\s*)"
        r"(.*?)$"
    )
    ref_match = re.search(references_pattern, message, re.DOTALL | re.IGNORECASE)

    message_without_refs = message

    if ref_match:
        # Remove references section from message
        message_without_refs = message[: ref_match.start()].rstrip()
        refs_text = ref_match.group(1).strip()

        # Parse individual references: [N] text
        ref_lines = re.findall(
            r"\[(\d+)\]\s*(.+?)(?=\n\[|\n\n|$)", refs_text, re.DOTALL
        )

        if ref_lines:
            for num_str, text in ref_lines:
                citation_text = text.strip()
                # Extract URL if present
                url_match = re.search(
                    r"(https?://\S+|PMID:\s*\d+|doi:\s*\S+)",
                    citation_text,
                    re.IGNORECASE,
                )
                url = url_match.group(1) if url_match else ""
                citations.append(
                    CitationInfo(
                        original_num=int(num_str),
                        citation_text=citation_text,
                        url=url,
                    )
                )
        else:
            # Handle simple _Zdroj: format (no numbered refs)
            citation_text = refs_text.strip().rstrip("_")
            if citation_text:
                citations.append(
                    CitationInfo(
                        original_num=1,
                        citation_text=citation_text,
                        url="",
                    )
                )

    return message_without_refs, citations


def renumber_citations(
    messages: list[str],
    citations: list[list[CitationInfo]],
) -> tuple[list[str], list[str]]:
    """Assign global citation numbering across multiple agent messages.

    Takes messages from multiple agents, each with their own [1][2]... numbering,
    and assigns global sequential numbers. Updates inline references in messages.

    Args:
        messages: List of agent message texts (without References sections).
        citations: List of citation lists, one per agent message.

    Returns:
        Tuple of (updated_messages, global_references_list).

    Examples:
        >>> msgs = ["Drug info [1]", "Study results [1][2]"]
        >>> cits = [
        ...     [CitationInfo(1, "SUKL")],
        ...     [CitationInfo(1, "PMID:123"), CitationInfo(2, "PMID:456")],
        ... ]
        >>> updated, refs = renumber_citations(msgs, cits)
        >>> updated[1]
        'Study results [2][3]'
    """
    updated_messages: list[str] = []
    global_references: list[str] = []
    global_counter = 1

    for msg, msg_citations in zip(messages, citations):
        # Build mapping: original_num -> global_num
        num_mapping: dict[int, int] = {}
        for citation in msg_citations:
            num_mapping[citation.original_num] = global_counter
            global_references.append(f"[{global_counter}] {citation.citation_text}")
            global_counter += 1

        # Replace inline references in message
        updated_msg = msg
        if num_mapping:
            # Replace in reverse order to avoid conflicts (e.g., [10] before [1])
            for old_num in sorted(num_mapping.keys(), reverse=True):
                new_num = num_mapping[old_num]
                updated_msg = updated_msg.replace(
                    f"[{old_num}]", f"[__TEMP_{new_num}__]"
                )
            # Replace temp markers with final numbers
            for new_num in num_mapping.values():
                updated_msg = updated_msg.replace(
                    f"[__TEMP_{new_num}__]", f"[{new_num}]"
                )

        updated_messages.append(updated_msg)

    return updated_messages, global_references


def validate_czech_terminology(text: str) -> dict[str, list[str]]:
    """Check correctness of Czech medical abbreviations in text.

    Validates that commonly used Czech medical abbreviations are used correctly.
    Returns warnings for English abbreviations that should be Czech, and
    suggestions for Czech abbreviations used without expansion.

    Args:
        text: Text to validate.

    Returns:
        Dict with 'warnings' (list of warning strings) and
        'suggestions' (list of suggestion strings).

    Examples:
        >>> result = validate_czech_terminology("Pacient s DM2T a ICHS")
        >>> result['warnings']
        []
        >>> result = validate_czech_terminology("Patient with T2DM")
        >>> len(result['warnings']) > 0
        True
    """
    warnings: list[str] = []
    suggestions: list[str] = []

    # Check for English abbreviations that should be Czech
    for eng, cz in _ENGLISH_TO_CZECH.items():
        # Use word boundary to avoid false matches
        if re.search(rf"\b{re.escape(eng)}\b", text):
            cz_full = CZECH_MEDICAL_ABBREVIATIONS.get(cz, cz)
            warnings.append(
                f"Nalezena anglická zkratka '{eng}' - "
                f"doporučeno použít '{cz}' ({cz_full})"
            )

    # Check Czech abbreviations used without expansion
    for abbr, full_name in CZECH_MEDICAL_ABBREVIATIONS.items():
        if re.search(rf"\b{re.escape(abbr)}\b", text):
            # Check if expansion follows: abbr (full_name...)
            expansion_pattern = (
                rf"\b{re.escape(abbr)}\s*\([^)]*?"
                rf"{re.escape(full_name)}[^)]*\)"
            )
            if not re.search(expansion_pattern, text, re.IGNORECASE):
                suggestions.append(
                    f"Zkratka `{abbr}` bez rozepsání - doporučeno: {abbr} ({full_name})"
                )

    return {"warnings": warnings, "suggestions": suggestions}


def format_response(
    combined_text: str,
    query_type: str,
    agent_types: list[str] | None = None,
) -> str:
    """Format the synthesized response based on query type.

    Structures the response appropriately:
    - quick (single agent): concise, 3-5 sentences via rule-based truncation
    - compound (multiple agents): structured with fixed section headings per agent

    Args:
        combined_text: The synthesized text from LLM.
        query_type: Either "quick" or "compound".
        agent_types: List of detected agent types for compound section headers.

    Returns:
        Formatted response string with footer.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    footer = (
        f"\n\n---\n_Odpověď vygenerována: {timestamp} | "
        "Czech MedAI - klinický rozhodovací nástroj_"
    )

    if query_type == "quick":
        # Rule-based brevity: max 5 sentences
        sentences = re.split(r"(?<=[.!?])\s+", combined_text.strip())
        if len(sentences) > 5:
            combined_text = " ".join(sentences[:5])
            if not combined_text.rstrip().endswith((".", "!", "?")):
                combined_text += "."
        return combined_text + footer

    if query_type == "compound" and agent_types:
        combined_text = _structure_compound_response(combined_text, agent_types)

    return combined_text + footer


def _structure_compound_response(text: str, agent_types: list[str]) -> str:
    """Structure compound response with fixed section headers per agent type.

    Splits the LLM combined text by agent keywords and wraps each part
    in the appropriate fixed section header.

    Args:
        text: Combined text from LLM synthesis.
        agent_types: List of detected agent types.

    Returns:
        Text restructured with fixed section headers.
    """
    # Split text into blocks by existing section headers or double newlines
    blocks = re.split(r"\n{2,}(?=(?:#{1,3}|\*\*)\s)", text.strip())
    if len(blocks) <= 1:
        blocks = text.strip().split("\n\n")

    # Map blocks to agent types by keyword matching
    agent_blocks: dict[str, list[str]] = {at: [] for at in agent_types}
    unmatched: list[str] = []

    for block in blocks:
        block = block.strip()
        if not block:
            continue
        matched = False
        for at in agent_types:
            if at in _AGENT_CONTENT_KEYWORDS:
                kws = _AGENT_CONTENT_KEYWORDS[at]
                if any(kw.lower() in block.lower() for kw in kws):
                    # Remove existing section header if present
                    clean = re.sub(r"^(?:#{1,3}|\*\*)[^\n]*\n?", "", block).strip()
                    if clean:
                        agent_blocks[at].append(clean)
                    matched = True
                    break
        if not matched and block:
            unmatched.append(block)

    # Build structured output with fixed section headers
    result_parts: list[str] = []
    for at in agent_types:
        if at in _AGENT_SECTION_HEADERS and agent_blocks.get(at):
            header = _AGENT_SECTION_HEADERS[at]
            content = "\n\n".join(agent_blocks[at])
            result_parts.append(f"{header}\n{content}")

    if unmatched:
        result_parts.extend(unmatched)

    if result_parts:
        return "\n\n".join(result_parts)

    # Fallback: return original text if no keyword matching worked
    return text


def _detect_agent_types(messages: list[Any]) -> list[str]:
    """Detect agent types from message content keywords.

    Checks assistant message content for known agent-specific keywords
    to determine which agents contributed to the conversation.

    Args:
        messages: List of assistant messages (dict or message objects).

    Returns:
        List of detected agent type strings.
    """
    agent_types: list[str] = []

    for msg in messages:
        content = (
            msg.get("content", "")
            if isinstance(msg, dict)
            else getattr(msg, "content", "")
        )
        if isinstance(content, list):
            content = content[0] if content else ""
            if isinstance(content, dict):
                content = content.get("text", "")
        content = str(content)

        for agent_type, kws in _AGENT_TYPE_KEYWORDS.items():
            if agent_type not in agent_types:
                if any(kw.lower() in content.lower() for kw in kws):
                    agent_types.append(agent_type)

    return agent_types


# =============================================================================
# Main Node Function
# =============================================================================


@with_timeout(timeout_seconds=10.0)
async def synthesizer_node(
    state: State,
    runtime: Runtime[Context],
) -> dict[str, Any]:
    """Combine multi-agent responses into a coherent Czech medical answer.

    Post-processing node that merges responses from parallel agents,
    renumbers citations globally, validates Czech terminology, and
    formats the final response.

    Workflow:
        1. Extract assistant messages from state.messages
        2. For each message: extract citations
        3. Renumber citations globally
        4. Combine messages using LLM (Claude)
        5. Validate Czech terminology
        6. Format response with References section
        7. Return updated state

    Args:
        state: Current agent state with messages from multiple agents.
        runtime: Runtime context with model configuration.

    Returns:
        Updated state dict with:
            - messages: list with synthesized assistant message
            - retrieved_docs: empty list (docs already in state via reducer)
            - next: "__end__"

    Constitution Compliance:
        - Principle I: Async function, proper signature
        - Principle II: Typed state/context
        - Principle IV: Entry/exit logging
        - Principle V: Single responsibility (synthesis only)
    """
    # Extract assistant messages from state
    agent_messages = [
        msg
        for msg in state.messages
        if (isinstance(msg, dict) and msg.get("role") == "assistant")
        or (hasattr(msg, "type") and msg.type == "ai")
    ]

    # Entry logging
    logger.info(
        f"[synthesizer_node] Starting synthesis of "
        f"{len(agent_messages)} agent responses"
    )

    # If no agent messages, return empty
    if not agent_messages:
        logger.warning("[synthesizer_node] No agent messages to synthesize")
        return {
            "messages": [
                {
                    "role": "assistant",
                    "content": "Nebyly nalezeny žádné odpovědi agentů k syntéze.",
                }
            ],
            "retrieved_docs": [],
            "next": "__end__",
        }

    # Extract content from messages
    def _get_content(msg: Any) -> str:
        content = msg.get("content", "") if isinstance(msg, dict) else msg.content
        if isinstance(content, list):
            content = content[0] if content else ""
            if isinstance(content, dict):
                content = content.get("text", "")
        return str(content)

    # If single agent message, pass through with minimal processing
    if len(agent_messages) == 1:
        content = _get_content(agent_messages[0])

        # Extract and re-add citations for consistency
        msg_text, citations = extract_citations_from_message(content)

        # Validate terminology
        validation = validate_czech_terminology(msg_text)
        logger.info(
            f"[synthesizer_node] Terminology: "
            f"warnings={len(validation['warnings'])}, "
            f"suggestions={len(validation['suggestions'])}"
        )

        # Format as quick consult (brevity: 3-5 sentences)
        formatted = format_response(msg_text, "quick")

        # Prepend terminology warning section if applicable
        if validation["warnings"] or validation["suggestions"]:
            warning_section = "## Terminologické upozornění\n"
            if validation["warnings"]:
                warning_section += (
                    "\n".join(f"- {w}" for w in validation["warnings"]) + "\n\n"
                )
            if validation["suggestions"]:
                warning_section += (
                    "\n".join(f"- {s}" for s in validation["suggestions"]) + "\n\n"
                )
            formatted = warning_section.rstrip() + "\n\n" + formatted

        # Add references back
        if citations:
            refs = "\n".join(f"[{c.original_num}] {c.citation_text}" for c in citations)
            formatted += f"\n\n## Reference\n{refs}"

        logger.info(
            f"[synthesizer_node] Completed (single agent). "
            f"Final message length: {len(formatted)} chars"
        )

        return {
            "messages": [{"role": "assistant", "content": formatted}],
            "retrieved_docs": [],
            "next": "__end__",
        }

    # Multiple agent messages - full synthesis
    raw_messages: list[str] = []
    all_citations: list[list[CitationInfo]] = []

    for msg in agent_messages:
        content = _get_content(msg)
        msg_text, citations = extract_citations_from_message(content)
        raw_messages.append(msg_text)
        all_citations.append(citations)

    # Detect agent types from message content
    agent_types = _detect_agent_types(agent_messages)
    logger.info(f"[synthesizer_node] Detected agent types: {agent_types}")

    # Renumber citations globally
    updated_messages, global_references = renumber_citations(
        raw_messages, all_citations
    )

    # Combine using LLM
    context = runtime.context or {}
    model_name = context.get("model_name", "claude-sonnet-4-5-20250929")

    try:
        llm = ChatAnthropic(
            model=model_name,
            temperature=0.0,
            timeout=None,
            stop=None,
            max_tokens=4096,
        )

        # Build synthesis prompt
        agent_sections = "\n\n---\n\n".join(
            f"**Odpověď agenta {i + 1}:**\n{msg}"
            for i, msg in enumerate(updated_messages)
        )

        synthesis_prompt = (
            "Syntetizuj následující odpovědi od specializovaných medicínských "
            "agentů do jedné koherentní české odpovědi.\n\n"
            "Pravidla:\n"
            "1. Zachovej všechny klíčové informace z každého agenta\n"
            "2. Používej přirozený český jazyk s korektní lékařskou terminologií\n"
            "3. Strukturuj odpověď do přehledných sekcí (pro více agentů)\n"
            "4. Zachovej všechny inline citace [N] přesně jak jsou\n"
            "5. NEPŘIDÁVEJ žádné nové informace, pouze syntetizuj existující\n"
            "6. NEpřidávej References sekci - tu přidám já\n"
            "7. Pokud agentovy odpovědi obsahují anglické části (např. PubMed abstrakty), přelož je do češtiny\n\n"
            f"Odpovědi agentů:\n{agent_sections}\n\n"
            "Syntetizovaná odpověď:"
        )

        response = await llm.ainvoke([HumanMessage(content=synthesis_prompt)])
        combined_text = (
            response.content
            if isinstance(response.content, str)
            else str(response.content)
        )

    except Exception as e:
        logger.warning(
            f"[synthesizer_node] LLM synthesis failed: {e} - "
            "falling back to concatenation"
        )
        # Fallback: simple concatenation with section headers
        sections = []
        for i, msg in enumerate(updated_messages):
            sections.append(f"### Výsledky agenta {i + 1}\n\n{msg}")
        combined_text = "\n\n".join(sections)

    # Validate Czech terminology
    validation = validate_czech_terminology(combined_text)
    logger.info(
        f"[synthesizer_node] Terminology: "
        f"warnings={len(validation['warnings'])}, "
        f"suggestions={len(validation['suggestions'])}"
    )

    # Format response with agent types for compound section headers
    formatted = format_response(combined_text, "compound", agent_types)

    # Prepend terminology warning section if applicable
    if validation["warnings"] or validation["suggestions"]:
        warning_section = "## Terminologické upozornění\n"
        if validation["warnings"]:
            warning_section += (
                "\n".join(f"- {w}" for w in validation["warnings"]) + "\n\n"
            )
        if validation["suggestions"]:
            warning_section += (
                "\n".join(f"- {s}" for s in validation["suggestions"]) + "\n\n"
            )
        formatted = warning_section.rstrip() + "\n\n" + formatted

    # Add global references
    if global_references:
        refs_section = "\n".join(global_references)
        formatted += f"\n\n## Reference\n{refs_section}"

    # Exit logging
    logger.info(
        f"[synthesizer_node] Completed. Final message length: {len(formatted)} chars"
    )

    return {
        "messages": [{"role": "assistant", "content": formatted}],
        "retrieved_docs": [],
        "next": "__end__",
    }
