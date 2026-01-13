# **Hloubková Analýza Architektury: Czech MedAI (Benjamin)**

Verze: 2.0 (BioMCP Integration)  
Architektonický styl: Supervisor-First Hybrid Multi-Agent System

## **1\. Filosofie: Proč "Supervisor-First"?**

Tradiční RAG (Retrieval-Augmented Generation) systémy selhávají na komplexních dotazech, protože se snaží narvat všechen kontext do jednoho promptu.

* *Příklad selhání:* "Jaká je úhrada léku X a co říkají studie o jeho vedlejších účincích?" \-\> Tradiční RAG by mohl smíchat informace z příbalového letáku (ČR) se studií z USA, kde je lék registrován pod jiným názvem a má jinou cenu.

Náš přístup:  
Systém se chová jako nemocniční tým.

1. **Supervisor (Primář):** Nepracuje, jen rozděluje úkoly. *"Ty zjisti cenu (VZP), ty najdi studie (BioMCP)."*  
2. **Agenti (Specialisté):** Každý řeší jen svůj malý úkol a neví o ostatních.  
3. **Synthesizer (Sekretář):** Spojí zprávy od specialistů do jedné propouštěcí zprávy.

## **2\. Jádro Systému: LangGraph Orchestrace**

LangGraph nám umožňuje definovat workflow jako orientovaný graf (State Machine).

### **2.1 State Schema (Paměť Grafu)**

Toto je "objekt", který si uzly mezi sebou předávají.

class AgentState(TypedDict):  
    \# Historie konverzace (User \+ AI messages)  
    messages: Annotated\[list\[AnyMessage\], add\_messages\]  
      
    \# Kdo je na řadě (např. "agent\_sukl", "agent\_biomcp", "\_\_end\_\_")  
    next: str  
      
    \# Strukturovaná data získaná agenty (pro Synthesizer)  
    \# Oddělujeme raw data od textové konverzace pro lepší citování  
    retrieved\_docs: list\[Document\] 

### **2.2 Supervisor Node (The Router)**

Využívá LLM (Claude 3.5 Sonnet) v režimu function\_calling nebo structured\_output.

* **Vstup:** Dotaz uživatele.  
* **Logika:** Klasifikace do 8 intentů.  
* **Výstup:** JSON s pokyny.

*Příklad rozhodnutí Supervisora:*

{  
  "next": \["agent\_local", "agent\_research"\],  
  "instructions": {  
    "agent\_local": "Najdi SPC pro lék 'Prestarium Neo'.",  
    "agent\_research": "Hledaj studie o 'perindopril efficacy in elderly'."  
  }  
}

## **3\. Datová Vrstva: Hybridní MCP Strategie**

Zde se děje magie integrace dat. Používáme protokol **MCP (Model Context Protocol)**, abychom oddělili logiku AI od logiky databází.

### **A. Lokální Vrstva (Proprietární) 🇨🇿**

Agent: agent\_local | Server: sukl-mcp & vzp-mcp

Toto musíme napsat my, protože česká data jsou specifická.

**1\. SÚKL (Vector Search):**

* **Problém:** Lékař napíše "lék na tlak", ale v databázi je "antihypertenzivum". SQL LIKE dotaz selže.  
* **Řešení:** Embeddings (Vektory).  
  * Každý odstavec SPC dokumentu převedeme na vektor (pole 1536 čísel) pomocí modelu text-embedding-3-small.  
  * Uložíme do **Supabase** (tabulka s indexem HNSW).  
  * Při dotazu hledáme "kosinovou podobnost".

**2\. VZP (Exact Search):**

* **Problém:** Ceny musí být přesné na haléř. Vektory zde nelze použít (halucinují čísla).  
* **Řešení:** SQL/Pandas.  
  * Stahujeme CSV LEK-13 (číselník VZP).  
  * Vyhledáváme přesně podle kódu SÚKL nebo normalizovaného názvu.

### **B. Globální Vrstva (Open Source) 🌍**

Agent: agent\_research | Server: biomcp (Docker)

Zde využíváme vaši nalezenou knihovnu **BioMCP**.

The "Sandwich" Pattern (Překladová vrstva):  
Protože BioMCP a PubMed neumí česky, musíme agenta obalit logikou:

1. **Horní vrstva (Pre-processing):**  
   * LLM přeloží český dotaz na anglická klíčová slova \+ MeSH termíny.  
   * *CZ:* "Léčba srdečního selhání" \-\> *EN:* "Heart failure therapy OR Cardiac failure treatment".  
2. **Střední vrstva (Execution):**  
   * Volání Docker kontejneru BioMCP (article\_searcher).  
3. **Spodní vrstva (Post-processing):**  
   * BioMCP vrátí 5 abstraktů v angličtině.  
   * LLM je analyzuje, vytáhne fakta a **přeloží je do češtiny**.  
   * Přidá citaci \[PubMed: 12345\].

## **4\. Infrastrukturní Pohled (Docker & Network)**

Aplikace běží jako sada kontejnerů.

graph TD  
    subgraph "Frontend Layer"  
        NextJS\[Next.js App\]  
    end

    subgraph "Backend Layer (Private Network)"  
        FastAPI\[FastAPI / LangGraph\]  
          
        subgraph "MCP Ecosystem"  
            BioMCP\[🐳 BioMCP Container\]  
            SuklMCP\[🐍 Custom SÚKL Service\]  
        end  
          
        DB\[(Supabase / Postgres)\]  
    end

    NextJS \--HTTPS/SSE--\> FastAPI  
    FastAPI \--HTTP/JSONRPC--\> BioMCP  
    FastAPI \--Function Call--\> SuklMCP  
    SuklMCP \--SQL--\> DB  
    BioMCP \--External API--\> PubMedCloud((NCBI Cloud))

## **5\. Tok Dat (User Journey)**

Sledujme jeden kompletní request:

1. **User:** "Jaké jsou vedlejší účinky léku Ozempic?"  
2. **FastAPI:** Otevře SSE stream spojení.  
3. **Supervisor:**  
   * Vidí "Ozempic" (název léku).  
   * Vidí "vedlejší účinky" (klinický dotaz).  
   * Rozhodnutí: Volám agent\_local (SÚKL má oficiální data o NÚ).  
4. **Agent Local:**  
   * Volá sukl-mcp.search\_spc("Ozempic", section="4.8 Nežádoucí účinky").  
5. **SÚKL MCP:**  
   * Dělá vektorový dotaz do Supabase.  
   * Vrací 3 relevantní textové "chunks" z SPC.  
6. **Synthesizer:**  
   * Dostane raw text z SPC.  
   * Zformátuje odpověď: "**Nejčastější nežádoucí účinky:** Nevolnost, průjem... \[SÚKL: Ozempic SPC\]".  
7. **Frontend:** Vykreslí text a modrý badge \[SÚKL\].

## **6\. Bezpečnost a Audit**

* **Stateless Processing:** Jakmile je odpověď odeslána, paměť AgentState se maže (pokud uživatel explicitně neukládá historii).  
* **Audit Log:** Do samostatné tabulky ukládáme:  
  * Timestamp  
  * Anonymizované ID uživatele  
  * Použité zdroje (např. "SÚKL ID 12345", "PubMed ID 99999")  
  * *Nikdy neukládáme jméno pacienta, pokud ho lékař omylem zadal.*

Shrnutí pro vývojáře:  
Stavíme modulární skládačku.

1. Nemusíte rozumět celému systému.  
2. Pokud děláte na BioMCP, zajímá vás jen překlad EN\<-\>CZ.  
3. Pokud děláte na SÚKL, zajímá vás ETL pipeline pro data.  
4. Vše spojuje LangGraph Supervisor.