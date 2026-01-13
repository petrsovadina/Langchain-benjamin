# **Project Brief: Czech MedAI (Benjamin)**

**Verze:** 2.2 (Final \- BioMCP Linked) **Datum:** 12\. ledna 2026 **Status:** Schváleno pro vývoj (Ready for Dev)

## **1\. Vize a Hodnota**

**Produkt:** Czech MedAI je inteligentní klinický asistent pro české lékaře, postavený na multi-agentní architektuře LangGraph. **Mise:** Demokratizovat přístup k aktuálním medicínským poznatkům a šetřit lékařům čas (až 312 h/rok) eliminací manuálního rešeršování ve více zdrojích.

**Klíčové propozice (USP):**

1. **Hyper-lokalizace:** Systém rozumí české terminologii, zná úhrady VZP a doporučené postupy ČLS JEP.  
2. **Citation-by-Design:** Každá odpověď obsahuje inline citace (PMID, SÚKL kód) vedoucí na primární zdroj. Prevence halucinací.  
3. **Hybridní Data Layer:** Kombinace vlastních českých databází (SÚKL, VZP) a robustního open-source řešení **BioMCP** pro světovou literaturu.

## **2\. Rozsah MVP (Fáze 1\)**

Následující funkce jsou **povinné** pro první verzi (MVP):

* **F-001 QuickConsult:** Chat rozhraní s odpovědí do 5 sekund (p95) pro běžné dotazy.  
* **F-002 LangGraph Orchestrace:** Implementace "Supervisor-First" architektury se 4 agenty.  
* **F-003 BioMCP Integrace:** Nasazení Docker kontejneru genomoncology/biomcp pro data z PubMedu a ClinicalTrials.  
* **F-004 SÚKL Integrace:** Vyhledávání v SPC a PIL (Custom MCP \+ Supabase pgvector).  
* **F-005 VZP Integrace:** Zobrazení ceny, úhrady a doplatku z číselníku LEK-13.

## **3\. Cílová skupina (Personas)**

1. **Dr. Jana Nováková (Praktická lékařka):** Potřebuje rychle ověřit, zda pojišťovna hradí lék X a jaké má preskripční omezení.  
2. **MUDr. Petr Svoboda (Kardiolog):** Potřebuje najít nejnovější studie o lékové interakci (využije sílu BioMCP pro Clinical Trials).  
3. **Dr. Martin Kučera (Urgent):** Potřebuje okamžitou odpověď pro diferenciální diagnostiku v časovém presu.

## **4\. Technická Strategie**

* **Frontend:** Next.js 14 (App Router), Tailwind, Shadcn/UI.  
* **Backend:** FastAPI (Python), LangGraph, LangChain.  
* **Global Data:** **BioMCP** (Dockerized) – PubMed, ClinicalTrials, Genetics.  
* **Local Data:** Custom MCP Servery (Python) – SÚKL, VZP, ČLS JEP.