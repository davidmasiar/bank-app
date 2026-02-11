# 🏦 Bank Application Portfolio Management

Nástroj pro správu a strategickou analýzu bankovního aplikačního portfolia postavený na frameworku Django. Aplikace integruje LLM (Large Language Models) pro pokročilé vyhodnocování technologického dluhu, analýzu rizik a automatizovanou vizualizaci integrací.

## 🏗️ Architektura a rozhodnutí

* **Data Grounding:** AI asistent nepracuje s obecnými znalostmi, ale v každém promptu dostává aktuální kontext z databáze. Tím je eliminováno riziko halucinací.
* **Validace seedování:** Systém využívá režim "všechno nebo nic". Při importu dat přes seed_data probíhá  kontrola proti povoleným hodnotám (Kritičnost, Lifecycle, Citlivost). Jakýkoliv překlep okamžitě zastaví proces a díky transaction.atomic() vrátí databázi do původního stavu, čímž brání uložení nekonzistentních dat.
* **Self-Correction Loop (Mermaid.js):** Modul pro vizualizaci integrací obsahuje dvoufázovou kontrolu. Pokud první výstup LLM vykazuje syntaktické chyby, systém automaticky spustí jeden opravný cyklus pro zajištění správného vykreslení diagramu.
* **Design:** Styling využívá **Tailwind CSS** v barvách Raiffeisen Bank pro dosažení profesionálního enterprise vzhledu.

## 🚀 Hlavní funkcionality
* **Filtrování a vyhledávání:** Implementováno real-time vyhledávání aplikací podle názvu v kombinaci s kategorickými filtry pro doménu a kritičnost.

* **Kompletní CRUD integrací:** Plná správa integračních vazeb přímo z UI. Uživatel může vytvářet, editovat i mazat vazby mezi aplikacemi, přičemž systém automaticky hlídá integritu těchto vztahů.

* **AI Analytik:** Interaktivní rozhraní pro dotazy nad celým portfoliem. Analytik dokáže na základě dat identifikovat duplicity, navrhovat prioritizaci modernizace nebo analyzovat dopady výpadků.

## 🔐 Konfigurace API klíčů (ENV)
Aplikace vyžaduje přístup k OpenAI API. Pro zabezpečení citlivých údajů jsou klíče uloženy v souboru `.env`.

1. V kořenovém adresáři vytvořte soubor `.env`.
2. Přidejte své klíče ve tvaru

```bash
OPENAI_API_KEY="klíč"
```
Volitelně můžete v portfolio/utils.py specifikovat LLM model, nyní nastavený model=gpt-4o-mini

# 🛠️ Setup a instalace
Postupujte podle těchto kroků pro zprovoznění aplikace na lokálním stroji:
1. Klonování a virtuální prostředí
```bash
git clone https://github.com/davidmasiar/bank-app.git
```
```bash
cd bank-app
```
Vytvoření a aktivace prostředí
```bash
python -m venv venv
```
Windows
```bash
venv\Scripts\activate
```
macOS/Linux
```bash
source venv/bin/activate
```

2. Instalace závislostí

```bash
pip install -r requirements.txt
```
3. Migrace databáze
Inicializujte schéma SQLite databáze:

```bash
python manage.py makemigrations
```
```bash
python manage.py migrate
```
4. Seedování dat - Aplikace obsahuje skript pro naplnění databáze mockup daty (40 aplikací).

```bash
python manage.py seed_data
```
Tento příkaz načte data ze souboru data.json, provede validaci konzistence hodnot a vytvoří relační vazby mezi aplikacemi a integracemi.

5. Spuštění serveru
```bash
python manage.py runserver
```
Portál bude dostupný na adrese http://127.0.0.1:8000/


# 📊 Demo instrukce pro testování

1. Aplikace: Vyhledávání a Vizualizace

V menu zvolte Aplikace. Tato sekce slouží jako centrální registr všech systémů.

Hledání a Filtry: Vyzkoušejte vyhledávání podle názvu aplikace nebo využijte filtry v horní části (Doména, Kritičnost).

Generování Mermaid diagramu: Proklikněte se do detailu libovolné aplikace (např. Retail-Core-CZ). Klikněte na tlačítko „Generovat diagram“. Systém využije LLM k analýze integračních vazeb a pomocí Mermaid.js vykreslí interaktivní mapu okolí dané aplikace (15).

2. Integrace: Správa vazeb (CRUD)
Přejděte do sekce Integrace. Zde můžete spravovat toky dat mezi systémy.

Testování CRUD: Vyzkoušejte vytvoření nové vazby přes tlačítko „Přidat vazbu“. Následně u existujících záznamů otestujte tlačítka Upravit (změna parametrů) a Smazat. Jakákoliv změna se okamžitě projeví v AI analýzách a diagramech.

3. Strategická Analýza portfolia

Modul Analýza slouží k získání celkového přehledu o zdraví bankovního prostředí.

Spuštění: Kliknutím na tlačítko spustíte komplexní audit. LLM projde celé portfolio a identifikuje kritické body, jako je technologický dluh u core systémů, rizika u legacy aplikací a návrhy na konsolidaci vendorů. S volitelným exportem do pdf, případně tiskem.

4. AI Dotaz: Interaktivní Q&A
Rychlé volby: Použijte předvybrané dotazy (tzv. suggest-pills) pod nadpisem, které okamžitě analyzují např. GDPR kanály nebo kandidáty na vyřazení.

Vlastní dotaz: Do textového pole napište vlastní dotaz (např. "Které aplikace v cloudu mají nejvyšší tech dluh?"). Systém na základě aktuálních dat z databáze vygeneruje odpověď.

# Poznámky k budoucímu rozvoji (Future Work):

Ukládání historie chatu: Aktuálně se historie Q&A ukládá pouze do session. V produkční verzi by bylo lepší ukládat konverzace do databáze pro pozdější analýzu nejčastějších dotazů uživatelů.

Deployment a Docker: Příprava kontejnerizace projektu pro snadné nasazení do cloudového prostředí nebo on-prem infrastruktury banky.

Automatizované testy: Unit a integrační testy, zejména pro validaci LLM promptů a správnost importu dat, aby byla zajištěna stabilita při každé změně kódu.

Pokročilé vyhledávání: Implementace full-textového vyhledávání napříč celým portfoliem (nejen názvy), aby uživatelé mohli rychleji najít aplikace podle klíčových slov.