"""Translation prompt templates for Czech ↔ English medical translation.

This module defines specialized prompts for translating medical queries
and abstracts between Czech and English, preserving medical terminology
and maintaining semantic accuracy (Feature 005).
"""

# Czech → English translation prompt for PubMed queries
CZ_TO_EN_PROMPT = """Translate the following Czech medical query to English for PubMed search.

CRITICAL RULES:
1. Preserve Latin medical terms unchanged (e.g., diabetes mellitus, hypertensio, myocardium)
2. Preserve drug names unchanged (e.g., Metformin, Ibalgin, Aspirin)
3. Preserve anatomical terms unchanged (e.g., myocardium, cerebrum, ventriculus)
4. Expand Czech medical abbreviations to full English terms:
   - DM2 → type 2 diabetes / type 2 diabetes mellitus
   - ICHS → ischemic heart disease / coronary artery disease
   - TEN → pulmonary embolism
   - IM → myocardial infarction
   - CMP → cerebrovascular accident / stroke
   - CHOPN → chronic obstructive pulmonary disease / COPD
   - AS → atrial septal defect (or aortic stenosis based on context)
   - HT → hypertension / arterial hypertension
5. Maintain medical precision - do not simplify terminology
6. Optimize for PubMed search effectiveness (use standard medical terminology)
7. Keep the query concise and focused on search terms

Czech query: {czech_query}

English translation (query only, no explanations):"""

# English → Czech translation prompt for PubMed abstracts
EN_TO_CZ_PROMPT = """Translate the following English medical abstract to professional Czech suitable for physicians.

CRITICAL RULES:
1. Use formal medical register appropriate for Czech physicians
2. Preserve Latin medical terms unchanged (e.g., diabetes mellitus, myocardium, ventriculus)
3. Preserve drug names unchanged (e.g., Metformin, Aspirin)
4. Preserve abbreviations if standard in Czech medical literature (e.g., CHOPN, DM2, ICHS)
5. Use standard Czech medical terminology from Czech medical textbooks and journals
6. Maintain paragraph structure and formatting
7. Translate study design terms accurately:
   - randomized controlled trial → randomizovaná kontrolovaná studie (RCT)
   - double-blind → dvojitě zaslepený
   - placebo-controlled → placebo-kontrolovaný
   - meta-analysis → metaanalýza
   - systematic review → systematický přehled
   - cohort study → kohortová studie
   - case-control study → případová kontrolní studie
8. Preserve numeric data exactly (p-values, confidence intervals, sample sizes)
9. Use passive voice where appropriate (common in Czech medical writing)
10. Maintain professional tone throughout

English abstract: {english_abstract}

Czech translation (abstract only, no explanations):"""
