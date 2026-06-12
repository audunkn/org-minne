# Fase 2 — Anomalideteksjon: krav og avgrensninger

## Scope

Utvider `/v1/analyse`-endepunktet til å kjøre en ensemble av fire algoritmer
(Z-score, IQR, IsolationForest, LOF) og returnere ett resultat per input-rad.
Brukeren limer inn et datasett i Excel, trykker "Anomali deteksjon", og får to
nye kolonner skrevet tilbake til høyre for dataene.

## Avgrensninger

- Minimum 5 rader kreves; færre rader gir `AnomaliFeil` og tomt `avvik`-felt i HTTP 200-svaret.
- Input-rekkefølge bevares: rad *i* i `avvik` svarer alltid til rad *i* i `inline_data`.
- Ingen ny Pydantic-modell for avvik-entry — `list[dict[str, Any]]` er tilstrekkelig.
- Ingen nytt endepunkt — `avvik`-feltet i eksisterende `/v1/analyse` fylles med reelle resultater.
- PyInstaller-kompatibilitet for sklearn utsettes (verifiseres ved første rebuild).

## Arkitekturvalg

**Generisk skjemadeteksjon:**
Første kolonne = identifikator/etikett. Øvrige kolonner der *alle* rader har
numerisk verdi (int/float, ikke bool, ikke None) = features.
Kolonner med minst én ikke-numerisk verdi ekskluderes som features.

**Kolonnedeteksjon:**
`pd.to_numeric(..., errors="coerce")` per kandidatkolonne; kolonner med NaN
etter koersjon utelates.

**Algoritme-parametere:**
- Z-score: flagg hvis maks abs > 2.5
- IQR: flagg hvis utenfor [Q1 - 1.5·IQR, Q3 + 1.5·IQR] på minst én feature
- IsolationForest: n_estimators=200, contamination=min(0.20, max(1/n, 0.01)), random_state=42
- LOF: n_neighbors=min(5, n-1), samme contamination-formel
- IsolationForest og LOF kjøres på StandardScaler-skalert data

**Avvik-entry per rad:**
```json
{
  "id": "<verdi fra id_kolonne, som str>",
  "antall_flagg": 0,
  "metoder": ["Z-score", "IQR"],
  "er_anomali": false,
  "zscore_max": 0.123,
  "isolation_forest_score": -0.1234,
  "lof_score": -1.2345
}
```

**er_anomali:** `antall_flagg >= 2`

**Input-rekkefølge bevares** slik at frontend kan skrive resultater posisjonelt
uten å matche på id-kolonnen.

## Norske feltnavn

Alle enum-verdier og feltnavn bevares på norsk. Algoritmenavnene i `metoder`
er unntatt (internasjonalt etablerte navn): "Z-score", "IQR",
"IsolationForest", "LOF".
