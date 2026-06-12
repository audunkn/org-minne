# Fase 2 — Anomalideteksjon: akseptansekriterier

## Gruppe 1 — Anomalimodul

- [ ] `test_for_få_rader_reiser_anomalifeil` grønn
- [ ] `test_ingen_numeriske_kolonner_reiser_anomalifeil` grønn
- [ ] `test_finn_kolonner_generisk_skjema` grønn
- [ ] `test_ren_data_ingen_anomali` grønn
- [ ] `test_tydelig_outlier_flagges` grønn
- [ ] `test_avvik_struktur` grønn
- [ ] `test_rekkefølge_bevares` grønn

## Gruppe 2 — Dependencies

- [ ] `pip install -r requirements.txt` kjøres uten feil
- [ ] `import sklearn` fungerer i backend-prosessen

## Gruppe 3 — API-integrasjon

- [ ] `test_analyse_med_for_få_rader` grønn
- [ ] `test_analyse_med_reelle_data_og_outlier` grønn
- [ ] Alle 6 eksisterende tester i test_api.py fortsatt grønne

## Gruppe 4 — Frontend-knapp

- [ ] "Anomali deteksjon"-knapp vises i Task Pane (deaktivert til Office.onReady)
- [ ] Knapp-control finnes i manifest.xml

## Gruppe 5 — Excel.run lese/skrive

- [ ] POST til /v1/analyse sendes med korrekt inline_data og token
- [ ] To nye kolonner ("Anomali", "Flagg") skrives rett til høyre for inputdata
- [ ] Outlier-rad viser "Ja" og høyere flagg-antall enn normale rader
- [ ] #resultat-panelet viser lesbar oppsummering

## Merge-sjekkliste

- [ ] Alle pytest-tester grønne (`pytest backend/core/tester/ -v`)
- [ ] Alle valideringspunkter over kryssav
- [ ] CHANGELOG.md oppdatert

## Risiko og oppfølging (ikke-blokkerende)

- **PyInstaller + sklearn:** scikit-learn kan kreve ekstra hiddenimports
  (f.eks. `sklearn.utils._cython_blas`). agent.exe vil bli markant større.
  Verifiseres ved første rebuild — ikke blokkerende for denne PR.
- **IsolationForest-determinisme:** random_state=42 gir deterministiske
  resultater, men contamination-parameteren varierer med n. Notert.
- **NaN/ikke-numerisk kolonnehåndtering:** kolonner med mixed typer
  ekskluderes stille som features. Grensesnitt med blank celle i Excel
  tolkes som tom streng — håndteres av pd.to_numeric koersjon.
