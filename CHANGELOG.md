# Endringslogg

## [Uutgitt]

### Ad hoc-endringer

#### fix(rag): score-terskel og query-konstruksjon *(2026-06-14 HH:MM)*

##### fix
- `rag_konfig.yaml`: hevet `score_terskel` fra 1.0 til 12.0 — for `paraphrase-multilingual-MiniLM-L12-v2` er relevante L2-distanser i range 9–11, terskel 1.0 filtrerte 100 % av resultater bort
- `backend/core/llm/forklaring.py`: `_bygg_rag_query()` — ny hjelpefunksjon som bygger semantisk query med `[Bedrift]`-prefiks og naturlig språk istedenfor teknisk `univariat: Kolonne=verdi`-streng; `"univariat: Omsetning=1890.0"` → `"[EDP] finansielle resultater Omsetning"`
- `backend/core/tester/test_gjenfinning.py`: oppdaterte mock-distanser [0.5, 1.5] → [9.0, 13.0] for å matche ny terskel

### Planlagte implementeringer

#### RAG-kvalitet — re-indeksering med bedriftsnavn og dotenv-fix *(2026-06-13 19:02)*

##### fix
- `backend/core/rag/indekser.py`: la til `load_dotenv()` slik at `.env`-filen leses ved kjøring av scriptet direkte

##### chore
- Slettet gammel `vector_db/` og re-indekserte 25 transkripsjoner — alle omdøpt med bedriftsprefiks, 1625 chunks indeksert

#### RAG-kvalitet — bedriftsidentifikasjon og score-terskel *(2026-06-13 HH:MM)*

##### feat
- `backend/core/rag/indekser.py`: `ekstraher_bedriftsnavn()` — kaller LLM på de første 2000 tegnene for å identifisere selskapet; returnerer "UKJENT" ved feil
- `backend/core/rag/indekser.py`: `indekser_fil()` — prefiks `[Bedrift] ` foran hver chunk, `bedrift`-nøkkel i metadata, filnavnbytte til `Bedrift_originalfilnavn.txt`
- `backend/core/rag/gjenfinning.py`: `søk_chromadb()` — filtrerer chunks med L2-distanse >= `score_terskel` (leses fra `rag_konfig.yaml`)
- `rag_konfig.yaml`: ny seksjon `søk.score_terskel: 1.0`

##### test
- `test_ekstraher_bedriftsnavn_returnerer_navn`: LLM svarer "EDP" → returnerer "EDP"
- `test_ekstraher_bedriftsnavn_feil_gir_ukjent`: LLM kaster → returnerer "UKJENT"
- `test_ekstraher_bedriftsnavn_renser_svar`: whitespace/linjeskift fjernes
- `test_chunk_prefiks_inneholder_bedrift`: chunk-tekst starter med `[EDP] `
- `test_metadata_inneholder_bedrift`: metadata har `bedrift`-nøkkel med korrekt verdi
- `test_søk_filtrerer_på_score_terskel`: kun chunks med distanse < terskel returneres

#### Fase 3, del 2 — LLM-analyse av anomalier med RAG-kontekst *(2026-06-13 17:00)*

##### feat
- `backend/core/rag/gjenfinning.py`: `søk_chromadb()` henter topp-N relevante chunks fra ChromaDB
- `backend/core/llm/klient.py`: `lag_llm_klient()` — fabrikk for OpenAI/Mistral basert på `LLM_LEVERANDØR`
- `backend/core/llm/forklaring.py`: `generer_forklaring()` — RAG-søk + prompt-bygging + LLM-kall
- `backend/core/main.py`: nytt endepunkt `POST /v1/forklaring` (`ForklaringForespørsel` → `ForklaringSvar`)
- `backend/core/modeller.py`: `ForklaringForespørsel` og `ForklaringSvar` lagt til
- `frontend/src/taskpane.html`: "LLM-analyse"-knapp (disabled inntil anomalideteksjon er kjørt)
- `frontend/src/taskpane.ts`: `kjørLLMAnalyse()` — leser Ja/Mulig-rader, kaller `/v1/forklaring`, skriver til "LLM-analyse"-kolonne med tekstvridd
- Progress-melding under kjøring: "LLM-analyse N av M rader…"
- Støtte for Mistral ved å sette `LLM_LEVERANDØR=mistral` i .env

##### test
- `test_forklaring_returnerer_tekst`: POST med gyldig token → 200, `tekst` er str
- `test_forklaring_krever_auth`: POST uten token → 401
- `test_søk_returnerer_dokumenter`: mock ChromaDB returnerer korrekte tekststrenger
- `test_søk_tom_samling_returnerer_tom_liste`: tom samling → `[]`

##### chore
- `openai>=1.0.0` og `mistralai>=1.0.0` lagt til i requirements.txt
- `LLM_LEVERANDØR`, `OPENAI_API_KEY`, `MISTRAL_API_KEY` lagt til i .env.mal

#### Fase 2 — `forklaring`-felt i anomaliresultat *(2026-06-13 HH:MM)*

##### feat
- `frontend/src/taskpane.ts`: ny "Forklaring"-kolonne i Excel-utskriften ved siden av "Anomali" og "Flagg"
- `backend/core/analyse/anomali.py`: nytt felt `forklaring` (str | None) i hvert avvik-entry
- Prioritering Z-score → IQR → multivariat: univariathendelser peker på konkret tallverdi
- Format `"univariat: {verdi}"` ved Z-score- eller IQR-flagg, `"multivariat"` ved kun IF/LOF, `None` uten flagg
- Format utvidet til `"univariat: {kolonnenavn}={verdi}"` — brukeren ser nå hvilken variabel som utløste flagget *(2026-06-13 16:00)*

##### test
- `test_avvik_struktur`: verifiserer at `forklaring`-nøkkel finnes og er `str | None`
- `test_forklaring_outlier_er_univariat`: ekstremverdien gir `forklaring` som starter med `"univariat: "` og inneholder kolonnenavnet (`"Kostnad"`)
- `test_forklaring_ren_data_er_none_eller_multivariat`: rene rader uten Z-score/IQR-flagg har `forklaring=None`

#### Fase 3, del 1 — RAG-indeksering av transkripsjoner *(2026-06-13 15:00)*

##### feat
- `backend/core/rag/indekser.py`: idempotent indeksering av norske resultatpresentasjoner i ChromaDB
- `rag_konfig.yaml`: konfigurerbar chunk-størrelse, overlapp, embedding-modell og db-sti
- Rekursiv chunking med korrekt tegnstart-tracking og separator-prioritering
- SentenceTransformer `paraphrase-multilingual-MiniLM-L12-v2` for norsk embedding
- Metadata per chunk: kilde_fil, chunk_nr, total_chunks, tegnstart
- ID-format `{filnavn}_{chunk_nr}` sikrer idempotens

##### test
- 17 enhetstester: konfigurasjonslasting, konfig-sti-traversering, chunking-logikk, idempotens, metadata, ID-format

##### chore
- chromadb==0.6.3, sentence-transformers==3.3.1, PyYAML==6.0.2 lagt til i requirements.txt
- `vector_db/` lagt til i .gitignore

#### Fase 2 — Anomalideteksjon *(2026-06-12)*

##### feat
- 4-algoritme ensemble (Z-score, IQR, IsolationForest, LOF) i `backend/core/analyse/anomali.py`
- Generisk skjemadeteksjon: første kolonne er identifikator, numeriske øvrige er features
- `/v1/analyse` returnerer nå reelle anomaliresultater (ikke lenger mock)
- Input-rekkefølge bevares — posisjonell skriving til Excel uten id-matching
- Ny "Anomali deteksjon"-knapp i Task Pane og manifest
- Excel-integrasjon: leser brukt område, skriver "Anomali"/"Flagg"-kolonner til høyre for data

##### test
- 7 enhetstester for anomalimodul (`test_anomali.py`)
- 2 nye API-integrasjonstester for `/v1/analyse` med reelle data og for-få-rader-håndtering

##### chore
- numpy==1.26.4, scipy==1.13.1, pandas==2.2.2, scikit-learn==1.5.1 lagt til i requirements.txt
- numpy og scipy fjernet fra PyInstaller excludes i agent.spec

#### Fase 1 — Bevis at delene snakker sammen

##### feat
- Office Add-in Task Pane med "Test tilkobling"-knapp og statusvisning
- FastAPI-backend med `/health` og `/v1/analyse` endepunkter
- Bearer token-autentisering på alle endepunkter
- CORS-konfigurasjon for Office-origins og localhost:3000
- Pydantic-modeller for forespørsel og svar
- Monorepo-struktur med frontend, backend, infra, docs, specs
- PyInstaller-spec og build.ps1 for pakking til agent.exe

##### test
- Pytest-integrasjonstester: /health (gyldig token, uten token, feil token)
- Pytest-integrasjonstester: /v1/analyse (gyldig token, uten token, feil token)

##### docs
- Utviklerveiledning med oppstartsprosedyre, sidelasting og autostart *(2026-05-29 15:41)*
- specs/fase-1-plan.md — detaljert implementeringssjekkliste *(2026-05-29 15:41)*

### Ad hoc-endringer

#### fix
- CORS preflight (OPTIONS) slipper nå gjennom token-middleware *(2026-05-31)*
- Dev-server bruker lokale PEM-sertifikater via office-addin-dev-certs i stedet for webpack --https-flagg *(2026-05-31)*
- Lagt til office-addin-dev-certs som devDependency *(2026-05-31)*
- PEM-filer ekskludert fra git via .gitignore *(2026-05-31)*
