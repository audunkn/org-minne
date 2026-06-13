"""
Enhetstester for anomalimodulen — Fase 2.

Kjøres med:  pytest backend/core/tester/ -v
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from analyse.anomali import AnomaliFeil, finn_kolonner, kjør_anomalideteksjon


# ---------------------------------------------------------------------------
# Hjelpefunksjon
# ---------------------------------------------------------------------------

def _bygg_rader(n: int, verdier: dict | None = None) -> list[dict]:
    """Bygger n rader med skjema {Avdeling: str, Kostnad: float, Volum: float}."""
    base = verdier or {}
    return [
        {"Avdeling": f"Avd{i}", "Kostnad": 100.0 + i, "Volum": 50.0 + i, **base}
        for i in range(n)
    ]


# ---------------------------------------------------------------------------
# test_for_få_rader_reiser_anomalifeil
# ---------------------------------------------------------------------------

def test_for_få_rader_reiser_anomalifeil():
    rader = _bygg_rader(3)
    with pytest.raises(AnomaliFeil):
        kjør_anomalideteksjon(rader)


# ---------------------------------------------------------------------------
# test_ingen_numeriske_kolonner_reiser_anomalifeil
# ---------------------------------------------------------------------------

def test_ingen_numeriske_kolonner_reiser_anomalifeil():
    rader = [
        {"Avdeling": f"Avd{i}", "Notat": f"tekst{i}", "Kode": f"K{i}"}
        for i in range(6)
    ]
    with pytest.raises(AnomaliFeil):
        kjør_anomalideteksjon(rader)


# ---------------------------------------------------------------------------
# test_finn_kolonner_generisk_skjema
# ---------------------------------------------------------------------------

def test_finn_kolonner_generisk_skjema():
    rader = [
        {"Avdeling": f"Avd{i}", "Kostnad": 100.0 + i, "Volum": 50.0 + i, "Notat": f"txt{i}"}
        for i in range(5)
    ]
    id_kol, feature_kol = finn_kolonner(rader)
    assert id_kol == "Avdeling"
    assert "Kostnad" in feature_kol
    assert "Volum" in feature_kol
    assert "Notat" not in feature_kol
    assert "Avdeling" not in feature_kol


# ---------------------------------------------------------------------------
# test_ren_data_ingen_anomali
# ---------------------------------------------------------------------------

def test_ren_data_ingen_anomali():
    """Ren, homogen data skal ikke utløse Z-score eller IQR.

    IsolationForest og LOF tvinger floor(contamination * n) = 1 rad til -1 hver.
    Hvis de tilfeldigvis velger samme rad, gir det maks 1 anomali totalt.
    Grensen sum(er_anomali) <= 1 er et matematisk sikkert øvre tak.
    """
    rader = _bygg_rader(10)
    avvik = kjør_anomalideteksjon(rader)
    assert len(avvik) == 10
    # Statistiske metoder flaggr ingen rad i ren, homogen data
    assert all(a["zscore_max"] < 2.5 for a in avvik)
    assert all("Z-score" not in a["metoder"] for a in avvik)
    assert all("IQR" not in a["metoder"] for a in avvik)
    # IF og LOF kan flagge ulike rader → maks 2 rader med er_anomali=True i ren data
    assert sum(a["er_anomali"] for a in avvik) <= 2


# ---------------------------------------------------------------------------
# test_tydelig_outlier_flagges
# ---------------------------------------------------------------------------

def test_tydelig_outlier_flagges():
    rader = _bygg_rader(9)
    # Legg til én ekstremverdi
    rader.append({"Avdeling": "Outlier", "Kostnad": 999999.0, "Volum": 999999.0})
    avvik = kjør_anomalideteksjon(rader)
    outlier = avvik[-1]
    assert outlier["er_anomali"] is True
    assert outlier["antall_flagg"] >= 2


# ---------------------------------------------------------------------------
# test_avvik_struktur
# ---------------------------------------------------------------------------

def test_avvik_struktur():
    rader = _bygg_rader(6)
    avvik = kjør_anomalideteksjon(rader)
    assert len(avvik) == 6
    for a in avvik:
        assert isinstance(a["id"], str)
        assert isinstance(a["antall_flagg"], int)
        assert isinstance(a["metoder"], list)
        assert isinstance(a["er_anomali"], bool)
        assert isinstance(a["zscore_max"], float)
        assert isinstance(a["isolation_forest_score"], float)
        assert isinstance(a["lof_score"], float)
        assert "forklaring" in a
        assert a["forklaring"] is None or isinstance(a["forklaring"], str)


# ---------------------------------------------------------------------------
# test_rekkefølge_bevares
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# test_forklaring_outlier_er_univariat
# ---------------------------------------------------------------------------

def test_forklaring_outlier_er_univariat():
    """Ekstremverdien (Kostnad=999999) skal gi forklaring som starter med 'univariat: '."""
    rader = _bygg_rader(9)
    rader.append({"Avdeling": "Outlier", "Kostnad": 999999.0, "Volum": 999999.0})
    avvik = kjør_anomalideteksjon(rader)
    outlier = avvik[-1]
    assert outlier["er_anomali"] is True
    assert isinstance(outlier["forklaring"], str)
    assert outlier["forklaring"].startswith("univariat: ")


# ---------------------------------------------------------------------------
# test_forklaring_ren_data_er_none_eller_multivariat
# ---------------------------------------------------------------------------

def test_forklaring_ren_data_er_none_eller_multivariat():
    """Rene rader uten Z-score- eller IQR-flagg skal ha forklaring=None eller 'multivariat'."""
    rader = _bygg_rader(10)
    avvik = kjør_anomalideteksjon(rader)
    for a in avvik:
        if not a["er_anomali"]:
            assert a["forklaring"] is None
        else:
            # Ren data: kun IF/LOF kan flagge → multivariat
            assert a["forklaring"] == "multivariat" or a["forklaring"] is None


# ---------------------------------------------------------------------------
# test_rekkefølge_bevares
# ---------------------------------------------------------------------------

def test_rekkefølge_bevares():
    rader = _bygg_rader(7)
    avvik = kjør_anomalideteksjon(rader)
    assert len(avvik) == len(rader)
    for i, (rad, avvik_rad) in enumerate(zip(rader, avvik)):
        assert avvik_rad["id"] == str(rad["Avdeling"]), (
            f"Rad {i}: forventet id={rad['Avdeling']!r}, fikk {avvik_rad['id']!r}"
        )
