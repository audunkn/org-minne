# Endringslogg

## [Uutgitt]

### Planlagte implementeringer

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
