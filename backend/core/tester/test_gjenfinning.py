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

def _lag_mock_samling(dokumenter: list[str], bedrifter: list[str] | None = None):
    """Returnerer en mock ChromaDB-samling som svarer med de gitte dokumentene.

    bedrifter: liste av bedriftsnavn som returneres fra samling.get() —
    brukes av _finn_matchende_bedrift(). Tom liste betyr ingen treff.
    """
    mock_samling = MagicMock()
    mock_samling.query.return_value = {
        "documents": [dokumenter],
        "ids": [[f"id_{i}" for i in range(len(dokumenter))]],
        "distances": [[0.1 * i for i in range(len(dokumenter))]],
    }
    mock_samling.get.return_value = {
        "metadatas": [{"bedrift": b} for b in (bedrifter or [])],
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

    def test_søk_filtrerer_på_score_terskel(self):
        """Dokumenter med distance >= score_terskel filtreres bort."""
        dokumenter = ["Relevant chunk", "Irrelevant chunk"]
        mock_samling = MagicMock()
        mock_samling.query.return_value = {
            "documents": [dokumenter],
            "ids": [["id_0", "id_1"]],
            "distances": [[9.0, 13.0]],  # 9.0 < 12.0 (terskel), 13.0 >= 12.0
        }
        mock_klient = _lag_mock_klient(mock_samling)
        mock_modell = MagicMock()
        mock_modell.encode.return_value = [[0.1, 0.2, 0.3]]

        with (
            patch("rag.gjenfinning.chromadb.PersistentClient", return_value=mock_klient),
            patch("rag.gjenfinning.SentenceTransformer", return_value=mock_modell),
        ):
            from rag.gjenfinning import søk_chromadb
            resultat = søk_chromadb("EDP kostnader", n_resultater=2)

        assert resultat == ["Relevant chunk"]

    def test_søk_med_eksakt_bedriftsnavn_sender_where_filter(self):
        """søk_chromadb sender where={'bedrift': 'KGHM'} ved eksakt match."""
        mock_samling = _lag_mock_samling(
            ["[KGHM] Inntektene økte markant i Q2."],
            bedrifter=["KGHM"],
        )
        mock_klient = _lag_mock_klient(mock_samling)
        mock_modell = MagicMock()
        mock_modell.encode.return_value = [[0.1, 0.2, 0.3]]

        with (
            patch("rag.gjenfinning.chromadb.PersistentClient", return_value=mock_klient),
            patch("rag.gjenfinning.SentenceTransformer", return_value=mock_modell),
        ):
            from rag.gjenfinning import søk_chromadb
            søk_chromadb("KGHM finansielle resultater", n_resultater=3, bedrift="KGHM")

        kall = mock_samling.query.call_args
        assert kall.kwargs.get("where") == {"bedrift": "KGHM"}

    def test_søk_med_delvis_bedriftsnavn_bruker_lagret_navn(self):
        """«Prysmian» matcher «Prysmian Group» i ChromaDB via fuzzy navnmatch."""
        mock_samling = _lag_mock_samling(
            ["[Prysmian Group] Kontantstrøm fra drift."],
            bedrifter=["Prysmian Group", "KGHM"],
        )
        mock_klient = _lag_mock_klient(mock_samling)
        mock_modell = MagicMock()
        mock_modell.encode.return_value = [[0.1, 0.2, 0.3]]

        with (
            patch("rag.gjenfinning.chromadb.PersistentClient", return_value=mock_klient),
            patch("rag.gjenfinning.SentenceTransformer", return_value=mock_modell),
        ):
            from rag.gjenfinning import søk_chromadb
            søk_chromadb("Prysmian finansielle resultater", n_resultater=3, bedrift="Prysmian")

        kall = mock_samling.query.call_args
        assert kall.kwargs.get("where") == {"bedrift": "Prysmian Group"}

    def test_søk_uten_bedrift_sender_ikke_where_filter(self):
        """søk_chromadb sender ikke where-filter når bedrift er None."""
        mock_samling = _lag_mock_samling(["Generisk chunk."])
        mock_klient = _lag_mock_klient(mock_samling)
        mock_modell = MagicMock()
        mock_modell.encode.return_value = [[0.1, 0.2, 0.3]]

        with (
            patch("rag.gjenfinning.chromadb.PersistentClient", return_value=mock_klient),
            patch("rag.gjenfinning.SentenceTransformer", return_value=mock_modell),
        ):
            from rag.gjenfinning import søk_chromadb
            søk_chromadb("generisk query", n_resultater=3)

        kall = mock_samling.query.call_args
        assert "where" not in kall.kwargs

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


class TestFinnMatchendeBedrift:

    def _samling(self, bedrifter: list[str]):
        mock = MagicMock()
        mock.get.return_value = {"metadatas": [{"bedrift": b} for b in bedrifter]}
        return mock

    def test_eksakt_match(self):
        from rag.gjenfinning import _finn_matchende_bedrift
        assert _finn_matchende_bedrift(self._samling(["KGHM", "EDP"]), "KGHM") == "KGHM"

    def test_delvis_match_input_er_del_av_db_navn(self):
        """«Prysmian» → «Prysmian Group»"""
        from rag.gjenfinning import _finn_matchende_bedrift
        assert _finn_matchende_bedrift(self._samling(["Prysmian Group"]), "Prysmian") == "Prysmian Group"

    def test_delvis_match_tuanche(self):
        """«TuanChe» → «TuanChe Limited»"""
        from rag.gjenfinning import _finn_matchende_bedrift
        assert _finn_matchende_bedrift(self._samling(["TuanChe Limited"]), "TuanChe") == "TuanChe Limited"

    def test_delvis_match_teamviewer(self):
        """«TeamViewer» → «TeamViewer AG»"""
        from rag.gjenfinning import _finn_matchende_bedrift
        assert _finn_matchende_bedrift(self._samling(["TeamViewer AG"]), "TeamViewer") == "TeamViewer AG"

    def test_ingen_match_returnerer_none(self):
        from rag.gjenfinning import _finn_matchende_bedrift
        assert _finn_matchende_bedrift(self._samling(["EDP", "KGHM"]), "Microsoft") is None
