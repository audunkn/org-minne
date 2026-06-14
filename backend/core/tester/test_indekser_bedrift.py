"""
Tester for ekstraksjon av bedriftsnavn, chunk-prefiks og metadata i indekser.py.
"""
import sys
import os
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ---------------------------------------------------------------------------
# Hjelpere
# ---------------------------------------------------------------------------

def _lag_mock_llm_klient(svar: str):
    """Returnerer mock LLM-klient (OpenAI-stil) som svarer med gitt tekst."""
    mock_klient = MagicMock()
    mock_valg = MagicMock()
    mock_valg.message.content = svar
    mock_klient.chat.completions.create.return_value = MagicMock(choices=[mock_valg])
    return mock_klient


# ---------------------------------------------------------------------------
# Tester — ekstraher_bedriftsnavn
# ---------------------------------------------------------------------------

class TestEkstraherBedriftsnavn:

    def test_ekstraher_bedriftsnavn_returnerer_navn(self):
        """LLM svarer 'EDP' → ekstraher_bedriftsnavn returnerer 'EDP'."""
        mock_klient = _lag_mock_llm_klient("EDP")

        with (
            patch("llm.klient.lag_llm_klient", return_value=mock_klient),
            patch.dict(os.environ, {"LLM_LEVERANDØR": "openai", "LLM_MODELL": "gpt-4o-mini"}),
        ):
            from rag.indekser import ekstraher_bedriftsnavn
            resultat = ekstraher_bedriftsnavn("EDP Renovables presenterer resultater for Q1 2025...")

        assert resultat == "EDP"

    def test_ekstraher_bedriftsnavn_feil_gir_ukjent(self):
        """Hvis LLM kaster en feil, returneres 'UKJENT'."""
        mock_klient = MagicMock()
        mock_klient.chat.completions.create.side_effect = RuntimeError("API-feil")

        with (
            patch("llm.klient.lag_llm_klient", return_value=mock_klient),
            patch.dict(os.environ, {"LLM_LEVERANDØR": "openai", "LLM_MODELL": "gpt-4o-mini"}),
        ):
            from rag.indekser import ekstraher_bedriftsnavn
            resultat = ekstraher_bedriftsnavn("Ukjent innhold")

        assert resultat == "UKJENT"

    def test_ekstraher_bedriftsnavn_renser_svar(self):
        """Whitespace og linjeskift i LLM-svar renses bort."""
        mock_klient = _lag_mock_llm_klient("  Hydro\n")

        with (
            patch("llm.klient.lag_llm_klient", return_value=mock_klient),
            patch.dict(os.environ, {"LLM_LEVERANDØR": "openai", "LLM_MODELL": "gpt-4o-mini"}),
        ):
            from rag.indekser import ekstraher_bedriftsnavn
            resultat = ekstraher_bedriftsnavn("Norsk Hydro presenterer...")

        assert resultat == "Hydro"


# ---------------------------------------------------------------------------
# Tester — chunk-prefiks og metadata
# ---------------------------------------------------------------------------

class TestChunkPrefiks:

    def _kjør_indekser_fil_med_mock(self, tekst: str, bedrift: str):
        """Hjelpefunksjon: kjører indekser_fil med mock-samling og -modell."""
        mock_klient_llm = _lag_mock_llm_klient(bedrift)
        mock_samling = MagicMock()
        mock_samling.get.return_value = {"ids": []}
        mock_modell = MagicMock()
        mock_modell.encode.return_value = [[0.1, 0.2]]

        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            fil = Path(tmpdir) / "transcript_NO_1234.txt"
            fil.write_text(tekst, encoding="utf-8")

            with (
                patch("llm.klient.lag_llm_klient", return_value=mock_klient_llm),
                patch.dict(os.environ, {"LLM_LEVERANDØR": "openai", "LLM_MODELL": "gpt-4o-mini"}),
            ):
                from rag.indekser import indekser_fil
                indekser_fil(fil, mock_samling, mock_modell)

        return mock_samling

    def test_chunk_prefiks_inneholder_bedrift(self):
        """Chunk-tekst sendt til ChromaDB starter med '[EDP] '."""
        tekst = "EDP Renovables Q1 2025\n\n" + "x" * 200
        mock_samling = self._kjør_indekser_fil_med_mock(tekst, "EDP")

        kall_args = mock_samling.add.call_args
        dokumenter = kall_args.kwargs.get("documents") or kall_args.args[0]
        assert all(d.startswith("[EDP] ") for d in dokumenter), \
            f"Første dokument: {dokumenter[0][:60]!r}"

    def test_metadata_inneholder_bedrift(self):
        """Metadata for hver chunk inneholder nøkkelen 'bedrift' med korrekt verdi."""
        tekst = "EDP Renovables Q1 2025\n\n" + "x" * 200
        mock_samling = self._kjør_indekser_fil_med_mock(tekst, "EDP")

        kall_args = mock_samling.add.call_args
        metadatas = kall_args.kwargs.get("metadatas") or kall_args.args[2]
        assert all(m.get("bedrift") == "EDP" for m in metadatas), \
            f"Første metadata: {metadatas[0]}"
