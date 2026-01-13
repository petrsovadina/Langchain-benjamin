

User Story

#  **User Personas**

## **4.1 Persona 1: Dr. Jana Nováková — Praktická Lékařka**

| Atribut | Hodnota |
| :---- | :---- |
| **Demografické údaje** | 45 let, 18 let praxe, ordinace v malém městě, 25-30 pacientů denně |
| **Tech skills** | Středně pokročilá, používá EHR (ICZ IKIS), smartphone, tablet v ordinaci |
| **Pain points** | Nemá čas studovat nové guidelines, anglická literatura je náročná, neví co hradí VZP |
| **Citát** | "Kdybych měla asistenta, který mi řekne správný postup a jaké léky jsou hrazené, šetřilo by mi to hodiny každý týden." |

## **4.2 Persona 2: MUDr. Petr Svoboda — Kardiolog v Ambulanci**

| Atribut | Hodnota |
| :---- | :---- |
| **Demografické údaje** | 38 let, 12 let praxe, městská nemocnice, 15-20 pacientů denně |
| **Tech skills** | Pokročilý, aktivní na lékařských fórech, používá PubMed pravidelně, early adopter |
| **Pain points** | Studie v PubMed jsou příliš obsáhlé, české guidelines někdy zaostávají za ESC |
| **Citát** | "Potřebuji nástroj, který mi udělá rešerši z relevantních zdrojů a shrne klíčové body — jako kdyby můj kolega přečetl 50 článků." |

## **4.3 Persona 3: Dr. Martin Kučera — Lékař na Urgentním Příjmu**

| Atribut | Hodnota |
| :---- | :---- |
| **Demografické údaje** | 32 let, 5 let praxe, fakultní nemocnice, 12-24h směny |
| **Tech skills** | Velmi pokročilý, používá mobilní aplikace, zvyklý na rychlá digitální řešení |
| **Pain points** | Nemá čas hledat informace během resuscitace, potřebuje okamžité odpovědi |
| **Citát** | "Když přijde pacient s neobvyklou kombinací symptomů ve 3 ráno, potřebuji asistenta, který mi během sekund poradí." |

# **5\. Functional Requirements**

## **5.1 Core Features (MVP)**

### **F-001: QuickConsult — Rychlé Klinické Dotazy**

| Popis | Primární rozhraní pro zadávání klinických dotazů v přirozeném jazyce. Systém poskytuje stručné odpovědi (3-5 vět) s inline citacemi. |
| :---- | :---- |
| **Priorita** | P0 (Must Have) |
| **Akceptační kritéria** | • Odpověď obsahuje minimálně 2 relevantní citace s PMID/DOI/SÚKL• Latence odpovědi \< 5 sekund pro 95% dotazů• Odpověď je v češtině s korektní lékařskou terminologií• Confidence score \> 0.7 pro validní odpovědi |

### **F-002: Multi-Agent RAG Pipeline**

| Popis | LangGraph multi-agent systém s centrálním orchestrátorem (Supervisor) a 4 specializovanými agenty: Drug Agent (SÚKL), PubMed Agent, Guidelines Agent, Pricing Agent (VZP). |
| :---- | :---- |
| **Priorita** | P0 (Must Have) |
| **Akceptační kritéria** | • Query Classifier správně identifikuje 8 typů intentů• Supervisor routing funguje pro single i compound queries• Každý agent vrací strukturované výsledky s citacemi• Fallback mechanismus při nedostupnosti zdrojů |

### **F-003: Citation System**

| Popis | Automatické generování inline citací \[1\]\[2\]\[3\] s referencemi na konci odpovědi. Unified Citation schema pro všechny zdroje. |
| :---- | :---- |
| **Priorita** | P0 (Must Have) |
| **Podporované formáty** | • PMID: PubMed články (odkaz na pubmed.ncbi.nlm.nih.gov)• SÚKL: Léčiva (odkaz na prehledy.sukl.cz)• DOI: Vědecké publikace• ČLS JEP: České guidelines |

### **F-004: Czech Localization**

| Popis | Plná podpora českého jazyka včetně 80+ lékařských zkratek a terminologie. Automatické překlady anglických zdrojů s uvedením originálu. |
| :---- | :---- |
| **Priorita** | P0 (Must Have) |
| **Akceptační kritéria** | • UI kompletně v češtině• Lékařská terminologie odpovídá českým standardům• Zkratky jsou vysvětleny při prvním použití• Správné kódování Windows-1250 pro SÚKL data |

### **F-005: VZP Integration**

| Popis | Zobrazení informací o úhradě léků a výkonů zdravotními pojišťovnami. Včetně maximální ceny, úhrady, doplatku a preskripčních omezení. |
| :---- | :---- |
| **Priorita** | P1 (Should Have) |
| **Akceptační kritéria** | • Zobrazení úhradových podmínek pro 90%+ běžných léků• Data z LEK-13 aktualizována měsíčně• Návrh levnějších alternativ se stejnou účinnou látkou |

## **5.2 Future Features (Post-MVP)**

| ID | Feature | Popis | Priorita |
| :---- | :---- | :---- | :---- |
| F-006 | DeepConsult | Hloubková analýza s porovnáním CZ vs mezinárodních guidelines | P2 (v2.0) |
| F-007 | Drug Interaction Checker | Kontrola lékových interakcí z SÚKL a mezinárodních zdrojů | P2 (v2.0) |
| F-008 | EHR Browser Extension | Integrace do STAPRO, ICZ, Galen EHR systémů | P2 (v2.0) |
| F-009 | Voice Interface | Hlasové dotazy pro hands-free použití | P3 (v3.0) |

# **6\. User Stories**

## **6.1 Epic 1: Klinické Dotazy**

| ID | User Story | Priorita |
| :---- | :---- | :---- |
| US-001 | Jako praktický lékař, chci zadat klinický dotaz v češtině, abych rychle získal odpověď s citacemi bez nutnosti prohledávat více zdrojů. | P0 |
| US-002 | Jako specialista, chci kliknout na citaci a zobrazit původní zdroj, abych mohl ověřit informace a přečíst si více detailů. | P0 |
| US-003 | Jako lékař, chci dostávat odpovědi s korektní českou lékařskou terminologií, abych mohl informace přímo použít v komunikaci s pacienty. | P0 |

## **6.2 Epic 2: Informace o Lécích**

| ID | User Story | Priorita |
| :---- | :---- | :---- |
| US-004 | Jako praktický lékař, chci zjistit informace o konkrétním léku (indikace, kontraindikace, dávkování), abych mohl bezpečně předepsat léčbu. | P1 |
| US-005 | Jako lékař, chci vidět, zda je lék hrazen VZP a kolik pacient doplatí, abych mohl předepsat dostupnou léčbu. | P1 |
| US-006 | Jako lékař, chci najít levnější alternativu se stejnou účinnou látkou, abych pacientovi ušetřil peníze. | P1 |

## 

## 

## 

##  **Epic 3: Guidelines**

| ID | User Story | Priorita |
| :---- | :---- | :---- |
| US-007 | Jako kardiolog, chci najít aktuální české guidelines pro specifickou diagnózu, abych postupoval podle národních standardů. | P0 |
| US-008 | Jako specialista, chci porovnat české a mezinárodní (ESC) guidelines, abych pochopil případné rozdíly. | P2 |

# **9\. Data Sources**

| Zdroj | Typ Dat | Integrace | Aktualizace |
| :---- | :---- | :---- | :---- |
| **SÚKL OpenData** | \~100K léčivých přípravků, SPC, PIL | CSV → pgvector | Měsíčně |
| **PubMed/MEDLINE** | 36M+ vědeckých článků | E-utilities API | Real-time |
| **LEK-13 (VZP)** | Ceny, úhrady, doplatky | CSV import | Měsíčně |
| **ČLS JEP Guidelines** | České doporučené postupy | PDF → pgvector | Kvartálně |
| **ESC/ERS Guidelines** | Evropské guidelines | PDF → pgvector | Při vydání |
| **Cochrane Library** | Systematic reviews, meta-analýzy | API | Real-time |

