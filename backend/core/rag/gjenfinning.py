"""
RAG-gjenfinning: søk i ChromaDB etter relevante dokumentchunks.
"""
from __future__ import annotations

from pathlib import Path

import chromadb
import yaml
from sentence_transformers import SentenceTransformer


def _last_konfig() -> dict:
    mappe = Path(__file__).resolve().parent
    while True:
        kandidat = mappe / "rag_konfig.yaml"
        if kandidat.exists():
            with open(kandidat, encoding="utf-8") as f:
                return yaml.safe_load(f), kandidat.parent
        forelder = mappe.parent
        if forelder == mappe:
            raise FileNotFoundError("Fant ikke rag_konfig.yaml")
        mappe = forelder


def søk_chromadb(query: str, n_resultater: int = 5) -> list[str]:
    """
    Søker ChromaDB og returnerer de N mest relevante dokumentchunkene som strenger.

    Returnerer tom liste hvis samlingen er tom eller ikke finnes.
    """
    konfig, rot = _last_konfig()

    db_sti = rot / konfig["vektor_db"]["sti"]
    samling_navn = konfig["vektor_db"]["samling"]
    modell_navn = konfig["embedding"]["modell"]
    enhet = konfig["embedding"]["enhet"]

    klient = chromadb.PersistentClient(path=str(db_sti))
    samling = klient.get_or_create_collection(name=samling_navn)

    modell = SentenceTransformer(modell_navn, device=enhet)
    enc = modell.encode([query])
    embedding = enc.tolist() if hasattr(enc, "tolist") else enc

    resultat = samling.query(query_embeddings=embedding, n_results=n_resultater)
    dokumenter = resultat.get("documents", [[]])[0]
    return dokumenter if dokumenter else []
