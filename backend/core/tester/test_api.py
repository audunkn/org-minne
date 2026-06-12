"""
Integrasjonstester for Fase 1 — handshake-bevis.

Kjøres med:  pytest backend/core/tester/
"""
import os
import sys

import pytest
from fastapi.testclient import TestClient

# Legg backend/core på sys.path slik at 'modeller' kan importeres
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Sett gyldige env-variabler før main.py lastes
os.environ.setdefault("TOKEN", "test-token-fase1")
os.environ.setdefault("VERSION", "0.1.0")
os.environ.setdefault("PORT", "8000")

from main import app  # noqa: E402  (import etter sys.path-oppsett)

GYLDIG_TOKEN = "test-token-fase1"
FEIL_TOKEN = "feil-token"

client = TestClient(app, raise_server_exceptions=True)


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------

def test_health_med_gyldig_token():
    svar = client.get("/health", headers=auth(GYLDIG_TOKEN))
    assert svar.status_code == 200
    data = svar.json()
    assert "status" in data
    assert "version" in data
    assert "timestamp" in data
    assert data["status"] == "ok"


def test_health_uten_token():
    svar = client.get("/health")
    assert svar.status_code == 401


def test_health_med_feil_token():
    svar = client.get("/health", headers=auth(FEIL_TOKEN))
    assert svar.status_code == 401


# ---------------------------------------------------------------------------
# /v1/analyse
# ---------------------------------------------------------------------------

def test_analyse_med_gyldig_token_og_minimal_payload():
    payload = {
        "kilde": "excel_tabell",
        "referanse": {"tabell": "PQ_Saldobalanse"},
        "inline_data": [],
    }
    svar = client.post("/v1/analyse", json=payload, headers=auth(GYLDIG_TOKEN))
    assert svar.status_code == 200
    data = svar.json()
    assert "analyse_id" in data
    assert "logg" in data
    assert isinstance(data["logg"], list)
    assert len(data["logg"]) > 0


def test_analyse_uten_token():
    payload = {"kilde": "excel_tabell"}
    svar = client.post("/v1/analyse", json=payload)
    assert svar.status_code == 401


def test_analyse_med_feil_token():
    payload = {"kilde": "excel_tabell"}
    svar = client.post("/v1/analyse", json=payload, headers=auth(FEIL_TOKEN))
    assert svar.status_code == 401


def test_analyse_med_for_få_rader():
    payload = {
        "kilde": "excel_tabell",
        "inline_data": [
            {"Avdeling": "A", "Kostnad": 100.0},
            {"Avdeling": "B", "Kostnad": 200.0},
            {"Avdeling": "C", "Kostnad": 300.0},
        ],
    }
    svar = client.post("/v1/analyse", json=payload, headers=auth(GYLDIG_TOKEN))
    assert svar.status_code == 200
    data = svar.json()
    assert data["avvik"] == []
    assert any("ikke kjørt" in steg["melding"].lower() or "minimum" in steg["melding"].lower()
               for steg in data["logg"])


def test_analyse_med_reelle_data_og_outlier():
    rader = [
        {"Avdeling": f"Avd{i}", "Kostnad": 100.0 + i, "Volum": 50.0 + i}
        for i in range(8)
    ]
    rader.append({"Avdeling": "Outlier", "Kostnad": 999999.0, "Volum": 999999.0})
    payload = {"kilde": "excel_tabell", "inline_data": rader}
    svar = client.post("/v1/analyse", json=payload, headers=auth(GYLDIG_TOKEN))
    assert svar.status_code == 200
    data = svar.json()
    assert len(data["avvik"]) == 9
    outlier = data["avvik"][-1]
    assert outlier["er_anomali"] is True
