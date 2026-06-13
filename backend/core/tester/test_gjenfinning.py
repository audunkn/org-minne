"""
Tester for rag/gjenfinning.py — søk mot ChromaDB.
"""
import sys
import os
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ---------------------------------------------------------------------------
# Hjelpefunksjoner for mock
# ---------------------------------------------------------------------------

def _lag_mock_samling(dokumenter: list[str]):
    """Returnerer en mock ChromaDB-samling som svarer med de gitte dokumentene."""
    mock_samling = MagicMock()
    mock_samling.query.return_value = {
        "documents": [dokumenter],
        "ids": [[f"id_{i}" for i in range(len(dokumenter))]],
        "distances": [[0.1 * i for i in range(len(dokumenter))]],
    }
    return mock_samling


def _lag_mock_klient(samling):
    mock_klient = MagicMock()
    mock_klient.get_or_create_collection.return_value = samling
    return mock_klient


# ---------------------------------------------------------------------------
# Tester
# ---------------------------------------------------------------------------

class TestSøkChromadb:

    def test_søk_returnerer_dokumenter(self):
        """søk_chromadb returnerer korrekte tekststrenger fra samlingen."""
        dokumenter = ["Selskapets inntekter økte markant i Q3.", "Kostnadsreduksjoner bidro til forbedret margin."]

        mock_samling = _lag_mock_samling(dokumenter)
        mock_klient = _lag_mock_klient(mock_samling)
        mock_modell = MagicMock()
        mock_modell.encode.return_value = [[0.1, 0.2, 0.3]]

        with (
            patch("rag.gjenfinning.chromadb.PersistentClient", return_value=mock_klient),
            patch("rag.gjenfinning.SentenceTransformer", return_value=mock_modell),
        ):
            from rag.gjenfinning import søk_chromadb
            resultat = søk_chromadb("Avd0 Kostnad høy", n_resultater=2)

        assert resultat == dokumenter

    def test_søk_tom_samling_returnerer_tom_liste(self):
        """søk_chromadb returnerer tom liste når samlingen er tom."""
        mock_samling = MagicMock()
        mock_samling.query.return_value = {
            "documents": [[]],
            "ids": [[]],
            "distances": [[]],
        }
        mock_klient = _lag_mock_klient(mock_samling)
        mock_modell = MagicMock()
        mock_modell.encode.return_value = [[0.1, 0.2, 0.3]]

        with (
            patch("rag.gjenfinning.chromadb.PersistentClient", return_value=mock_klient),
            patch("rag.gjenfinning.SentenceTransformer", return_value=mock_modell),
        ):
            from rag.gjenfinning import søk_chromadb
            resultat = søk_chromadb("Avd0 Kostnad høy", n_resultater=5)

        assert resultat == []
