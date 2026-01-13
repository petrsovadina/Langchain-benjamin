# Czech MedAI - Projektová Dokumentace

> Kompletní dokumentace pro projekt Benjamin - AI asistent pro české lékaře

## 📁 Struktura Dokumentace

Dokumentace je organizována do 4 hlavních kategorií pro snadnou orientaci:

### 01-strategicke-dokumenty/
Strategická vize a produktový brief projektu
- `01-bila-kniha.md` - Bílá kniha Czech MedAI: Revoluce v klinickém rozhodování
- `02-prd-produktovy-brief.md` - Product Requirements Document (PRD)

### 02-pozadavky-a-uzivatelske-scenare/
Funkční požadavky a uživatelské příběhy
- `01-user-stories.md` - User Stories a persony uživatelů
- `02-funkcni-pozadavky.md` - Funkční požadavky odvozené od user stories

### 03-architektura-a-technicka-dokumentace/
Technické detaily a architektonické řešení
- `01-architektura-hlubkova-analyza.md` - Hloubková analýza multi-agentní architektury
- `02-technicka-dokumentace.md` - Komplexní technická dokumentace

### 04-specifikace-komponent/
Detailní specifikace jednotlivých komponent systému
- `01-mvp-specifikace.md` - MVP specifikace (Minimum Viable Product)
- `02-biomcp-integrace.md` - Specifikace integrace BioMCP komponenty
- `03-frontend-ux-design.md` - Frontend UX/UI design specifikace

## 🚀 Rychlý Start

**Pro nové členy týmu** - doporučené pořadí čtení:
1. Začněte s `01-strategicke-dokumenty/01-bila-kniha.md` pro pochopení vize
2. Pokračujte s `01-strategicke-dokumenty/02-prd-produktovy-brief.md` pro produktový kontext
3. Přečtěte si `04-specifikace-komponent/01-mvp-specifikace.md` pro scope MVP
4. Pro technické detaily navštivte `03-architektura-a-technicka-dokumentace/`

**Pro vývojáře:**
- Backend: `03-architektura-a-technicka-dokumentace/01-architektura-hlubkova-analyza.md`
- Frontend: `04-specifikace-komponent/03-frontend-ux-design.md`
- Integrace: `04-specifikace-komponent/02-biomcp-integrace.md`

## 📊 Přehled Projektu

**Název:** Czech MedAI (Projekt Benjamin)
**Verze:** MVP 1.0
**Datum:** Leden 2026
**Technologie:** LangGraph, FastAPI, Next.js, Supabase

**Klíčové komponenty:**
- Multi-agentní architektura (LangGraph)
- Specializovaní agenti (Drug, PubMed, Guidelines, Pricing)
- MCP serverová infrastruktura
- Citation-by-design systém

## 🎯 Cílová Skupina

- Praktičtí lékaři
- Specialisté (kardiologové, internisté, etc.)
- Lékaři na urgentních příjmech

## 📝 Aktualizace Dokumentace

Poslední reorganizace: 13. ledna 2026
- Vytvořena logická adresářová struktura
- Normalizováno pojmenování souborů
- Přidán README pro navigaci
