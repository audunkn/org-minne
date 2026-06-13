"""
Integrasjonstester for POST /v1/forklaring.
"""
import sys
import os
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("TOKEN", "test-token-fase1")
os.environ.setdefault("VERSION", "0.1.0")
os.environ.setdefault("PORT", "8000")
os.environ.setdefault("LLM_LEVERANDØR", "openai")
os.environ.setdefault("OPENAI_API_KEY", "sk-test")

from fastapi.testclient import TestClient
from main import app  # noqa: E402

client = TestClient(app, raise_server_exceptions=True)

GYLDIG_TOKEN = "test-token-fase1"


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


PAYLOAD = {
    "bedrift": "Avd0",
    "anomali_forklaring": "univariat: Kostnad=999999.0",
}

FORVENTET_TEKST = "Analyse: Kostnaden er svært høy.\n\nSitater:\n• sitat 1"


def test_forklaring_returnerer_tekst():
    """POST /v1/forklaring med gyldig token returnerer 200 og tekst som string."""
    with patch("main.generer_forklaring", return_value=FORVENTET_TEKST):
        svar = client.post("/v1/forklaring", json=PAYLOAD, headers=auth(GYLDIG_TOKEN))

    assert svar.status_code == 200
    data = svar.json()
    assert "tekst" in data
    assert isinstance(data["tekst"], str)
    assert data["tekst"] == FORVENTET_TEKST


def test_forklaring_krever_auth():
    """POST /v1/forklaring uten token returnerer 401."""
    svar = client.post("/v1/forklaring", json=PAYLOAD)
    assert svar.status_code == 401
