# Arkitektur: "Det Organisatoriske Minnet"

En AI-assistent for økonomiavdelinger, pakket inn i Excel-hverdagen de allerede kjenner.

## Kontekst

Dette er et nytt prosjekt, uavhengig av personalisert-monitor. Grunnlaget er en lang
design-dialog (3010 avsnitt) der konseptet utviklet seg fra "kalle et API fra Excel" til en
komplett Enterprise-arkitektur. Brukeren er business controller med 20 års økonomierfaring og
7 til 8 års koding, og ser løsningen både som et kommersielt produkt (No Cure, No Pay mot SMB)
og som porteføljemateriale for utviklerstillinger.

Formålet med dette dokumentet er å fryse arkitekturen på beslutningsnivå før kode skrives.
Brukeren har bedt om å forfine arkitekturen, ikke kode ennå. Neste konkrete steg avgjøres etter
godkjenning av dette dokumentet.

## Konseptet

Et lukket, deterministisk system som gjør to ting som henger sammen:

1. Anomalianalyse av tall (statistikk eller ML, kjørt lokalt).
2. RAG-søk mot møtereferater og dokumenter for å forklare hvorfor avviket oppstod.

Hver kjøring lagres som et uforanderlig kontrollspor, slik at bedriftens uformelle hukommelse
bevares over tid. Logikken er låst i kode, og AI-en får kun lov til å lete og forklare.
Dette er differensieringen mot Copilot og Claude i Excel, der brukeren må kontrollere
AI-genererte formler manuelt hver gang.

## Låste beslutninger

Avklart gjennom dialogen og denne planleggingssesjonen:

- Frontend er Office Add-in (Task Pane) i TypeScript, ikke Office Scripts. Office Scripts kjører
  i Microsofts sky-sandkasse og kan ikke kalle en lokal backend. Task Pane kjører lokalt i
  WebView2 og kan snakke med localhost.
- Python i Excel (=PY) brukes ikke. Den har ingen utgående nettverkstilgang og er lisensavhengig.
- Motoren er en Python-app (FastAPI), pakket med PyInstaller til agent.exe.
- Datafangst skjer via Power Query inn i en navngitt Excel-tabell.
- Kontrollspor og organisatorisk minne lagres i lokal SQLite.
- Alle tre markedsnivåene bygges som moduler i én kodebase med felles Add-in-frontend.
- Nivå 3 (Fabric): backend kjører som lokal agent som kobler ut mot Fabrics SQL-endepunkt.
  Én driftsmodell på tvers av nivåene, enkel remote-fiksing.
- AI-lag er abstrahert bak et grensesnitt. OpenAI eller Anthropic brukes i demo, Azure AI Foundry
  som prod-modul.
- RAG: lokal vektorbase (Chroma eller sqlite-vss) for nivå 1 og 2, slik at sensitive dokumenter
  ikke forlater maskinen. Azure AI Search tas i bruk først på nivå 3.

## Arkitektur: delt kjerne, fire grensesnitt, tre konfigurasjoner

Excel-grensesnittet og Python-kjernen er identiske på alle tre nivåene. All variasjon presses inn
bak fire grensesnitt og velges via config per kunde. Et "nivå" blir da en kombinasjon av moduler.

### Kontrakt mellom Add-in og backend

Ett endepunkt, `POST /v1/analyse`. Add-in sender enten dataene direkte eller en referanse:

```json
{
  "kilde": "excel_tabell | lokal_fil | fabric",
  "referanse": { "tabell": "PQ_Saldobalanse", "sti": "...", "view": "vw_AnalyseKlar" },
  "inline_data": [ ... ]
}
```

Backend svarer med analyseresultat og en strukturert kjøringslogg (steg med tidsstempel og
linjereferanser) som Task Pane tegner som den pedagogiske tidslinjen. Små datasett sendes inline,
Fabric og store sett sendes som referanse og hentes av backend. Dette løser push mot pull i én
kontrakt.

### De fire grensesnittene

| Grensesnitt  | Ansvar                                  | Implementasjoner                                      |
|--------------|-----------------------------------------|-------------------------------------------------------|
| DataSource   | `hent_data(referanse) -> DataFrame`     | ExcelTabell, LokalFil (openpyxl), Fabric (pyodbc/view) |
| AIProvider   | `analyser()`, `embed()`                 | OpenAI (demo), Foundry (prod)                          |
| Retriever    | `søk(spørring) -> avsnitt`              | LokalVektorbase (Chroma/sqlite-vss), AzureAISearch     |
| MemoryStore  | kontrollspor og organisatorisk minne    | SQLite (WAL-modus for flerbruker)                      |

Kjernen (anomalideteksjon, RAG-orkestrering, loggbygger) kjenner bare grensesnittene. Bytte av
nivå skjer ved å bytte implementasjon i config.

### De tre nivåene som konfigurasjon

- Nivå 1, manuell/ad-hoc: ExcelTabell eller LokalFil, LokalVektorbase, OpenAI. Backend som lokal
  agent.exe på localhost. Målgruppe: bedrifter med manuelle Excel-ark.
- Nivå 2, hybrid: samme moduler, men Add-in når backend via localhost eller Cloudflare Tunnel.
  Frontend slår opp endepunktet dynamisk. To deployment-varianter:
  - 2a (server hos kunden): agent.exe på Windows Server / Azure VM kunden eier. Cloudflare
    Tunnel eksponerer fast domene. Brukes når kunden har infrastruktur.
  - 2b (container, SaaS): agent.exe i Docker, deployes til Azure Container Apps eller VPS per
    kunde. Leverandøren (oss) drifter instansen. Endrer prismodell til abonnement.
  Målgruppe: M365-bedrifter med tunge Power Query-modeller eller Excel Online-brukere uten
  lokal agent.
- Nivå 3, fullskala Fabric: Fabric som DataSource, AzureAISearch som Retriever, Foundry som
  AIProvider. Lokal agent kobler ut mot Fabrics SQL-endepunkt. Målgruppe: bedrifter på Fabric.

Samme Add-in-knapp ser lik ut og oppfører seg likt for økonomisjefen uansett nivå.

## Monorepo-struktur

```
/frontend          Office Add-in / Task Pane (delt, identisk)
/backend
  /core            FastAPI, /v1/analyse, orkestrering, loggbygger
  /datasources     excel_tabell.py, lokal_fil.py, fabric.py
  /ai              openai.py, foundry.py
  /retrieval       lokal_vektor.py, azure_search.py
  /memory          sqlite.py + skjema
  config.json      velger moduler per nivå
/infra             GitHub Actions, PyInstaller, manifest-maler, tunnel-config
/docs              systemdok.md, IT-whitepaper.md
```

## Tverrgående valg

- API-versjonering i URL (`/v1/`) for zero-downtime-oppdatering. Frontend pinner versjonen.
- Token-autentisering også lokalt, slik at vilkårlige prosesser ikke kan treffe localhost-porten.
- CORS i FastAPI for Add-in-origin. WebView2-runtime som krav på Desktop.
- SQLite i WAL-modus, og backend som eneste skriver. Dette løser "fil låst av annen bruker".
- Hemmeligheter (Azure- og API-nøkler) i `.env` eller Key Vault, aldri i kode eller Excel.
- Kodesignering av agent.exe med Code Signing Certificate, så Windows SmartScreen ikke flagger den.
- Runtime-lokasjon for agent.exe: `C:\Users\[navn]\AppData\Local\AI-Revisor\agent.exe` på
  kundens PC. Starter med Windows, lytter på localhost:8000. Ingenting kjører i SharePoint.
- CI/CD: GitHub Actions bygger agent.exe (PyInstaller) og kompilerer frontend. Ferdig agent.exe
  lastes opp til en SharePoint-mappe som distribusjonskanal — IT henter derfra, eller exe-en
  laster ned selv ved neste oppstart.
- Selvoppdatering: agent.exe sammenligner sin versjon mot version.txt i SharePoint-mappen ved
  oppstart, og erstatter seg selv hvis en nyere versjon finnes.
- Backup av SQLite i tre ledd: SQLite-filen legges i en mappe som OneDrive/SharePoint
  synkroniserer automatisk (gir versjonshistorikk på den levende, lokale databasen), intern
  shutil-kopi med dato, og IT-avdelingens ordinære backuprutiner.

## Risikoer og mitigeringer

Fra djevelens advokat-gjennomgangen i dialogen:

- Microsoft endrer API-regler og bryter integrasjonen. Mitigering: hold frontend tynn, isoler
  alt mot grensesnittene, versjonér endepunkt.
- Søppel inn, søppel ut ved dårlige møtereferater. Mitigering: vis kilde og treffsikkerhet i
  loggen, la superbruker korrigere og "oppdra" minnet.
- IT flagger usignert exe. Mitigering: kodesignering og IT-whitepaper på én side.
- Skaleringsfellen med per-kunde installasjoner. Mitigering: superbruker-modell og sentralisert
  remote-vedlikehold.

## Åpne punkter (avgjøres når vi går til bygging)

- Eget repo for prosjektet. Skal ikke ligge i personalisert-monitor.
- Hvilket nivå som skal være første byggemål, og om første leveranse er demo eller MVP.
- Valg av statistikk mot ML for anomalidelen (Z-score og kvartiler mot Isolation Forest).
- Konkret design og innhold i Task Pane (tidslinje, kodevisning, godkjenn-knapp).
- Tunnel-leverandør for testing (Cloudflare Tunnel anbefalt foran ngrok for faste domener).
- Nivå 2-valg: 2a (agent hos kunden, enklere drift) eller 2b (container hos oss, SaaS-modell
  med abonnement). Avgjør forretningsmodell og hvem som bærer driftskostnad og -ansvar.

## Validering, veien videre

Når vi går til bygging valideres arkitekturen risiko-først:

1. Handshake: Office Add-in (Task Pane) kaller en minimal FastAPI på localhost og viser svaret i
   Excel. Dette beviser den mest kritiske antakelsen og fjerner det meste av teknisk risiko.
2. Datakilde: les en navngitt Power Query-tabell via Add-in og kjør en enkel anomalisjekk i
   backend, med strukturert kjøringslogg tilbake til Task Pane.
3. RAG lokalt: vektoriser et testreferat i lokal vektorbase, søk på et avvik, og få forklaring.
4. Sky-vei: eksponer samme localhost via Cloudflare Tunnel og verifiser at Excel Online treffer
   agent.exe.
5. Fabric: koble backend mot Fabrics SQL-endepunkt via et view og bekreft at Excel Desktop og
   backend leser samme objekt.
6. Drift: push til main, la GitHub Actions bygge agent.exe, og bekreft selvoppdatering via
   version.txt hos en simulert kunde.

Hvert trinn er kjørbart og demonstrerbart isolert, og egner seg som scener i demo- eller
YouTube-materiellet.

## Veikart — hva som bygges, steg for steg

---

### Fase 1 — Bevis at delene snakker sammen

**Hva vi gjør:**
Vi installerer det lille bakgrunnsprogrammet (motoren) på en PC og legger til en ny knapp i
Excel. Knappen gjør ingenting annet enn å sende en testmelding til motoren og vise svaret
tilbake i Excel.

**Hva vi ser når det virker:**
Økonomen trykker på knappen i Excel. En liten panel åpner seg og viser en bekreftelse: motoren
er i gang, versjon og tidsstempel er synlig.

**Hvorfor dette er viktig:**
Hele løsningen er avhengig av at Excel og motoren kan kommunisere. Inntil vi har vist dette i
praksis, er alt annet teori. Denne fasen fjerner den største tekniske risikoen på én til to
dager.

---

### Fase 2 — Hent tallene og pek på det som ser rart ut

**Hva vi gjør:**
Vi kobler Excel-tabellen med saldobalansen (eller annen regnskapsdata) til motoren. Motoren
kjører en statistisk analyse og finner kontoer eller poster som skiller seg ut fra normalen —
for eksempel en kostnad som er dobbelt så høy som foregående periode, eller en inntektspost
som plutselig er null.

**Hva vi ser når det virker:**
Økonomen åpner sin vanlige Excel-fil, trykker på Analyser-knappen, og får opp en liste i
sidepanelet: "Disse seks postene bør undersøkes nærmere" — med kontonummer, beløp og en kort
forklaring på avviket. Analysen og resultatet lagres automatisk med tidsstempel, slik at det
finnes en logg over hva som ble gjort og når.

**Hvorfor dette er viktig:**
Dette er selve kjernen i produktet. En økonom med 200 kontoer i balansen kan nå få flagget de
fem til ti som faktisk fortjener oppmerksomhet, i stedet for å bla gjennom alle manuelt.

---

### Fase 3 — Finn ut hvorfor avviket skjedde

**Hva vi gjør:**
Vi laster inn møtereferater, styreprotokoller og interne notater i systemet. Motoren lærer seg
innholdet og kan søke i det. Når et avvik er funnet, søker motoren automatisk gjennom
dokumentene og ser om avviket ble diskutert, besluttet eller varslet et sted.

**Hva vi ser når det virker:**
Under avviket i sidepanelet dukker det opp et avsnitt: "Dette kan henge sammen med styremøtet
14. mars, der det ble besluttet å øke markedsbudsjettet med 40 %. Kilde: styreprotokoll
Q1-2025, side 3." Økonomen vurderer selv om forklaringen stemmer. Hvis den gjør det, kan
hen bekrefte og lagre koblingen. Hvis ikke, kan hen notere en annen forklaring — som da
inngår i systemets hukommelse til neste gang.

**Hvorfor dette er viktig:**
Dette er det som skiller løsningen fra et vanlig avviksverktøy. Over tid bygger systemet opp
et organisatorisk minne: bedriftens uformelle kunnskap blir søkbar og sporbar.

---

### Fase 4 — Gjør løsningen tilgjengelig for sky-brukere

**Hva vi gjør:**
Vi sørger for at løsningen også fungerer for ansatte som bruker Excel i nettleseren (Microsoft
365 Online) og ikke har programmet installert på sin egen PC. Motoren flyttes til en server
— enten en server kunden allerede har, eller en vi setter opp — og kobles sikkert til Excel
Online.

**Hva vi ser når det virker:**
En controller som jobber fra en nettbrett eller en delt PC logger inn i Excel Online, åpner
den samme Add-in-knappen, og får nøyaktig samme analyseopplevelse som en kollega med
lokalt installert program. Ingen forskjell fra brukerens perspektiv.

**Hvorfor dette er viktig:**
Mange bedrifter har gått bort fra fast installasjon av programmer. Uten denne fasen er
løsningen utilgjengelig for en stor del av markedet.

---

### Fase 5 — Koble til Fabric for kunder med skybasert datagrunnlag

**Hva vi gjør:**
Noen kunder lagrer all regnskapsdata i Microsofts skyplattform Fabric i stedet for i
Excel-filer. Vi utvider motoren slik at den kan hente data direkte derfra, uten at
økonomen trenger å eksportere noe til Excel først.

**Hva vi ser når det virker:**
Økonomen trykker på Analyser-knappen. Motoren henter fersk data fra Fabric, kjører analysen,
og viser resultatet i sidepanelet — på samme måte som i tidligere faser. Økonomen merker
ingen forskjell annet enn at dataene alltid er oppdaterte.

**Hvorfor dette er viktig:**
Fabric er Microsofts satsning for større bedrifter og er i sterk vekst. Denne fasen gjør
løsningen relevant for det segmentet som bruker mest på datainfrastruktur.

---

### Fase 6 — Automatisk utrulling og selvoppdatering

**Hva vi gjør:**
Vi setter opp en prosess som automatisk bygger og distribuerer nye versjoner av programmet når
vi legger inn forbedringer. Programmet sjekker ved oppstart om det finnes en nyere versjon og
oppdaterer seg selv. IT-avdelingen hos kunden trenger ikke gjøre noe.

**Hva vi ser når det virker:**
Vi publiserer en feilretting klokken 10. Innen klokken 11 har alle kundenes motorer lastet ned
og installert oppdateringen automatisk neste gang de startet. Økonomen merker ingenting — annet
enn at det kanskje går litt raskere.

**Hvorfor dette er viktig:**
Uten dette må vi rulle ut oppdateringer manuelt hos hver enkelt kunde. Det er tidkrevende og
feilbarlig. Med dette på plass kan vi drifte mange kunder uten at driftskostnaden vokser
proporsjonalt.
