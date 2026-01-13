  
**Czech MedAI**

MVP Specifikace

*Klinický AI Asistent pro České Lékaře*

Verze 1.0

Leden 2026

Projekt: Benjamin

# **Obsah**

# **1\. Executive Summary**

Czech MedAI MVP je minimální životaschopný produkt zaměřený na validaci základní hypotézy: čeští lékaři potřebují a chtějí používat lokalizovaného AI asistenta pro rychlý přístup ke klinickým informacím.

# **2\. Rozsah MVp**

## **2.1 In Scope (Součástí MVP)**

| ID | Funkce | Popis |
| :---- | :---- | :---- |
| **F-001** | QuickConsult | Klinické dotazy v přirozeném jazyce, odpověď 3-5 vět, \< 5s |
| **F-002** | Multi-Agent RAG | LangGraph orchestrace 4 specializovaných agentů |
| **F-003** | Citation System | Inline citace \[1\]\[2\] s PMID/SÚKL/DOI odkazy |
| **F-004** | Czech Localization | Česká terminologie, 80+ zkratek, české UI |
| **F-005** | VZP Integration | Ceny, úhrady, doplatky z LEK-13 |

## **2.2 Out of Scope (Mimo MVP)**

* Diagnostický nástroj — systém neposkytuje diagnózy pacientů  
* EHR integrace — browser extension je post-MVP feature  
* Drug Interaction Checker — komplexní kontrola interakcí  
* Voice Interface — hlasové ovládání  
* Multi-language — pouze čeština v MVP  
* Offline režim — vyžaduje internetové připojení  
* B2C aplikace — pouze pro healthcare professionals

# **3\. Technická Architektura**

## **3.1 High-Level Architecture**

MVP využívá multi-agent architekturu postavenou na LangGraph s centrálním orchestrátorem (Supervisor) a 4 specializovanými agenty. Každý agent má přístup k dedikovanému MCP serveru.

### **Architektonické principy**

1. Supervisor-First — centrální agent klasifikuje a deleguje dotazy  
2. Specializovaní agenti — každý agent má úzce vymezenou doménu  
3. MCP-Native — standardizované rozhraní pro datové zdroje  
4. Citation-by-Design — citace jsou součástí každého kroku  
5. Graceful Degradation — odolnost vůči výpadkům zdrojů

## **3.2 Technology Stack**

| Vrstva | Technologie | Verze |
| :---- | :---- | :---- |
| **Frontend** | Next.js, TypeScript, Tailwind CSS, Radix UI | Next.js 14.x |
| **Backend** | FastAPI, LangGraph, LangChain | Python 3.11+, LangGraph 1.0.x |
| **Database** | Supabase (PostgreSQL \+ pgvector) | PostgreSQL 15, pgvector 0.7 |
| **Cache** | Redis | Redis 7.x |
| **LLM** | Claude Sonnet 4.5 (primary) | claude-sonnet-4-5-20250929 |
| **Embeddings** | OpenAI text-embedding-ada-002 | 1536 dimensions |
| **MCP Framework** | FastMCP | FastMCP 2.0 |
| **Monitoring** | Langfuse | Cloud / Self-hosted |
| **Infrastructure** | Vercel (FE), Railway (BE) | EU datacenter |

# **4\. Specializovaní Agenti**

## **4.1 Přehled Agentů**

| Agent | MCP Server | Datový Zdroj | Nástroje |
| :---- | :---- | :---- | :---- |
| **Drug Agent** | sukl-mcp:8001 | SÚKL OpenData | search\_drugs, get\_details, get\_spc |
| **PubMed Agent** | pubmed-mcp:8002 | NCBI E-utilities | search\_pubmed, get\_abstract |
| **Pricing Agent** | vzp-mcp:8003 | VZP LEK-13 | get\_pricing, find\_alternatives |
| **Guidelines Agent** | guidelines-mcp:8004 | ČLS JEP (Vector DB) | search\_guidelines |

## **4.2 Drug Agent**

**Účel:** Poskytuje informace o léčivých přípravcích registrovaných v ČR.

**Datový zdroj:** SÚKL OpenData (\~100 000 přípravků)

**Aktualizace:** Měsíčně (27. den měsíce)

### **Nástroje**

| Nástroj | Popis | Parametry |
| :---- | :---- | :---- |
| search\_drugs | Semantic search v databázi léčiv | query, limit, threshold |
| get\_drug\_details | Detail léčiva podle SÚKL kódu | sukl\_code |
| get\_spc | Souhrn údajů o přípravku | sukl\_code |
| get\_alternatives | Alternativy se stejnou účinnou látkou | sukl\_code, limit |

## **4.3 PubMed Agent**

**Účel:** Vyhledávání vědeckých článků a evidence-based informací.

**Datový zdroj:** PubMed/MEDLINE (36M+ článků)

**API:** NCBI E-utilities (real-time)

### **Nástroje**

| Nástroj | Popis | Parametry |
| :---- | :---- | :---- |
| search\_pubmed | Vyhledávání článků | query, max\_results, date\_range |
| get\_abstract | Získání abstraktu podle PMID | pmid |
| get\_related | Související články | pmid, limit |

## **4.4 Pricing Agent**

**Účel:** Informace o cenách a úhradách léčiv.

**Datový zdroj:** VZP LEK-13 (měsíční číselník)

**Aktualizace:** Měsíčně (\~8. den měsíce)

### **Nástroje**

| Nástroj | Popis | Parametry |
| :---- | :---- | :---- |
| get\_pricing | Cena, úhrada, doplatek | sukl\_code |
| find\_alternatives | Levnější alternativy | sukl\_code, max\_copay |

## **4.5 Guidelines Agent**

**Účel:** Vyhledávání v doporučených postupech.

**Datový zdroj:** ČLS JEP guidelines (PDF → Vector DB)

**Aktualizace:** Kvartálně

### **Nástroje**

| Nástroj | Popis | Parametry |
| :---- | :---- | :---- |
| search\_guidelines | Semantic search v guidelines | query, specialty, limit |
| get\_guideline\_section | Konkrétní sekce guidelines | guideline\_id, section |

# **5\. Klasifikace Dotazů**

## **5.1 Intent Types**

Supervisor klasifikuje každý dotaz do jedné z 8 kategorií, které určují routing na příslušné agenty.

| Intent | Popis | Agent(i) |
| :---- | :---- | :---- |
| drug\_info | Informace o léčivu (indikace, KI, dávkování) | Drug Agent |
| drug\_interaction | Lékové interakce | Drug Agent |
| guideline\_lookup | Doporučené postupy | Guidelines Agent |
| clinical\_question | Obecný klinický dotaz | PubMed Agent |
| pricing\_coverage | Ceny a úhrady | Pricing Agent |
| urgent\_diagnostic | Urgentní diferenciální diagnostika | PubMed Agent (fast path) |
| compound\_query | Kombinovaný dotaz (více intentů) | Multiple agents (parallel) |
| out\_of\_scope | Mimo rozsah systému | Graceful decline |

## **5.2 Příklady Dotazů**

| Dotaz | Intent | Agent(i) |
| :---- | :---- | :---- |
| "Jaké jsou kontraindikace metforminu?" | drug\_info | Drug |
| "Guidelines pro léčbu hypertenze" | guideline\_lookup | Guidelines |
| "Kolik stojí Xarelto a hradí ho VZP?" | pricing\_coverage | Pricing |
| "Diferenciální diagnostika bolesti na hrudi" | clinical\_question | PubMed |
| "Metformin u CKD \- guidelines a cena" | compound\_query | Guidelines \+ Pricing |

# **6\. Datové Zdroje**

## **6.1 SÚKL OpenData**

| Parametr | Hodnota |
| :---- | :---- |
| URL | https://opendata.sukl.cz |
| Formát | CSV (Windows-1250 encoding) |
| Velikost | \~100 000 léčivých přípravků |
| Aktualizace | Měsíčně (27. den) |
| Klíčové soubory | dlp\_lecivepripravky.csv, dlp\_slozeni.csv, dlp\_atc.csv |

## **6.2 VZP LEK-13**

| Parametr | Hodnota |
| :---- | :---- |
| URL | https://opendata.sukl.cz/soubory/LEK13/ |
| Obsah | Ceny, úhrady, doplatky, výdeje |
| Aktualizace | Měsíčně (\~8. den) |

## **6.3 PubMed E-utilities**

| Parametr | Hodnota |
| :---- | :---- |
| Base URL | https://eutils.ncbi.nlm.nih.gov/entrez/eutils/ |
| Endpoints | esearch.fcgi, efetch.fcgi, elink.fcgi |
| Rate Limit | 3 req/s (bez API key), 10 req/s (s API key) |
| Databáze | 36M+ článků |

## **6.4 ČLS JEP Guidelines**

| Parametr | Hodnota |
| :---- | :---- |
| Zdroj | https://www.cls.cz \+ odborné společnosti |
| Formát | PDF → chunking → embeddings → pgvector |
| Aktualizace | Kvartálně (manuální review) |

# **7\. Databázové Schéma**

## **7.1 Tabulka: drugs**

Hlavní tabulka léčivých přípravků s vektorovým embeddingem pro semantic search.

| Sloupec | Typ | Nullable | Popis |
| :---- | :---- | :---- | :---- |
| id | UUID | NOT NULL | Primary key |
| sukl\_code | VARCHAR(7) | NOT NULL | SÚKL kód (unique) |
| name | VARCHAR(70) | NOT NULL | Název přípravku |
| strength | VARCHAR(24) | NULL | Síla |
| form | VARCHAR(27) | NULL | Léková forma |
| atc\_code | VARCHAR(7) | NULL | ATC kód WHO |
| active\_substances | TEXT | NULL | Léčivé látky |
| is\_available | BOOLEAN | DEFAULT false | Dostupnost na trhu |
| search\_text | TEXT | NULL | Kombinovaný text pro embedding |
| embedding | vector(1536) | NULL | OpenAI ada-002 embedding |

## **7.2 Tabulka: drug\_pricing**

| Sloupec | Typ | Nullable | Popis |
| :---- | :---- | :---- | :---- |
| id | UUID | NOT NULL | Primary key |
| sukl\_code | VARCHAR(7) | NOT NULL | FK → drugs.sukl\_code |
| period | VARCHAR(6) | NULL | Období (YYYYMM) |
| avg\_price | DECIMAL(10,2) | NULL | Průměrná cena |
| reimbursement | DECIMAL(10,2) | NULL | Úhrada VZP |
| copay | DECIMAL(10,2) | NULL | Doplatek pacienta |

## **7.3 Indexy**

\-- HNSW index pro vektorové vyhledávání

CREATE INDEX drugs\_embedding\_idx ON drugs USING hnsw (embedding vector\_cosine\_ops);

\-- B-tree indexy pro běžné dotazy

CREATE INDEX drugs\_atc\_idx ON drugs(atc\_code);

CREATE INDEX drugs\_name\_idx ON drugs(name);

CREATE INDEX drugs\_sukl\_idx ON drugs(sukl\_code);

# **8\. API Kontrakty**

## **8.1 QuickConsult Endpoint**

POST /api/v1/consult

### **Request**

{

  "query": "Jaké jsou kontraindikace metforminu?",

  "session\_id": "uuid",

  "context": {

    "specialty": "general\_practice",

    "urgency": "normal"

  }

}

### **Response**

{

  "answer": "Metformin je kontraindikován u pacientů s...\[1\]\[2\]",

  "citations": \[

    {

      "id": 1,

      "source\_type": "sukl",

      "source\_id": "0012345",

      "title": "METFORMIN TEVA 500 MG \- SPC",

      "url": "https://www.sukl.cz/...",

      "snippet": "Kontraindikace: ..."

    }

  \],

  "confidence": 0.92,

  "intent": "drug\_info",

  "agents\_used": \["drug\_agent"\],

  "latency\_ms": 2340

}

## **8.2 Citation Schema**

| Pole | Typ | Popis |
| :---- | :---- | :---- |
| id | integer | Pořadové číslo citace v odpovědi |
| source\_type | enum | sukl | pubmed | guideline | vzp |
| source\_id | string | SÚKL kód / PMID / DOI / guideline ID |
| title | string | Název zdroje |
| url | string | URL na původní zdroj |
| snippet | string | Relevantní úryvek (max 200 znaků) |
| relevance\_score | float | Skóre relevance (0-1) |

# **9\. UI/UX Specifikace**

## **9.1 Hlavní Obrazovky**

6. Landing Page — představení produktu, login/signup  
7. Dashboard — hlavní rozhraní s chat input  
8. Conversation View — historie dotazů a odpovědí  
9. Citation Modal — detail zdroje po kliknutí na citaci  
10. Settings — uživatelské preference, API usage

## **9.2 Design Principy**

* Clean & Professional — minimalistický design vhodný pro zdravotnické prostředí  
* Mobile-First — responsive design pro tablet/mobile v ordinaci  
* Accessibility — WCAG 2.1 AA, keyboard navigation  
* Speed — skeleton loading, optimistic updates

## **9.3 Interakční Flow**

1\. Lékař zadá dotaz v přirozeném jazyce

2\. Systém zobrazí loading indicator (\< 5s)

3\. Odpověď se zobrazí s inline citacemi \[1\]\[2\]\[3\]

4\. Kliknutí na citaci otevře modal s detailem zdroje

5\. Možnost kopírovat odpověď nebo sdílet

# **10\. Implementační Roadmap**

## **10.1 Přehled Fází**

| Fáze | Týden | Hlavní Deliverables |
| :---- | :---- | :---- |
| **0** | 1-2 | Smoke Test: Single-page app, Claude API, 5 beta testerů |
| **1** | 3-6 | MVP Foundation: Supabase, SÚKL pipeline, Drug Agent |
| **2** | 7-10 | Core Features: PubMed Agent, Query Classifier, Citations |
| **3** | 11-12 | Production: Auth, Monitoring, Beta launch (50 lékařů) |

## **10.2 Fáze 0: Smoke Test (Týden 1-2)**

**Cíl:** Validace základní hypotézy s minimálním kódem

* Single-page Next.js aplikace  
* Direct Claude API call s PubMed kontextem  
* 5 beta testerů (lékaři)  
* Go/No-Go: 80%+ pozitivní feedback, \< 10s latence

## **10.3 Fáze 1: MVP Foundation (Týden 3-6)**

* Supabase projekt setup (PostgreSQL \+ pgvector)  
* SÚKL data pipeline (download → parse → embed → store)  
* sukl-mcp server (FastMCP 2.0)  
* Drug Agent s ReAct pattern  
* Basic FastAPI backend

## **10.4 Fáze 2: Core Features (Týden 7-10)**

* pubmed-mcp server \+ PubMed Agent  
* Query Classifier (8 intent types)  
* Supervisor \+ LangGraph orchestrace  
* Response Synthesizer \+ Citation System  
* VZP Pricing Agent \+ LEK-13 data  
* Guidelines Agent \+ ČLS JEP indexace

## **10.5 Fáze 3: Production Ready (Týden 11-12)**

* OAuth2 \+ Supabase Auth  
* Langfuse monitoring \+ tracing  
* Load testing (1000+ concurrent users)  
* Security audit  
* Beta launch (50 lékařů)

# **11\. Rizika a Mitigace**

| Riziko | Závažnost | Mitigace |
| :---- | :---- | :---- |
| LLM halucinace | Vysoká | Povinné citace, confidence \> 0.7, multi-source validation |
| Regulatorní (EU MDR) | Vysoká | Early SÚKL engagement, ISO certifikace, legal review |
| Data quality | Střední | Multi-source validation, regular audits, user feedback |
| User adoption | Střední | Beta testing, UX research, iterativní vývoj, freemium |
| API rate limits | Nízká | Redis caching, fallback providers, rate limiting |
| MCP availability | Střední | Health checks, graceful degradation, circuit breakers |

# **12\. Metriky Úspěchu**

## **12.1 Klíčové KPIs**

| Metrika | Baseline | Target (12W) | Měření |
| :---- | :---- | :---- | :---- |
| MAU (Monthly Active Users) | 0 | 100 | Analytics |
| DAU (Daily Active Users) | 0 | 50 | Analytics |
| NPS Score | N/A | \> 40 | Survey |
| Response Time (p95) | N/A | \< 5s | APM |
| Citation Accuracy | N/A | \> 90% | Manual audit |
| Retention M2M | N/A | \> 60% | Cohort analysis |
| Queries per User/Day | N/A | \> 3 | Analytics |

## **12.2 Kvalitativní Feedback**

* Týdenní user interviews (5 lékařů)  
* In-app feedback widget (thumbs up/down \+ komentář)  
* Monthly NPS survey  
* Bug/feature request tracking

*— Konec dokumentu —*

Czech MedAI | Projekt Benjamin | Leden 2026