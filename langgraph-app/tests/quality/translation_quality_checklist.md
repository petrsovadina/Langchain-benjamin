# Translation Quality Validation Checklist (T068 - SC-002)

**Success Criterion SC-002**: Czech medical queries translated with 95% semantic preservation

**Validation Method**: Manual expert review by Czech-speaking medical professional

## Purpose

Validate that the Sandwich Pattern (CZ → EN → PubMed → EN → CZ) preserves medical semantics across both translation steps:
1. **CZ → EN**: Czech query → English PubMed search query
2. **EN → CZ**: English abstract → Czech abstract for physician

## Validation Protocol

### Participants
- **Reviewer**: Czech-speaking physician or medical translator
- **Sample Size**: Minimum 20 query-abstract pairs (to achieve statistical significance)
- **Scoring**: 1-5 scale (1=poor, 5=excellent semantic preservation)
- **Passing Threshold**: 95% of pairs score ≥4 (good or excellent preservation)

### Test Scenarios

#### Query Translation (CZ → EN) - 10 Samples

Test diverse medical query types to validate query translation quality:

| # | Czech Query | Expected English Query | Actual English Query | Score (1-5) | Notes |
|---|-------------|------------------------|----------------------|-------------|-------|
| 1 | Jaké jsou nejnovější studie o diabetu typu 2? | What are the latest studies on type 2 diabetes? | _(fill in)_ | _(1-5)_ | |
| 2 | Studie za poslední 2 roky o hypertenzi | Studies from the last 2 years on hypertension | _(fill in)_ | _(1-5)_ | Date filter preservation |
| 3 | Účinnost metforminu u diabetu typu 2 | Efficacy of metformin in type 2 diabetes | _(fill in)_ | _(1-5)_ | Drug name preservation |
| 4 | Kardiovaskulární rizika SGLT2 inhibitorů | Cardiovascular risks of SGLT2 inhibitors | _(fill in)_ | _(1-5)_ | Technical terminology |
| 5 | Léčba chronické obstrukční plicní nemoci (CHOPN) | Treatment of chronic obstructive pulmonary disease (COPD) | _(fill in)_ | _(1-5)_ | Acronym handling |
| 6 | Klinické studie nových antikoagulancií | Clinical studies of novel anticoagulants | _(fill in)_ | _(1-5)_ | Clinical terminology |
| 7 | Vedlejší účinky statinů u starších pacientů | Side effects of statins in elderly patients | _(fill in)_ | _(1-5)_ | Age group specificity |
| 8 | Doporučení pro screening rakoviny prsu | Guidelines for breast cancer screening | _(fill in)_ | _(1-5)_ | Guideline queries |
| 9 | Studie o interakcích léků s warfarinem | Studies on drug interactions with warfarin | _(fill in)_ | _(1-5)_ | Drug interactions |
| 10 | Prevence kardiovaskulárních onemocnění u diabetiků | Prevention of cardiovascular diseases in diabetics | _(fill in)_ | _(1-5)_ | Multi-condition query |

**Query Translation Scoring Criteria**:
- **5 (Excellent)**: Perfect semantic preservation, all medical terms correct, search would return optimal results
- **4 (Good)**: Minor wording differences, all key concepts preserved, would return relevant results
- **3 (Acceptable)**: Some semantic drift, key concepts mostly preserved, might miss some relevant results
- **2 (Poor)**: Significant semantic loss, missing key concepts, would return suboptimal results
- **1 (Unacceptable)**: Major mistranslation, critical information lost, would fail to return relevant results

#### Abstract Translation (EN → CZ) - 10 Samples

Test medical abstract translation from English to Czech:

| # | English Abstract (Excerpt) | Expected Czech Translation | Actual Czech Translation | Score (1-5) | Notes |
|---|----------------------------|----------------------------|--------------------------|-------------|-------|
| 1 | Background: Metformin is a first-line therapy for type 2 diabetes mellitus. Methods: 200 patients were randomized... | Východiska: Metformin je léčbou první volby pro diabetes mellitus typu 2. Metody: 200 pacientů bylo randomizováno... | _(fill in)_ | _(1-5)_ | Drug therapy translation |
| 2 | Results: HbA1c decreased by 1.5% in the metformin group vs 0.2% in placebo (p<0.001). | Výsledky: HbA1c se snížil o 1,5 % ve skupině s metforminem oproti 0,2 % v placebu (p<0,001). | _(fill in)_ | _(1-5)_ | Statistical data preservation |
| 3 | Adverse events included gastrointestinal symptoms (15%), headache (8%), and dizziness (3%). | Nežádoucí účinky zahrnovaly gastrointestinální příznaky (15 %), bolest hlavy (8 %) a závratě (3 %). | _(fill in)_ | _(1-5)_ | Side effects terminology |
| 4 | Conclusion: Metformin is effective for glycemic control in newly diagnosed type 2 diabetes patients. | Závěr: Metformin je účinný pro kontrolu glykémie u nově diagnostikovaných pacientů s diabetem typu 2. | _(fill in)_ | _(1-5)_ | Clinical conclusion |
| 5 | A randomized, double-blind, placebo-controlled trial evaluated the efficacy of atorvastatin 40mg daily. | Randomizovaná, dvojitě zaslepená, placebem kontrolovaná studie hodnotila účinnost atorvastatinu 40 mg denně. | _(fill in)_ | _(1-5)_ | Study design terminology |
| 6 | Inclusion criteria: patients aged 40-75 years with LDL cholesterol >4.0 mmol/L. | Kritéria zařazení: pacienti ve věku 40–75 let s LDL cholesterolem >4,0 mmol/l. | _(fill in)_ | _(1-5)_ | Eligibility criteria |
| 7 | The primary endpoint was major adverse cardiovascular events (MACE) at 12 months. | Primárním cílovým ukazatelem byly závažné nežádoucí kardiovaskulární příhody (MACE) ve 12 měsících. | _(fill in)_ | _(1-5)_ | Clinical endpoints |
| 8 | Subgroup analysis showed greater benefit in patients with baseline HbA1c >9%. | Analýza podskupin ukázala větší přínos u pacientů s výchozím HbA1c >9 %. | _(fill in)_ | _(1-5)_ | Subgroup analysis |
| 9 | Limitations include single-center design and relatively short follow-up duration. | Omezení zahrnují jednoc entrový design a relativně krátkou dobu sledování. | _(fill in)_ | _(1-5)_ | Study limitations |
| 10 | Further research is needed to confirm these findings in larger, multi-center trials. | Je potřeba dalšího výzkumu k potvrzení těchto zjištění ve větších, multicentrických studiích. | _(fill in)_ | _(1-5)_ | Future directions |

**Abstract Translation Scoring Criteria**:
- **5 (Excellent)**: Perfect medical Czech, all technical terms correct, natural phrasing, physician-ready
- **4 (Good)**: Minor grammatical issues, all medical concepts correct, understandable and usable
- **3 (Acceptable)**: Some awkward phrasing, medical concepts mostly correct, requires minor editing
- **2 (Poor)**: Significant grammatical errors, some medical terms incorrect, requires substantial editing
- **1 (Unacceptable)**: Major mistranslations, critical medical errors, unusable for clinical decision-making

## Validation Procedure

### Step 1: Sample Selection
1. Generate 10 diverse Czech medical queries covering common use cases
2. Execute full Sandwich Pattern workflow for each query
3. Select top result abstract from each query for translation validation
4. Total: 20 samples (10 query translations + 10 abstract translations)

### Step 2: Expert Review
1. Provide reviewer with:
   - Source text (Czech query or English abstract)
   - System-generated translation
   - Expected/ideal translation (reference)
   - Scoring criteria
2. Reviewer scores each sample independently (1-5)
3. Reviewer notes any critical issues or patterns

### Step 3: Analysis
1. Calculate percentage of samples scoring ≥4:
   - Query translations: ___ / 10 (___%)
   - Abstract translations: ___ / 10 (___%)
   - Overall: ___ / 20 (___%)
2. **Pass Threshold**: ≥95% (19/20 samples score ≥4)

### Step 4: Issue Documentation
For any sample scoring <4, document:
- **Issue Category**: Terminology error, grammatical error, semantic drift, missing information, etc.
- **Severity**: Critical (impacts clinical decision), Major (confusing), Minor (awkward phrasing)
- **Root Cause**: Prompt engineering, model limitation, context issue, etc.
- **Recommended Fix**: Prompt modification, fine-tuning, post-processing, etc.

## Results Template

**Validation Date**: ____________
**Reviewer Name**: ____________
**Reviewer Credentials**: ____________

### Summary Statistics

| Metric | Query Translation | Abstract Translation | Overall |
|--------|-------------------|----------------------|---------|
| Mean Score | _____ / 5 | _____ / 5 | _____ / 5 |
| % Scoring ≥4 | _____ % | _____ % | _____ % |
| Pass/Fail (≥95%) | _____ | _____ | _____ |

### Critical Issues Identified

_(List any samples scoring <4 with issue descriptions)_

1. **Sample #__**: _(describe issue)_
   - **Severity**: _____
   - **Root Cause**: _____
   - **Recommended Fix**: _____

### Reviewer Comments

_(Free-form feedback on overall translation quality, patterns observed, suggestions for improvement)_

---

## Automation Considerations

While this checklist requires manual expert review for initial validation, consider these automation opportunities for continuous monitoring:

1. **BLEU Score Monitoring**: Track BLEU scores for query and abstract translations (automated metric)
2. **Reference Translation Database**: Build database of expert-validated query translations for automated comparison
3. **Terminology Consistency Checks**: Automated checks for consistent medical term usage
4. **Regression Testing**: Re-run validated samples after prompt/model changes to detect quality degradation

## Acceptance Criteria (SC-002)

- ✅ **PASS**: ≥95% of samples score ≥4 (19+/20 samples)
- ❌ **FAIL**: <95% of samples score ≥4 (<19/20 samples) → Requires prompt engineering improvements or model fine-tuning

**Next Steps on Failure**:
1. Analyze failure patterns (terminology, grammar, semantic drift)
2. Update translation prompts with examples of correct translations
3. Consider medical terminology glossary injection
4. Re-validate with new 20-sample set
5. Iterate until passing threshold achieved

---

**Document Version**: 1.0
**Feature**: 005-biomcp-pubmed-agent
**Success Criterion**: SC-002
**Task ID**: T068
