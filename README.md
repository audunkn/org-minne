# Det Organisatoriske Minnet

En AI-assistent for økonomiavdelinger, pakket inn i Excel-hverdagen de allerede kjenner.

## Konsept

Lukket, deterministisk system som gjør to ting som henger sammen:

1. Anomalianalyse av tall (statistikk eller ML, kjørt lokalt).
2. RAG-søk mot møtereferater og dokumenter for å forklare hvorfor avviket oppstod.

Hver kjøring lagres som et uforanderlig kontrollspor. Logikken er låst i kode — AI-en får kun lov til å lete og forklare.

## Arkitektur

```
/frontend          Office Add-in / Task Pane (TypeScript)
/backend
  /core            FastAPI, /v1/analyse, orkestrering
  /datasources     excel_tabell.py, lokal_fil.py, fabric.py
  /ai              openai.py, foundry.py
  /retrieval       lokal_vektor.py, azure_search.py
  /memory          sqlite.py + skjema
/infra             PyInstaller, build-scripts, manifest-maler
/docs              Utviklerveiledning, systemdok
/specs             Fase-planer og validering
```

## Kom i gang

Se [specs/fase-1-plan.md](specs/fase-1-plan.md) for Fase 1 — handshake mellom Excel og backend.

## Fase-veikart

| Fase | Mål |
|------|-----|
| 1    | Bevis at Excel (Add-in) og backend (FastAPI) snakker sammen |
| 2    | Anomalideteksjon på Excel-tabell med kjøringslogg |
| 3    | RAG mot lokale dokumenter |
| 4    | Sky-støtte via Cloudflare Tunnel / Excel Online |
| 5    | Fabric som datakilde |
| 6    | Automatisk utrulling og selvoppdatering |
