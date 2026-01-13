# **BioMCP Integration Specification**

**Komponenta:** Global Research Layer **Zdroj:** [genomoncology/biomcp](https://github.com/genomoncology/biomcp) **Verze:** 1.0 (Implementation Draft)

## **1\. Účel Komponenty**

BioMCP (Bioinformatics Model Context Protocol) slouží jako **brána do světové medicínské literatury**. V architektuře Czech MedAI nahrazuje potřebu psát vlastní strivery (scrapers) pro PubMed a ClinicalTrials.gov.

**Klíčové funkce pro MVP:**

1. **PubMed Search:** Vyhledávání v 36M+ abstraktech (MEDLINE).  
2. **Clinical Trials:** Přehled probíhajících klinických studií (pro onkologii/kardiologii).  
3. **Semantic Mapping:** BioMCP interně řeší mapování synonym (např. *Trastuzumab* \= *Herceptin*).

## **2\. Technická Implementace (Docker)**

BioMCP běží jako izolovaný mikroservis. Využijeme oficiální Docker image.

### **2.1 Konfigurace (docker-compose.yml)**

services:  
  biomcp:  
    image: genomoncology/biomcp:latest  
    container\_name: czech\_medai\_biomcp  
    ports:  
      \- "8000:8000" \# MCP Server endpoint  
    environment:  
      \- BIOMCP\_TOOLS=pubmed,clinical\_trials \# Aktivujeme jen potřebné nástroje  
      \- LOG\_LEVEL=info  
    networks:  
      \- medai\_network  
    restart: always

## **3\. Rozhraní Nástrojů (Tool Definitions)**

LangGraph Supervisor bude volat BioMCP prostřednictvím těchto definovaných nástrojů. BioMCP je exponuje automaticky, ale náš agent\_research je musí umět využít.

### **A. article\_searcher (PubMed)**

Používá se pro dohledání publikovaných studií a meta-analýz.

* **Input Schema:**  
  {  
    "query": "efficacy of SGLT2 inhibitors in heart failure",  
    "retmax": 5,  
    "email": "dev@czechmedai.cz" // Vyžadováno NCBI pro identifikaci  
  }

* **Output Data:**  
  * uid: PMID (např. "34567890")  
  * title: Název článku  
  * abstract: Plný text abstraktu  
  * pubdate: Datum publikace  
  * source: Název žurnálu (např. "N Engl J Med")

### **B. trial\_searcher (ClinicalTrials.gov)**

Používá se pro dotazy na nové, dosud nepublikované léčebné postupy.

* **Input Schema:**  
  {  
    "condition": "Non-small cell lung cancer",  
    "intervention": "Immunotherapy",  
    "status": "RECRUITING" // Volitelné filtrování  
  }

## **4\. LangGraph Integrace (Workflow)**

Integrace BioMCP do českého systému vyžaduje **"Sandwich Pattern"** (Překlad \-\> Dotaz \-\> Překlad), protože BioMCP neumí česky.

### **Logika agent\_research Node:**

1. **Input (CZ):** *"Jaké jsou nejnovější studie o léčbě srdečního selhání inhibitory SGLT2?"*  
2. **Step 1: Translation (LLM):** Agent přeloží dotaz do anglické odborné terminologie.  
   * *Prompt:* Translate medical query to English keywords: "SGLT2 inhibitors heart failure efficacy"  
3. **Step 2: BioMCP Call:** Agent zavolá nástroj article\_searcher.  
   * *Action:* biomcp.call("article\_searcher", query="SGLT2 inhibitors heart failure efficacy")  
4. **Step 3: Processing:** BioMCP vrátí JSON s 5 abstrakty v angličtině.  
5. **Step 4: Synthesis & Localization (LLM):** Agent vybere relevantní informace, přeloží je do češtiny a přidá citace.  
   * *Output:* "Dle studie z NEJM (2025) snižují inhibitory SGLT2 riziko hospitalizace o 30%$$1$$  
     ."

### **Diagram toku dat**

sequenceDiagram  
    participant U as User (CZ)  
    participant S as Supervisor  
    participant A as Research Agent  
    participant B as BioMCP (Docker)  
    participant P as PubMed API (External)

    U-\>\>S: "Existují studie na lék X?"  
    S-\>\>A: Activate Agent  
    A-\>\>A: Translate CZ \-\> EN keywords  
    A-\>\>B: Call tool: article\_searcher(keywords)  
    B-\>\>P: GET /esearch & /esummary  
    P--\>\>B: XML Data  
    B--\>\>A: JSON List (Abstracts)  
    A-\>\>A: Summarize & Translate EN \-\> CZ  
    A--\>\>S: Final Answer with Citations  
    S--\>\>U: Display Response

## **5\. Zpracování chyb a Limitace**

* **Latency:** Volání NCBI API může trvat 2-4 sekundy.  
  * *Řešení:* Frontend musí zobrazovat stav 🌍 BioMCP: Kontaktuji databázi PubMed....  
* **Rate Limiting:** NCBI omezuje požadavky bez API klíče.  
  * *Řešení:* V produkci je nutné do BioMCP kontejneru přidat NCBI\_API\_KEY.  
* **Kontextové okno:** 5 abstraktů může zaplnit kontext modelu.  
  * *Řešení:* BioMCP vrací pouze abstrakty, ne plné texty (PDF). To je pro MVP dostačující.

## **6\. Příklad Výstupu (JSON pro Frontend)**

Když BioMCP vrátí data, frontend obdrží strukturovanou citaci:

{  
  "citation\_id": "1",  
  "source\_type": "PUBMED",  
  "title": "Dapagliflozin in Patients with Heart Failure and Reduced Ejection Fraction",  
  "metadata": {  
    "pmid": "31535829",  
    "journal": "N Engl J Med",  
    "year": "2019",  
    "authors": "McMurray JJV et al.",  
    "url": "\[https://pubmed.ncbi.nlm.nih.gov/31535829/\](https://pubmed.ncbi.nlm.nih.gov/31535829/)"  
  }  
}

