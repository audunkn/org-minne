"""
Anomalideteksjon — 4-algoritme ensemble.

Brukes av /v1/analyse-endepunktet.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler

MINIMUM_RADER = 5


class AnomaliFeil(Exception):
    def __init__(self, melding: str) -> None:
        self.melding = melding
        super().__init__(melding)


def finn_kolonner(rader: list[dict[str, Any]]) -> tuple[str, list[str]]:
    """Returnerer (id_kolonne, feature_kolonner).

    id_kolonne  = første nøkkel i første rad.
    feature_kolonner = øvrige kolonner der alle rader har numerisk verdi
                       (int/float, ikke bool, ikke None).
    """
    if not rader:
        raise AnomaliFeil("Ingen rader i input.")

    alle_nøkler = list(rader[0].keys())
    id_kolonne = alle_nøkler[0]
    kandidater = alle_nøkler[1:]

    df = pd.DataFrame(rader)
    feature_kolonner: list[str] = []
    for kol in kandidater:
        serie = pd.to_numeric(df[kol], errors="coerce")
        if serie.isna().any():
            continue
        feature_kolonner.append(kol)

    return id_kolonne, feature_kolonner


def kjør_anomalideteksjon(rader: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Kjører 4-algoritme ensemble og returnerer ett avvik-entry per rad.

    Rekkefølgen i returlisten matcher rekkefølgen i ``rader``.

    Reiser AnomaliFeil hvis:
    - Færre enn MINIMUM_RADER rader
    - Ingen numeriske feature-kolonner ble funnet
    """
    n = len(rader)
    if n < MINIMUM_RADER:
        raise AnomaliFeil(
            f"Minimum {MINIMUM_RADER} rader kreves for anomalideteksjon; fikk {n}."
        )

    id_kolonne, feature_kolonner = finn_kolonner(rader)

    if not feature_kolonner:
        raise AnomaliFeil(
            "Ingen numeriske feature-kolonner funnet. "
            "Minst én kolonne (utenom første) må ha numeriske verdier i alle rader."
        )

    df = pd.DataFrame(rader)
    X = df[feature_kolonner].to_numpy(dtype=float)

    # --- Z-score ---
    z_abs = np.abs(stats.zscore(X, axis=0))
    zscore_max_per_rad = z_abs.max(axis=1)
    zscore_flagg = zscore_max_per_rad > 2.5

    # --- IQR ---
    q1 = np.percentile(X, 25, axis=0)
    q3 = np.percentile(X, 75, axis=0)
    iqr = q3 - q1
    nedre = q1 - 1.5 * iqr
    øvre = q3 + 1.5 * iqr
    iqr_flagg = np.any((X < nedre) | (X > øvre), axis=1)

    # --- Skalert data for IsolationForest og LOF ---
    scaler = StandardScaler()
    X_skalert = scaler.fit_transform(X)

    # --- IsolationForest ---
    contamination = min(0.20, max(1 / n, 0.01))
    iso = IsolationForest(n_estimators=200, contamination=contamination, random_state=42)
    iso_pred = iso.fit_predict(X_skalert)
    iso_score = iso.score_samples(X_skalert)
    iso_flagg = iso_pred == -1

    # --- LOF ---
    n_neighbors = min(5, n - 1)
    lof = LocalOutlierFactor(n_neighbors=n_neighbors, contamination=contamination)
    lof_pred = lof.fit_predict(X_skalert)
    lof_score = lof.negative_outlier_factor_
    lof_flagg = lof_pred == -1

    # --- Bygg resultat ---
    avvik: list[dict[str, Any]] = []
    for i in range(n):
        utløste: list[str] = []
        if zscore_flagg[i]:
            utløste.append("Z-score")
        if iqr_flagg[i]:
            utløste.append("IQR")
        if iso_flagg[i]:
            utløste.append("IsolationForest")
        if lof_flagg[i]:
            utløste.append("LOF")

        antall_flagg = len(utløste)
        avvik.append(
            {
                "id": str(df[id_kolonne].iloc[i]),
                "antall_flagg": antall_flagg,
                "metoder": utløste,
                "er_anomali": antall_flagg >= 2,
                "zscore_max": round(float(zscore_max_per_rad[i]), 3),
                "isolation_forest_score": round(float(iso_score[i]), 4),
                "lof_score": round(float(lof_score[i]), 4),
            }
        )

    return avvik
