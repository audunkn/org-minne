"""
Tester for backend/core/rag/indekser.py
TDD: disse testene skrives FØR implementeringen.

Gruppe 1 — Konfigurasjonslasting
Gruppe 2 — Chunking-logikk
Gruppe 3 — Indekseringslogikk (idempotens, metadata, ID-format)
"""

import os
import sys
import tempfile
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest
import yaml

# Legg til prosjektroten i sys.path slik at vi kan importere rag-modulen
PROSJEKTROT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROSJEKTROT))

from rag.indekser import chunk_tekst, last_konfig, finn_konfig_sti


# ---------------------------------------------------------------------------
# Gruppe 1 — Konfigurasjonslasting
# ---------------------------------------------------------------------------

class TestKonfigurasjon:
    def test_last_konfig_returnerer_dict(self, tmp_path):
        konfig_sti = tmp_path / "rag_konfig.yaml"
        konfig_sti.write_text(
            textwrap.dedent("""\
            transkripsjoner:
              mappe: transcripts
              mønster: "*.txt"
              encoding: utf-8
            chunking:
              chunk_størrelse: 800
              chunk_overlapp: 150
              separator: "\\n\\n"
            embedding:
              modell: paraphrase-multilingual-MiniLM-L12-v2
              enhet: cpu
            vektor_db:
              sti: vector_db
              samling: transkripsjoner
            """),
            encoding="utf-8",
        )
        konfig = last_konfig(konfig_sti)
        assert konfig["transkripsjoner"]["mappe"] == "transcripts"
        assert konfig["chunking"]["chunk_størrelse"] == 800
        assert konfig["chunking"]["chunk_overlapp"] == 150
        assert konfig["embedding"]["modell"] == "paraphrase-multilingual-MiniLM-L12-v2"
        assert konfig["vektor_db"]["samling"] == "transkripsjoner"

    def test_last_konfig_manglende_nokkel_gir_keyerror(self, tmp_path):
        konfig_sti = tmp_path / "rag_konfig.yaml"
        konfig_sti.write_text("transkripsjoner:\n  mappe: transcripts\n", encoding="utf-8")
        konfig = last_konfig(konfig_sti)
        with pytest.raises(KeyError):
            _ = konfig["chunking"]["chunk_størrelse"]

    def test_finn_konfig_sti_finner_yaml(self, tmp_path):
        konfig_sti = tmp_path / "rag_konfig.yaml"
        konfig_sti.write_text("vektor_db:\n  sti: vector_db\n", encoding="utf-8")
        funnet = finn_konfig_sti(tmp_path)
        assert funnet == konfig_sti

    def test_finn_konfig_sti_traverserer_opp(self, tmp_path):
        sub = tmp_path / "backend" / "core" / "rag"
        sub.mkdir(parents=True)
        konfig_sti = tmp_path / "rag_konfig.yaml"
        konfig_sti.write_text("vektor_db:\n  sti: vector_db\n", encoding="utf-8")
        funnet = finn_konfig_sti(sub)
        assert funnet == konfig_sti

    def test_finn_konfig_sti_gir_feil_hvis_ikke_funnet(self, tmp_path):
        sub = tmp_path / "dypere" / "mappe"
        sub.mkdir(parents=True)
        with pytest.raises(FileNotFoundError):
            finn_konfig_sti(sub)


# ---------------------------------------------------------------------------
# Gruppe 2 — Chunking-logikk
# ---------------------------------------------------------------------------

class TestChunking:
    def test_kort_tekst_gir_en_chunk(self):
        tekst = "Dette er en kort tekst."
        chunks = chunk_tekst(tekst, chunk_størrelse=800, overlapp=150)
        assert len(chunks) == 1
        assert chunks[0][0] == tekst
        assert chunks[0][1] == 0  # tegnstart

    def test_lang_tekst_gir_flere_chunks(self):
        avsnitt = "A" * 200
        tekst = "\n\n".join([avsnitt] * 6)  # 6 avsnitt à 200 tegn
        chunks = chunk_tekst(tekst, chunk_størrelse=400, overlapp=50)
        assert len(chunks) > 1

    def test_chunk_storrelse_respekteres(self):
        tekst = "X" * 2000
        chunks = chunk_tekst(tekst, chunk_størrelse=500, overlapp=0)
        for chunk_txt, _ in chunks:
            assert len(chunk_txt) <= 500

    def test_overlapp_er_korrekt(self):
        # Bygg tekst der vi kan forutsi overlapp
        del1 = "A" * 300
        del2 = "B" * 300
        tekst = del1 + del2
        chunks = chunk_tekst(tekst, chunk_størrelse=400, overlapp=100)
        if len(chunks) >= 2:
            # Slutten av chunk 1 og starten av chunk 2 skal overlappe
            slutt_chunk1 = chunks[0][0][-100:]
            start_chunk2 = chunks[1][0][:100]
            assert slutt_chunk1 == start_chunk2

    def test_tegnstart_er_korrekt(self):
        tekst = "12345\n\n67890\n\nABCDE"
        chunks = chunk_tekst(tekst, chunk_størrelse=10, overlapp=0)
        for chunk_txt, tegnstart in chunks:
            assert tekst[tegnstart : tegnstart + len(chunk_txt)] == chunk_txt

    def test_separator_brukes_fremfor_midtveis_splitt(self):
        # Tekst med tydelig dobbelt-linjeskift-grense
        del1 = "Første avsnitt " * 20   # ~300 tegn
        del2 = "Andre avsnitt " * 20    # ~280 tegn
        tekst = del1.rstrip() + "\n\n" + del2.rstrip()
        chunks = chunk_tekst(tekst, chunk_størrelse=350, overlapp=0)
        # Første chunk skal ende ved dobbelt-linjeskift
        assert chunks[0][0].rstrip() == del1.rstrip()

    def test_tom_tekst_gir_ingen_chunks(self):
        chunks = chunk_tekst("", chunk_størrelse=800, overlapp=150)
        assert chunks == []


# ---------------------------------------------------------------------------
# Gruppe 3 — Indekseringslogikk
# ---------------------------------------------------------------------------

class TestIndekseringslogikk:
    """
    Tester indekseringslogikken isolert med mock-ChromaDB og mock-SentenceTransformer.
    """

    def _lag_mock_samling(self, eksisterende_filer=None):
        """Returnerer en mock ChromaDB-samling."""
        mock_col = MagicMock()
        eksisterende = eksisterende_filer or []

        def get_side_effect(where=None, limit=1):
            if where and where.get("kilde_fil") in eksisterende:
                return {"ids": [["dummy_id"]], "documents": [["dummy"]]}
            return {"ids": [[]], "documents": [[]]}

        mock_col.get.side_effect = get_side_effect
        mock_col.add = MagicMock()
        return mock_col

    def test_allerede_indeksert_fil_hoppes_over(self, tmp_path):
        from rag.indekser import indekser_fil

        txt_fil = tmp_path / "rapport.txt"
        txt_fil.write_text("Kort tekst for testing.", encoding="utf-8")

        mock_col = self._lag_mock_samling(eksisterende_filer=["rapport.txt"])
        mock_modell = MagicMock()

        resultat = indekser_fil(txt_fil, mock_col, mock_modell, chunk_størrelse=800, overlapp=150)

        assert resultat == 0  # ingen nye chunks lagt til
        mock_col.add.assert_not_called()

    def test_ny_fil_indekseres_og_returnerer_antall_chunks(self, tmp_path):
        from rag.indekser import indekser_fil

        tekst = "Avsnitt én.\n\nAvsnitt to.\n\nAvsnitt tre.\n\nAvsnitt fire."
        txt_fil = tmp_path / "ny_rapport.txt"
        txt_fil.write_text(tekst, encoding="utf-8")

        mock_col = self._lag_mock_samling(eksisterende_filer=[])
        mock_modell = MagicMock()
        mock_modell.encode.return_value = [[0.1, 0.2, 0.3]]

        resultat = indekser_fil(txt_fil, mock_col, mock_modell, chunk_størrelse=800, overlapp=150)

        assert resultat >= 1
        mock_col.add.assert_called_once()

    def test_metadata_inneholder_pakrevde_felt(self, tmp_path):
        from rag.indekser import indekser_fil

        txt_fil = tmp_path / "meta_test.txt"
        txt_fil.write_text("Tekst for metadatatest.", encoding="utf-8")

        mock_col = self._lag_mock_samling(eksisterende_filer=[])
        mock_modell = MagicMock()
        mock_modell.encode.return_value = [[0.1, 0.2]]

        indekser_fil(txt_fil, mock_col, mock_modell, chunk_størrelse=800, overlapp=150)

        _, kwargs = mock_col.add.call_args
        metadatas = kwargs.get("metadatas") or mock_col.add.call_args[0][2]
        for meta in metadatas:
            assert "kilde_fil" in meta
            assert "chunk_nr" in meta
            assert "total_chunks" in meta
            assert "tegnstart" in meta

    def test_id_format_er_filnavn_og_chunk_nr(self, tmp_path):
        from rag.indekser import indekser_fil

        txt_fil = tmp_path / "id_test.txt"
        txt_fil.write_text("Kort tekst.", encoding="utf-8")

        mock_col = self._lag_mock_samling(eksisterende_filer=[])
        mock_modell = MagicMock()
        mock_modell.encode.return_value = [[0.1, 0.2]]

        indekser_fil(txt_fil, mock_col, mock_modell, chunk_størrelse=800, overlapp=150)

        _, kwargs = mock_col.add.call_args
        ids = kwargs.get("ids") or mock_col.add.call_args[0][3]
        assert ids[0] == "id_test.txt_0"

    def test_kilde_fil_metadata_er_filnavn(self, tmp_path):
        from rag.indekser import indekser_fil

        txt_fil = tmp_path / "kilde_test.txt"
        txt_fil.write_text("Tekst.", encoding="utf-8")

        mock_col = self._lag_mock_samling(eksisterende_filer=[])
        mock_modell = MagicMock()
        mock_modell.encode.return_value = [[0.1]]

        indekser_fil(txt_fil, mock_col, mock_modell, chunk_størrelse=800, overlapp=150)

        _, kwargs = mock_col.add.call_args
        metadatas = kwargs.get("metadatas") or mock_col.add.call_args[0][2]
        assert metadatas[0]["kilde_fil"] == "kilde_test.txt"
