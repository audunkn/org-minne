# Endringslogg

## [Uutgitt]

### Planlagte implementeringer

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
