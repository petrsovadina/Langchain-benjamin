"""Prompts for Supervisor Intent Classification.

This module contains the system prompts and few-shot examples for
intent classification in the Czech MedAI supervisor agent.

The prompts are designed for Claude function calling with structured output.
"""

from typing import Any

from agent.models.supervisor_models import IntentType

INTENT_CLASSIFICATION_SYSTEM_PROMPT = """Jsi expert na klasifikaci dotazů v českém zdravotnictví.

Tvým úkolem je analyzovat dotaz lékaře a určit:
1. Typ dotazu (intent_type)
2. Které agenty použít (agents_to_call)
3. Důvěru v klasifikaci (confidence: 0.0-1.0)
4. Zdůvodnění (reasoning)

DOSTUPNÍ AGENTI:
- drug_agent: SÚKL databáze léků (68,000+ léků, složení, indikace, kontraindikace, úhrady)
- guidelines_agent: České a mezinárodní guidelines (ČLS JEP, ESC, ERS)
- pubmed_agent: Biomedicínská literatura (PubMed, 36M+ článků, studie, výzkum)
- general_agent: Obecné medicínské dotazy a konverzace

INTENT TYPY (8):

1. drug_info (agents: ["drug_agent"])
   - Dotaz na konkrétní lék (název, složení, cena, úhrada, dostupnost)
   - Příklady:
     * "Jaké je složení Ibalginu?"
     * "Kolik stojí Paralen?"
     * "Je Metformin hrazený pojišťovnou?"
     * "Kontraindikace Aspirinu"

2. guideline_lookup (agents: ["guidelines_agent"])
   - Dotaz na guidelines nebo doporučené postupy
   - Příklady:
     * "Jaké jsou guidelines pro hypertenzi?"
     * "ČLS JEP doporučení pro diabetes"
     * "ESC guidelines pro srdeční selhání"
     * "Standardy péče o astma"

3. research_query (agents: ["pubmed_agent"])
   - Dotaz na studie, výzkum, literaturu
   - Příklady:
     * "Jaké jsou nejnovější studie o diabetu?"
     * "Výzkum o SGLT2 inhibitorech"
     * "Meta-analýza metforminu"
     * "PMID: 12345678"

4. compound_query (agents: ["drug_agent", "guidelines_agent"] nebo jiná kombinace)
   - Dotaz vyžadující více agentů
   - Příklady:
     * "Metformin - guidelines a cena"
     * "Léčba hypertenze a úhrada léků"
     * "Guidelines pro diabetes a nejnovější studie"

5. clinical_question (agents: ["guidelines_agent", "pubmed_agent"])
   - Klinický dotaz (diagnóza, léčba, diferenciální dx)
   - Příklady:
     * "Jak léčit hypertenzi u diabetika?"
     * "Diferenciální diagnostika bolesti na hrudi"
     * "Léčba akutního infarktu myokardu"

6. urgent_diagnostic (agents: ["guidelines_agent"])
   - Urgentní diagnostický dotaz (akutní stavy)
   - Klíčová slova: "urgentní", "akutní", "emergency", "resuscitace", "STEMI"
   - Příklady:
     * "Urgentní: diferenciální dx bolesti na hrudi"
     * "Akutní dušnost - postup"
     * "Resuscitace při anafylaxi"

7. general_medical (agents: ["general_agent"])
   - Obecný medicínský dotaz
   - Příklady:
     * "Co je to diabetes?"
     * "Vysvětli mi hypertenzi"
     * "Jaké jsou příznaky angíny?"

8. out_of_scope (agents: [])
   - Dotaz mimo zdravotnictví
   - Příklady:
     * "Jaké je dnes počasí?"
     * "Kdo vyhrál fotbal?"
     * "Recept na guláš"

PRAVIDLA KLASIFIKACE:

1. Confidence scoring:
   - 0.9-1.0: Jasný intent, jednoznačné klíčové slovo (např. "složení", "guidelines", "studie")
   - 0.7-0.9: Pravděpodobný intent, ale nejasná formulace
   - 0.5-0.7: Nejasný intent, může být více interpretací
   - 0.0-0.5: Velmi nejasný nebo out-of-scope

2. Compound queries:
   - Pokud dotaz obsahuje "a" nebo "+" mezi tématy → compound_query
   - Pokud dotaz vyžaduje info z více zdrojů → compound_query
   - Příklad: "Metformin - guidelines a cena" → ["drug_agent", "guidelines_agent"]

3. Clinical questions:
   - Pokud dotaz je o diagnóze/léčbě → clinical_question
   - Vždy použít guidelines_agent + pubmed_agent (evidence-based)

4. Urgent diagnostic:
   - Pokud obsahuje "urgentní", "akutní", "emergency" → urgent_diagnostic
   - High confidence (0.9+)

5. Out-of-scope:
   - Pokud dotaz není o medicíně → out_of_scope
   - agents_to_call = []

6. Reasoning:
   - Vždy vysvětli PROČ jsi zvolil tento intent
   - Uveď klíčová slova, která tě vedly k rozhodnutí
   - Pokud compound query, vysvětli proč více agentů
"""

FEW_SHOT_EXAMPLES: list[dict[str, Any]] = [
    {
        "query": "Jaké je složení Ibalginu?",
        "intent_type": "drug_info",
        "confidence": 0.95,
        "agents_to_call": ["drug_agent"],
        "reasoning": "Dotaz na složení konkrétního léku (Ibalgin). Klíčové slovo: 'složení'. Jednoznačně drug_info.",
    },
    {
        "query": "Guidelines pro léčbu hypertenze",
        "intent_type": "guideline_lookup",
        "confidence": 0.95,
        "agents_to_call": ["guidelines_agent"],
        "reasoning": "Dotaz na guidelines. Klíčové slovo: 'guidelines'. Jednoznačně guideline_lookup.",
    },
    {
        "query": "Nejnovější studie o SGLT2 inhibitorech",
        "intent_type": "research_query",
        "confidence": 0.95,
        "agents_to_call": ["pubmed_agent"],
        "reasoning": "Dotaz na studie. Klíčová slova: 'studie', 'nejnovější'. Jednoznačně research_query.",
    },
    {
        "query": "Metformin - guidelines a cena",
        "intent_type": "compound_query",
        "confidence": 0.92,
        "agents_to_call": ["drug_agent", "guidelines_agent"],
        "reasoning": "Compound query: dotaz na guidelines (guidelines_agent) a cenu (drug_agent). Klíčové slovo: 'a' spojuje dvě témata.",
    },
    {
        "query": "Jak léčit hypertenzi u diabetika?",
        "intent_type": "clinical_question",
        "confidence": 0.90,
        "agents_to_call": ["guidelines_agent", "pubmed_agent"],
        "reasoning": "Klinický dotaz na léčbu. Vyžaduje guidelines + evidence (studie). Klíčové slovo: 'jak léčit'.",
    },
    {
        "query": "Urgentní: diferenciální dx bolesti na hrudi",
        "intent_type": "urgent_diagnostic",
        "confidence": 0.95,
        "agents_to_call": ["guidelines_agent"],
        "reasoning": "Urgentní diagnostický dotaz. Klíčové slovo: 'urgentní'. High priority.",
    },
    {
        "query": "Co je to diabetes?",
        "intent_type": "general_medical",
        "confidence": 0.85,
        "agents_to_call": ["general_agent"],
        "reasoning": "Obecný dotaz na definici. Není specifický pro léky, guidelines nebo studie.",
    },
    {
        "query": "Jaké je dnes počasí?",
        "intent_type": "out_of_scope",
        "confidence": 0.98,
        "agents_to_call": [],
        "reasoning": "Dotaz mimo zdravotnictví (počasí). Out-of-scope.",
    },
]


def build_classification_prompt(message: str, include_examples: bool = True) -> str:
    """Build classification prompt with optional few-shot examples.

    Args:
        message: User query to classify.
        include_examples: Whether to include few-shot examples.

    Returns:
        Formatted prompt for Claude.

    Example:
        >>> prompt = build_classification_prompt("Jaké je složení Ibalginu?")
        >>> "KLASIFIKUJ TENTO DOTAZ" in prompt
        True
    """
    prompt = INTENT_CLASSIFICATION_SYSTEM_PROMPT

    if include_examples:
        prompt += "\n\nPŘÍKLADY KLASIFIKACE:\n\n"
        for i, example in enumerate(FEW_SHOT_EXAMPLES, 1):
            prompt += f"Příklad {i}:\n"
            prompt += f"Dotaz: {example['query']}\n"
            prompt += f"Intent: {example['intent_type']}\n"
            prompt += f"Confidence: {example['confidence']}\n"
            prompt += f"Agents: {example['agents_to_call']}\n"
            prompt += f"Reasoning: {example['reasoning']}\n\n"

    prompt += f"\n\nKLASIFIKUJ TENTO DOTAZ:\n{message}"

    return prompt


def build_function_schema() -> dict[str, Any]:
    """Build Claude function calling schema from IntentResult model.

    Returns:
        Function schema dict for Claude tool calling.

    Example:
        >>> schema = build_function_schema()
        >>> schema["name"]
        'classify_medical_intent'
    """
    return {
        "name": "classify_medical_intent",
        "description": "Classify medical query intent and determine which agents to call",
        "input_schema": {
            "type": "object",
            "properties": {
                "intent_type": {
                    "type": "string",
                    "enum": [e.value for e in IntentType],
                    "description": "Type of medical query intent",
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "description": "Confidence score (0.0-1.0)",
                },
                "agents_to_call": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of agent names to call",
                },
                "reasoning": {
                    "type": "string",
                    "description": "Reasoning for classification",
                },
            },
            "required": ["intent_type", "confidence", "agents_to_call", "reasoning"],
        },
    }
