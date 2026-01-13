# **Product Requirements Document (MVP)**

Projekt: Czech MedAI (Benjamin)  
Dokument: PRD v2.2  
Datum: 12\. ledna 2026

## **1\. Epics & User Stories**

### **Epic 1: QuickConsult (Rychlé klinické dotazy)**

*Cíl: Okamžitá pomoc v ordinaci.*

* **US-1.1:** Jako lékař chci zadat dotaz v přirozené češtině (např. "dávkování metforminu u CKD"), abych nemusel hledat klíčová slova.  
* **US-1.2:** Jako lékař chci dostat strukturovanou odpověď (Markdown), kde jsou klíčové informace zvýrazněny tučně.  
* **US-1.3:** Jako lékař chci vidět indikátor "myšlení" systému (např. "BioMCP: Prohledávám ClinicalTrials..."), abych věděl, že systém pracuje.

### **Epic 2: Evidence & Citace (Trust Layer)**

*Cíl: 100% auditovatelnost.*

* **US-2.1:** Jako lékař chci, aby každé tvrzení mělo inline citaci \[x\].  
* **US-2.2:** Při dotazu na mezinárodní studie chci, aby systém prohledal nejen PubMed, ale i registr klinických studií (BioMCP: trial\_searcher).  
* **US-2.3:** Citace musí jasně odlišovat zdroj: \[SÚKL\], \[PubMed\], \[VZP\], \[Trial\].  
* **US-2.4:** Po kliknutí na citaci se musí zobrazit detail zdroje (abstrakt/SPC) bez opuštění kontextu.

### **Epic 3: Informace o lécích a úhradách (Local Context)**

*Cíl: Propojení kliniky s ekonomikou.*

* **US-3.1:** Jako lékař chci při dotazu na lék vidět sekci "Úhrada VZP" (Max. cena, Doplatek).  
* **US-3.2:** Jako lékař chci rychle najít sekci "Kontraindikace" z oficiálního SPC dokumentu (SÚKL).

### **Epic 4: Multi-Agent Intelligence**

*Cíl: Inteligentní směrování.*

* **US-4.1:** Systém musí automaticky rozpoznat intent a směrovat dotaz buď na lokální data (SÚKL/VZP) nebo na BioMCP (PubMed/Trials).  
* **US-4.2:** Systém musí zvládnout složené dotazy ("Jaká je cena léku X a co říkají studie o jeho vedlejších účincích?").

## **2\. Funkční Požadavky**

| ID | Název | Popis |
| :---- | :---- | :---- |
| **F-001** | **Streamovaná Odpověď** | Backend posílá data po tokenech (SSE), latence \< 1s na první token. |
| **F-002** | **BioMCP Integration** | Integrace docker image genomoncology/biomcp pro získávání dat z NCBI a ClinicalTrials.gov. |
| **F-003** | **Custom MCPs** | Vývoj vlastních serverů pro SÚKL (pgvector) a VZP (CSV). |
| **F-004** | **Query Expansion** | Využití BioMCP pro automatické rozšíření dotazu o synonyma léků (např. Brand name \-\> Generic name). |
| **F-005** | **Lokalizace** | Automatický překlad anglických výstupů z BioMCP do češtiny před zobrazením uživateli. |

## **3\. Akceptační Kritéria**

1. **Validita Dat:** České dotazy na léky MUSÍ být zodpovězeny primárně ze SÚKL, nikoliv z PubMedu.  
2. **Rychlost:** Odpověď obsahující data z BioMCP musí být vygenerována do 8 sekund. Lokální dotazy do 5 sekund.  
3. **Fallback:** Pokud BioMCP neodpovídá, systém musí upozornit uživatele a zkusit odpovědět z obecných znalostí LLM s varováním.