# Plan: Fase 1-spesifikasjon — Det Organisatoriske Minnet

## Kontekst

Brukeren har godkjent et fryst arkitekturdokument for det nye prosjektet "Det Organisatoriske Minnet". Dette er et selvstendig prosjekt uten tilknytning til personalisert-monitor. Neste steg er å opprette et nytt, frittstående repo og skrive et detaljert planleggingsdokument for Fase 1 ("Bevis at delene snakker sammen").

Fase 1 er det teknisk mest risikofylte steget: å bevise at Office Add-in (Task Pane i TypeScript) kan kommunisere med en lokal FastAPI-backend via localhost. Ingen annen funksjonalitet implementeres i denne fasen.

---

## Hva som opprettes

### 1. Nytt lokalt repo

Et frittstående repo opprettes i `/home/user/org-minne/` med følgende struktur:

```
org-minne/
├── frontend/              # Office Add-in (Task Pane, TypeScript)
├── backend/
│   ├── core/              # FastAPI, /v1/analyse, orkestrering
│   ├── datasources/       # (tom i Fase 1)
│   ├── ai/                # (tom i Fase 1)
│   ├── retrieval/         # (tom i Fase 1)
│   └── memory/            # (tom i Fase 1)
├── infra/                 # PyInstaller-spec, build-scripts
├── docs/                  # Utviklerveiledning
├── specs/
│   └── fase-1-plan.md     # Detaljert sjekkliste (hoveddokumentet)
├── config.json            # Modul-valg per nivå (skjelett)
├── .gitignore
└── README.md
```

### 2. Hoveddokumentet: `specs/fase-1-plan.md`

Ett enkelt, frittstående Markdown-dokument med full kontekst, forklarende innledninger per gruppe og avkryssbare deloppgaver. Dokumentet skal kunne leses uten kjennskap til noe annet dokument.

---

## Innhold i specs/fase-1-plan.md

### Innledning

- Hva Fase 1 er og hvorfor den prioriteres først
- Hva som bevises når fasen er ferdig (handshake-testen)
- Hva som eksplisitt utsettes til Fase 2+ (anomali, RAG, database, pakking)
- Forutsetninger (Node.js, Python 3.11+, Excel Desktop med WebView2)

---

### Gruppe 1 — Monorepo-struktur

**Ingress:** Oppretter skjelettet alle faser bygger videre på. Alle mapper opprettes selv om de er tomme i denne fasen, slik at strukturen er stabil fra starten.

- [ ] Opprett rot-repo i ny mappe og initialiser git (`git init`)
- [ ] Opprett mappestruktur: `frontend/`, `backend/core/`, `backend/datasources/`, `backend/ai/`, `backend/retrieval/`, `backend/memory/`, `infra/`, `docs/`, `specs/`
- [ ] Opprett `.gitignore` som ekskluderer: `__pycache__`, `*.pyc`, `.env`, `node_modules/`, `dist/`, `build/`, PyInstaller-output
- [ ] Opprett `config.json` med skjelett: `{ "kilde": "excel_tabell", "ai": "openai", "retriever": "lokal_vektor" }`
- [ ] Opprett `README.md` med prosjektnavn, ett-linje-beskrivelse og lenke til `specs/fase-1-plan.md`
- [ ] Gjør første commit: `chore: initialiser monorepo-struktur`

---

### Gruppe 2 — Backend: minimal FastAPI

**Ingress:** En lettvekts Python-app som lytter på `localhost:8000`. Den gjør ingenting annet enn å svare på to endepunkter og avvise forespørsler uten gyldig token. Dette er nok til å bevise handshake-koblingen.

- [ ] Opprett `backend/core/requirements.txt` med avhengigheter: `fastapi`, `uvicorn[standard]`, `python-dotenv`, `pydantic`
- [ ] Opprett `backend/core/.env.mal` med variablene `PORT=8000`, `TOKEN=<bytt-ut>`, `VERSION=0.1.0`
- [ ] Opprett `backend/core/main.py` med:
  - [ ] FastAPI-instans med tittel og versjon fra `.env`
  - [ ] CORS-middleware som tillater forespørsler fra `https://localhost:3000` og Office-origins
  - [ ] Bearer token-middleware: avviser forespørsler uten gyldig `Authorization: Bearer <token>`-header med HTTP 401
  - [ ] Startup-logg som skriver versjon og port til konsollen når appen starter
- [ ] Implementer `GET /health` — returnerer `{ "status": "ok", "version": "...", "timestamp": "..." }` som JSON
- [ ] Implementer `POST /v1/analyse` — tar imot forespørsel (se kontrakt under), returnerer hardkodet mock-respons med strukturert kjøringslogg (liste av steg med tidsstempel og melding)
- [ ] Opprett `backend/core/modeller.py` med Pydantic-modeller for forespørsel og svar på `/v1/analyse`
- [ ] Verifiser manuelt: start backend med `uvicorn core.main:app --reload` og kall `GET /health` med curl — forvent HTTP 200

**API-kontrakt POST /v1/analyse (referanse):**
```json
Forespørsel: { "kilde": "excel_tabell", "referanse": { "tabell": "PQ_Saldobalanse" }, "inline_data": [] }
Svar:        { "analyse_id": "uuid", "avvik": [], "logg": [ { "steg": 1, "tid": "...", "melding": "..." } ] }
```

---

### Gruppe 3 — Frontend: Office Add-in (Task Pane)

**Ingress:** Et TypeScript-prosjekt som legger til en "AI-Revisor"-knapp i Excel-båndet og åpner et sidepanel. I Fase 1 gjør knappen kun én ting: kaller `/health` på backend og viser svaret. Dette er tilstrekkelig til å bekrefte at Task Pane kan nå localhost.

- [ ] Initialiser npm-prosjekt i `frontend/`: `npm init -y`
- [ ] Installer avhengigheter: `@types/office-js`, `office-addin-debugging`, `webpack`, `webpack-cli`, `ts-loader`, `typescript`, `html-webpack-plugin`
- [ ] Installer `office.js` som CDN-referanse i HTML (ikke npm-pakke)
- [ ] Opprett `frontend/manifest.xml` med:
  - [ ] Globalt unik Add-in ID (generer UUID)
  - [ ] Visningsnavn: "AI-Revisor"
  - [ ] Task Pane URL: `https://localhost:3000/taskpane.html`
  - [ ] Ribbon-knapp med ikon og label "Analyser"
  - [ ] Tillatelse: `ReadWriteDocument`
- [ ] Opprett `frontend/src/taskpane.html` med:
  - [ ] `<script>` som laster Office.js fra CDN
  - [ ] Knapp med id `btnAnalyser` og tekst "Test tilkobling"
  - [ ] Statusfelt (`<div id="status">`) for lasting/feil-melding
  - [ ] Responsfelt (`<div id="resultat">`) for visning av svar fra backend
- [ ] Opprett `frontend/src/taskpane.ts` med:
  - [ ] `Office.onReady()` som aktiverer knappen når Office er klar
  - [ ] Knappehandler: kaller `GET http://localhost:8000/health` med `Authorization: Bearer <token>` header
  - [ ] Velykket svar: viser versjon og tidsstempel i `#resultat`
  - [ ] Feilhåndtering: viser lesbar melding i `#status` hvis backend ikke svarer eller returnerer feil
- [ ] Opprett `frontend/tsconfig.json` og `frontend/webpack.config.js` konfigurert for Office Add-in
- [ ] Verifiser at `npm run build` i `frontend/` produserer bundle uten kompileringsfeil

---

### Gruppe 4 — Lokal utvikling og sidelasting i Excel

**Ingress:** For å teste Add-in i Excel Desktop uten å publisere til AppSource brukes sidelasting via en lokal filkatalog. Dette er standardprosedyren under utvikling.

- [ ] Start webpack devserver: `npm run dev-server` i `frontend/` (HTTPS på `localhost:3000`)
- [ ] Sideload manifest i Excel Desktop:
  - Fil → Alternativer → Klareringssenter → Innstillinger for klareringssenter → Klarerte App-kataloger → legg til sti til `frontend/`-mappen
  - Start Excel på nytt → Sett inn → Mine tillegg → velg "AI-Revisor"
- [ ] Verifiser at "Analyser"-knappen vises i Excel-båndet
- [ ] Start backend parallelt (`uvicorn`) og klikk knappen — forvent svar i Task Pane
- [ ] Dokumenter full oppstartsprosedyre i `docs/utvikling.md`

---

### Gruppe 5 — PyInstaller-pakking

**Ingress:** Backend pakkes til en frittstående `agent.exe` som ikke krever Python installert på kundens maskin. Installasjonsstedet er `C:\Users\[navn]\AppData\Local\AI-Revisor\agent.exe`.

- [ ] Installer PyInstaller i backend-miljøet: `pip install pyinstaller`
- [ ] Opprett `infra/agent.spec` — PyInstaller one-file-spec med:
  - [ ] Entry-point: `backend/core/main.py`
  - [ ] Inkluder `.env`-fil som data-fil
  - [ ] Ekskluder tunge, unødvendige pakker (f.eks. `tkinter`)
  - [ ] Sett appnavn til `AI-Revisor`
- [ ] Opprett `infra/build.ps1` (Windows PowerShell) som kaller `pyinstaller infra/agent.spec`
- [ ] Bygg `agent.exe` og verifiser at filen produseres uten feil
- [ ] Kopier `agent.exe` til en ren Windows-maskin uten Python og kjør den
- [ ] Verifiser at `GET /health` svarer korrekt fra den pakkede exe-en

---

### Gruppe 6 — Windows-autostart

**Ingress:** Agent skal starte automatisk med Windows slik at økonomen aldri trenger å starte den manuelt. Dette gjøres via Windows startup-mappen (ingen admin-rettigheter nødvendig).

- [ ] Definer installasjonssti: `C:\Users\[navn]\AppData\Local\AI-Revisor\`
- [ ] Kopier `agent.exe` til installasjonsstien
- [ ] Opprett snarvei i `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\` som peker på `agent.exe`
- [ ] Start Windows på nytt og verifiser at `agent.exe` kjører etter oppstart (sjekk Task Manager)
- [ ] Verifiser at `GET http://localhost:8000/health` svarer innen 10 sekunder etter pålogging

---

### Gruppe 7 — Integrasjonstest og bevis

**Ingress:** Denne gruppen dokumenterer og beviser at Fase 1 er fullført. Resultatet brukes som demonstrasjonsmateriale og som regresjonsgrunnlag for neste fase.

- [ ] Skriv pytest-integrasjonstester i `backend/core/tester/test_api.py`:
  - [ ] Test: `GET /health` med gyldig token → HTTP 200, felt `status`, `version`, `timestamp` finnes
  - [ ] Test: `GET /health` uten token → HTTP 401
  - [ ] Test: `GET /health` med feil token → HTTP 401
  - [ ] Test: `POST /v1/analyse` med gyldig token og minimal payload → HTTP 200, felt `analyse_id` og `logg` finnes
- [ ] Kjør alle tester: `pytest backend/core/tester/` — alle skal være grønne
- [ ] Gjennomfør manuell handshake-test i Excel Desktop:
  - [ ] Åpne Excel, finn "Analyser"-knappen i båndet
  - [ ] Klikk knappen — sidepanel åpnes, svar fra backend vises med versjon og tidsstempel
  - [ ] Stopp backend og klikk knappen igjen — lesbar feilmelding vises i Task Pane
- [ ] Ta skjermbilde av fungerende handshake og lagre i `docs/fase-1-bevis.png`
- [ ] Gjør avsluttende commit: `feat(core): fase 1 handshake komplett`

---

## Verifikasjon etter opprettelse

Etter at alle filer er skrevet leses `specs/fase-1-plan.md` for å bekrefte at innhold og formatering er riktig. Ingen implementeringskode skrives — dette er et planleggingsdokument.
