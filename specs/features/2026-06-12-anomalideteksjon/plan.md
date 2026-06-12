# Fase 2 — Anomalideteksjon: implementeringsplan

## Gruppe 1 — Backend: anomalimodul (TDD)

- [ ] Skriv `backend/core/tester/test_anomali.py` med 7 tester (alle røde)
- [ ] Opprett `backend/core/analyse/__init__.py` (tom pakke)
- [ ] Implementer `backend/core/analyse/anomali.py` (grønn)
- [ ] Commit: `test(anomali): røde tester for anomalimodul`
- [ ] Commit: `feat(anomali): 4-algoritme ensemble med generisk skjemadeteksjon`

## Gruppe 2 — Backend: dependencies

- [ ] Legg til numpy, scipy, pandas, scikit-learn i `backend/core/requirements.txt`
- [ ] Fjern numpy og scipy fra `excludes` i `infra/agent.spec`
- [ ] Commit: `chore(deps): legg til numpy/scipy/pandas/scikit-learn`

## Gruppe 3 — Backend: API-integrasjon (TDD)

- [ ] Legg til 2 nye tester i `backend/core/tester/test_api.py` (røde)
- [ ] Oppdater `backend/core/main.py` med `kjør_anomalideteksjon`-integrasjon (grønn)
- [ ] Commit: `feat(api): integrer anomalideteksjon i /v1/analyse`

## Gruppe 4 — Frontend: knapp og manifest

- [ ] Legg til `<button id="btnAnomali">` i `frontend/src/taskpane.html`
- [ ] Legg til `AnomaliButton`-kontroll i `frontend/manifest.xml`
- [ ] Commit: `feat(frontend): legg til Anomali deteksjon-knapp i Task Pane og manifest`

## Gruppe 5 — Frontend: Excel.run lese/skrive

- [ ] Implementer `kjørAnomalideteksjon()` i `frontend/src/taskpane.ts`
- [ ] Commit: `feat(frontend): Excel-lese/skrive for anomalideteksjon`

## Gruppe 6 — Manuell verifikasjon og docs

- [ ] Manuell ende-til-ende test i Excel (se validation.md)
- [ ] Oppdater `CHANGELOG.md`
- [ ] Commit: `docs(changelog): fase 2 anomalideteksjon`
