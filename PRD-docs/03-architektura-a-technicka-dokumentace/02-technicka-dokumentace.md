### Technická Dokumentace: Czech MedAI (Projekt Benjamin)

#### 1.0 Úvod a Architektonická Vize

Tento dokument slouží jako centrální technická dokumentace pro vývojáře systému Czech MedAI, multi-agentního systému pro podporu klinického rozhodování postaveného na platformě LangGraph. Architektura platformy představuje strategický odklon od konvenčních monolitických RAG (Retrieval-Augmented Generation) systémů. Tato architektura záměrně dekomponuje monolitické paradigma RAG na kooperativní soubor specializovaných, doménově expertních agentů, které jsou orchestrovány centrálním supervisorem. Tento přístup zajišťuje systému nezbytnou škálovatelnost, přesnost a schopnost řešit komplexní klinické dotazy, na kterých jednodušší řešení selhávají.Naše platforma je postavena na pěti klíčových designových principech, které společně tvoří robustní základ pro spolehlivost a důvěryhodnost celého řešení:

1. **Supervisor-First Architecture:**  Každý uživatelský dotaz je nejprve analyzován centrálním agentem (Supervisor). Jeho úkolem je identifikovat záměr uživatele a rozhodnout, kteří specializovaní agenti jsou pro vyřešení úkolu nejvhodnější. Tento princip zajišťuje efektivní a přesné směrování úkolů k expertům s relevantní doménovou znalostí.  
2. **Specializovaní agenti:**  Každý agent má úzce vymezenou doménu a přístup ke specifickým nástrojům a datovým zdrojům (např. léky, doporučené postupy, ceny). Tato specializace zajišťuje vysokou přesnost a relevanci v dané oblasti a umožňuje paralelní zpracování, což výrazně zvyšuje rychlost a efektivitu systému, zejména u vícesložkových dotazů.  
3. **MCP-Native Integration:**  Všechny datové zdroje jsou do systému integrovány prostřednictvím standardizovaného protokolu MCP (Model Context Protocol). Tento přístup odděluje logiku agentů od implementace přístupu k datům, což dramaticky snižuje čas a náklady na integraci nových datových zdrojů a zajišťuje platformě dlouhodobou flexibilitu a schopnost rychlé expanze na nové datové zdroje a trhy.  
4. **Citation-by-Design:**  Transparentnost a důvěryhodnost nejsou doplňkové funkce, ale základní kámen celé architektury. Každý fragment informace je od počátku neoddělitelně spojen se svým primárním zdrojem. Tento princip je naší primární technickou mitigací rizika "halucinací" a zajišťuje, že každé tvrzení generované systémem je auditovatelné až k primárnímu zdroji dat.  
5. **Graceful Degradation:**  Architektura je navržena s ohledem na vysokou odolnost vůči výpadkům. Pokud je některý z datových zdrojů (např. databáze VZP) dočasně nedostupný, systém o tom transparentně informuje uživatele a poskytne zbývající části odpovědi bez selhání celého procesu.Tato promyšlená architektonická vize je realizována prostřednictvím součinnosti několika klíčových komponent, které si podrobněji popíšeme v následující kapitole.

#### 2.0 Architektura Systému na Vysoké Úrovni

Jednotlivé komponenty systému Czech MedAI spolupracují v jednom uceleném, kontrolovaném a auditovatelném workflow, které zajišťuje efektivní zpracování klinických dotazů. Tato sekce poskytuje přehled cesty uživatelského dotazu od jeho zadání, přes analýzu a sběr dat, až po doručení finální, syntetizované a ocitované odpovědi.Zpracování dotazu probíhá v následujících sekvenčních a paralelních krocích:

1. **Příjem a klasifikace dotazu:**  Uživatelský dotaz nejprve přijme Orchestrátor (Supervisor). Ten pomocí klasifikačního modelu analyzuje text a identifikuje jeden nebo více uživatelských záměrů (intents), například drug\_info, guideline\_lookup nebo složený dotaz compound\_query.  
2. **Delegace na specializované agenty:**  Na základě klasifikovaného záměru Supervisor inteligentně aktivuje a pověří příslušné specializované agenty, aby začali pracovat na svých dílčích úkolech. V případě složeného dotazu mohou být agenti aktivováni souběžně (paralelně).  
3. **Získávání dat (Retrieval):**  Každý aktivovaný agent komunikuje se svými dedikovanými datovými zdroji prostřednictvím standardizovaných MCP serverů. Například Drug Agent se dotazuje SÚKL databáze, zatímco Guidelines Agent prohledává vektorovou databázi s doporučenými postupy.  
4. **Syntéza odpovědi:**  Strukturované a ocitované výstupy od jednotlivých agentů jsou předány modulu Response Synthesizer. Ten je integruje do jediné, koherentní a srozumitelné odpovědi pro koncového uživatele, přičemž zachovává všechny reference na původní zdroje.Následující kapitola se bude věnovat hlubšímu technickému popisu každé z těchto klíčových komponent.

#### 3.0 Detailní Popis Komponent

Tato kapitola poskytuje hloubkový technický pohled na jednotlivé stavební bloky systému Czech MedAI. Pochopení funkcí a odpovědností každé komponenty je klíčové pro vývoj, údržbu a budoucí rozšiřování platformy.

##### 3.1 Orchestrátor (Supervisor)

Orchestrátor, označovaný také jako Supervisor, je centrálním mozkem celého systému. Jeho primární odpovědností je inteligentní směrování (routing) a koordinace práce specializovaných agentů. Po přijetí dotazu jej nejprve klasifikuje, aby určil záměr uživatele, a následně deleguje úkoly nejvhodnějším agentům. Tento mechanismus zajišťuje, že každý dotaz je zpracován efektivně a s maximální relevancí.Následující tabulka mapuje typy uživatelských záměrů na příklady dotazů a primárního agenta zodpovědného za jejich zpracování:| Intent | Příklad dotazu | Primární Agent || \------ | \------ | \------ || drug\_info | "Jaké jsou kontraindikace metforminu?" | Drug Agent || drug\_interaction | "Mohu kombinovat warfarin s ibuprofem?" | Drug Agent || guideline\_lookup | "Guidelines pro léčbu hypertenze u diabetiků" | Guidelines Agent || clinical\_question | "Diferenciální diagnostika bolesti na hrudi" | PubMed Agent || pricing\_coverage | "Kolik stojí Xarelto a hradí ho VZP?" | Pricing Agent || urgent\_diagnostic | "Pacient s ST elevací a bolestí na hrudi" | PubMed Agent (fast path) || compound\_query | "Metformin u CKD \- guidelines a cena" | Multiple agents |

##### 3.2 Specializovaní Agenti

Koncept specializovaných agentů představuje jádro naší modulární architektury. Každý agent funguje jako digitální expert s úzce vymezenou doménou a přístupem k specifickým nástrojům a datovým zdrojům. Tato modularita umožňuje nejen paralelní zpracování složených dotazů, ale také výrazně zvyšuje přesnost a relevanci odpovědí, jelikož každý agent operuje pouze s daty, pro která byl navržen.Následující tabulka shrnuje čtyři hlavní agenty, jejich datové zdroje a nástroje:| Specializovaný agent | Datový zdroj | Příklad řešeného úkolu | Využívané nástroje || \------ | \------ | \------ | \------ || **Drug Agent** | SÚKL OpenData v Supabase pgvector (\~100K léků) | "Jaké jsou kontraindikace metforminu?" | search\_drugs, get\_drug\_details, get\_spc || **PubMed Agent** | NCBI E-utilities (PubMed, 36M+ článků) | "Diferenciální diagnostika bolesti na hrudi." | search\_pubmed, get\_abstract, get\_related || **Guidelines Agent** | Vector DB (ČLS JEP, ESC PDFs) | "Jaké jsou aktuální guidelines pro léčbu hypertenze?" | search\_guidelines, compare\_guidelines || **Pricing Agent** | VZP LEK-13 (CSV data) | "Kolik stojí Xarelto a hradí ho VZP?" | get\_pricing, find\_alternatives |

##### 3.3 MCP Servery (Model Context Protocol)

MCP server je standardizované rozhraní, které hraje strategickou roli v naší architektuře. Odděluje logiku specializovaných agentů od přímé implementace přístupu k datům. Místo toho, aby se každý agent staral o připojení k různým API či databázím, komunikuje s jednoduchým a jednotným MCP serverem. Tento přístup dramaticky zjednodušuje údržbu, testování a především budoucí rozšiřování systému o nové datové zdroje.V systému jsou implementovány následující klíčové MCP servery:

* sukl-mcp:8001  
* pubmed-mcp:8002  
* vzp-mcp:8003  
* guidelines-mcp:8004

##### 3.4 Response Synthesizer

Modul Response Synthesizer je finální komponentou v řetězci zpracování dotazu. Jeho úkolem je převzít strukturované, dílčí výstupy od jednotlivých agentů a sestavit z nich finální, koherentní a správně ocitovanou odpověď pro uživatele. Zajišťuje, že výsledek je srozumitelný, gramaticky správný a zachovává všechny reference na původní zdroje.Následující sekce demonstruje praktickou spolupráci všech těchto komponent na konkrétním příkladu.

#### 4.0 Příklad Workflow: Zpracování Složeného Dotazu

Tato sekce demonstruje sílu a flexibilitu multi-agentní architektury na konkrétním, praktickém příkladu. Krok za krokem rozebereme proces zpracování složeného dotazu (compound query), který vyžaduje informace z více domén:  **"Metformin u CKD \- guidelines a cena"** .Proces zpracování je rozdělen do následujících kroků:

1. **Krok 1: Klasifikace dotazu:**  Dotaz nejprve přijme  **Orchestrátor (Supervisor)** . Ten pomocí klasifikačního modelu analyzuje text a identifikuje dva odlišné záměry: guideline\_lookup (vyhledání doporučených postupů pro metformin u chronického onemocnění ledvin) a pricing\_coverage (zjištění ceny a úhrady metforminu).  
2. **Krok 2: Paralelní směrování:**  Na základě identifikovaných záměrů Supervisor inteligentně aktivuje a pověří dva specializované agenty, aby pracovali souběžně:  **Guidelines Agent**  a  **Pricing Agent** . Tímto paralelním zpracováním se výrazně zkracuje celková doba odpovědi.  *Tento krok je přímou realizací principu*  ***Specializovaných agentů***  *, který umožňuje efektivní paralelizaci práce.*  
3. **Krok 3: Specializované vyhledávání:**  Každý agent se připojí ke svému dedikovanému datovému zdroji.  **Guidelines Agent**  prohledá vektorovou databázi obsahující doporučené postupy ČLS JEP a ESC. Současně  **Pricing Agent**  zasílá dotaz na data z číselníku LEK-13 od VZP, aby získal informace o ceně a úhradě.  *Komunikace probíhá přes standardizované rozhraní, což demonstruje výhodu*  ***MCP-Native Integration***  *.*  
4. **Krok 4: Syntéza odpovědi:**  Strukturované výsledky od obou agentů (úryvky z guidelines a data o ceně) jsou předány finálnímu modulu,  **Response Synthesizer** . Ten je integruje do jediné, koherentní a srozumitelné odpovědi pro lékaře, která obsahuje jak klinická doporučení, tak praktické informace o úhradě, a to vše řádně ocitované.  *Finální odpověď je plně ocitovaná díky principu*  ***Citation-by-Design***  *, který je integrován v celém procesu.*Tato efektivní orchestrace je umožněna pečlivě zvoleným technologickým stackem, který poskytuje potřebný výkon a flexibilitu.

#### 5.0 Technologický Stack a Infrastruktura

Robustnost, škálovatelnost a výkon platformy Czech MedAI jsou zajištěny pečlivým výběrem moderních a v praxi ověřených technologií. Následující tabulka poskytuje kompletní přehled použitého technologického stacku, organizovaného podle jednotlivých vrstev systému.| Vrstva | Technologie || \------ | \------ || **Frontend** | Next.js 14, TypeScript, Tailwind CSS, Radix UI || **Backend** | FastAPI (Python 3.11+), LangGraph 0.2+, LangChain 0.3+ || **Databáze** | Supabase (PostgreSQL \+ pgvector), Redis (cache) || **LLM** | Claude Sonnet 4.5 (primary), GPT-4 (fallback) || **Infrastruktura** | Vercel (frontend), Railway (backend), EU datacenter || **Monitoring** | Langfuse (LLM observability), Sentry (errors) |  
Tento technologický stack je navržen pro efektivní zpracování dat z unikátního ekosystému národních a mezinárodních zdrojů, které jsou základem relevance celého systému.

#### 6.0 Datový Ekosystém

Strategický význam platformy Czech MedAI spočívá v hyper-lokalizaci a hluboké integraci různorodých datových zdrojů. Právě unikátní schopnost syntetizovat data z českých regulatorních databází, národních doporučených postupů a nejnovějších mezinárodních vědeckých publikací je klíčovou konkurenční výhodou a zárukou relevance pro českého lékaře.

##### 6.1 Národní Datové Zdroje (ČR)

Tyto zdroje zajišťují, že platforma rozumí lokálním specifikům, od standardů péče až po úhradové politiky.| Zdroj | Typ dat | Role v systému | Aktualizace || \------ | \------ | \------ | \------ || **SÚKL OpenData** | \~100K léčivých přípravků, SPC, PIL | Základní zdroj pro  **Drug Agent** ; poskytuje informace o lécích registrovaných v ČR. | Měsíčně || **LEK-13 (VZP)** | Ceny, úhrady, doplatky | Primární zdroj pro  **Pricing Agent** ; umožňuje odpovědět na praktické dotazy o nákladech. | Měsíčně || **ČLS JEP Guidelines** | Národní doporučené postupy | Klíčový zdroj pro  **Guidelines Agent** ; zajišťuje soulad s národními standardy péče. | Kvartálně |

##### 6.2 Mezinárodní Datové Zdroje

Mezinárodní zdroje doplňují lokální data o nejnovější vědecké poznatky a zajišťují, že odpovědi jsou v souladu s principy medicíny založené na důkazech.| Zdroj | Typ dat | Role v systému | Aktualizace || \------ | \------ | \------ | \------ || **PubMed/MEDLINE** | 36M+ vědeckých článků | Hlavní zdroj pro  **PubMed Agent** ; umožňuje rešerše a dokládání tvrzení důkazy. | Real-time || **Cochrane Library** | Systematické review a meta-analýzy | Doplňkový zdroj pro zajištění nejvyšší kvality důkazů (systematické review, meta-analýzy) a validaci informací z primárních studií. | Real-time || **Evropské odborné společnosti (ESC, ERS)** | Mezinárodní doporučené postupy | Zdroj pro  **Guidelines Agent**  pro porovnání českých a mezinárodních standardů. | Při vydání |  
