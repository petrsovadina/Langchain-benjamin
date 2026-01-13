# **Frontend Specification: Czech MedAI (Design v2.3)**

Filosofie: "Clinical Canvas" (Klinické Plátno)  
Priorita: Absolutní čistota, redukce kognitivní zátěže, plynulá expanze.  
Verze: 2.3 (Final Design)

## **1\. Uživatelský Flow (The Expansion Pattern)**

Rozhraní se chová jako "Interface on Demand". Nezahltí lékaře tlačítky, dokud nejsou potřeba.

### **Stav A: "Zen Mode" (Výchozí stav)**

Lékař přichází k "čistému stolu".

* **Vizuál:** Prázdná, uklidňující plocha (velmi jemná off-white nebo subtilní gradient slate-50). Žádné trvalé postranní lišty, žádná těžká menu.  
* **Fokus:** Uprostřed obrazovky levituje pouze **Inteligentní Vstupní Pole (Omnibox)**.  
* **Interakce:** Kurzor je automaticky v poli. Lékař začne psát nebo diktovat.

### **Stav B: "Active Consultation" (Po odeslání)**

V momentě odeslání dotazu se rozhraní *nepřepíná* skokově, ale plynule **transformuje**:

1. **Levitace:** Omnibox se plynule odsune (zaglideuje) k dolnímu okraji obrazovky, kde zůstane kotvený pro další dotazy.  
2. **Expanze:** Prostor nad ním se zaplní "kartou" s odpovědí agenta.  
3. **Historie:** Předchozí konverzace se jemně vynoří v pozadí (pokud existuje), jinak zůstává skrytá.

## **2\. Klíčové UI Komponenty**

### **A. The Omnibox (Srdce systému)**

Toto není jen "input". Je to řídící centrum celé aplikace.

* **Design:** Minimalistický, jemný stín (elevation-low), zaoblené rohy (pill-shape).  
* **Chování:**  
  * **Auto-grow:** Při psaní se dynamicky zvětšuje.  
  * **Contextual Suggestions:** Návrhy (léky, diagnózy) se objevují v plovoucím okně *nad* polem jen když uživatel píše.  
  * **Minimalismus:** Obsahuje pouze nezbytné ikony v šedé barvě: Mikrofon (Diktování), Sponka (Upload).

### **B. Agent Thought Stream (Indikátor práce)**

Nahrazuje klasický spinner. Uživatel musí vidět, že systém pracuje s daty.

* *Umístění:* Přímo nad Omniboxem nebo v záhlaví odpovědi.  
* *Vizuál:* Malý, pulzující text v mono fontu.  
* *Sekvence stavů:*  
  1. 🧠 \[Supervisor\] Klasifikuji dotaz: Onkologie...  
  2. 🌍 \[BioMCP\] Prohledávám PubMed (Found: 12 articles)...  
  3. 🇨🇿 \[SÚKL Agent\] Ověřuji registraci v ČR...  
  4. 📝 \[Synthesizer\] Překládám a formátuji...

### **C. Contextual Overlay (Modální Detail)**

Klíčová komponenta pro "nevyskakování" z kontextu.

* **Spouštěč:** Kliknutí na citaci \[1\] nebo \[SÚKL\] v textu odpovědi.  
* **Chování:** Z pravé strany (Desktop) nebo zespodu (Mobile) vyjede **Overlay Panel**.  
* **Vlastnosti:**  
  * **Non-blocking:** Hlavní chat se jen mírně ztmaví. Lékař může panel kdykoliv zavřít klávesou Esc.  
  * **Obsah:** V panelu se načte PDF z SÚKL nebo abstrakt z PubMedu/BioMCP.  
  * **Split-View efekt:** Lékař vidí vlevo syntézu AI a vpravo originální dokument pro verifikaci.

## **3\. Typografie a Strukturální Design**

* **Font:** Inter nebo Geist Sans (maximální čitelnost).  
* **Hierarchie Odpovědi:**  
  * AI nevrací "blok textu", ale vizuálně strukturovanou kartu.  
  * **Sekce:** Jasně oddělené nadpisy (Indikace, Dávkování, Úhrada).  
  * **Highlights:** Klíčová varování (interakce) podbarvena bg-red-50 s červeným proužkem.  
  * **Safe Info:** Schválené úhrady podbarveny bg-green-50.

## **4\. Ovládání a Přístupnost**

* **Focus First:** Aplikace je plně ovladatelná klávesnicí (/ pro skok do Omniboxu).  
* **Escape Hatch:** Klávesa Esc vždy zavře aktuální modální okno (Overlay).  
* **Dark Mode:** Automatická adaptace dle systému (kritické pro noční služby).