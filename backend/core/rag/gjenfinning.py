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


def _finn_matchende_bedrift(samling, bedrift: str) -> str | None:
    """
    Finner det lagrede bedriftsnavnet som best matcher input.

    Prøver i rekkefølge:
    1. Eksakt match                  «KGHM»          → «KGHM»
    2. Case-insensitiv eksakt        «kghm»           → «KGHM»
    3. Input er del av lagret navn   «Prysmian»       → «Prysmian Group»
    4. Lagret navn er del av input   «TeamViewer AG»  → «TeamViewer AG»

    Returnerer None hvis ingen match finnes.
    """
    res = samling.get(include=["metadatas"])
    alle_bedrifter = {m["bedrift"] for m in res["metadatas"] if "bedrift" in m}

    if bedrift in alle_bedrifter:
        return bedrift

    b_lower = bedrift.lower()

    for b in alle_bedrifter:
        if b_lower == b.lower():
            return b

    for b in alle_bedrifter:
        if b_lower in b.lower():
            return b

    for b in alle_bedrifter:
        if b.lower() in b_lower:
            return b

    return None


def hent_transkripsjon(bedrift: str) -> str | None:
    """
    Returnerer innholdet i transkripsjonsfilen for den gitte bedriften.

    Kobler til ChromaDB, løser opp bedriftsnavnet via fuzzy match, henter
    kilde_fil fra metadata og leser filen fra {prosjektrot}/transcripts/.
    Returnerer None hvis bedriften ikke finnes i DB eller filen mangler.
    """
    konfig, rot = _last_konfig()

    db_sti = rot / konfig["vektor_db"]["sti"]
    samling_navn = konfig["vektor_db"]["samling"]
    transkripsjon_mappe = rot / konfig["transkripsjoner"]["mappe"]
    encoding = konfig["transkripsjoner"].get("encoding", "utf-8")

    klient = chromadb.PersistentClient(path=str(db_sti))
    samling = klient.get_or_create_collection(name=samling_navn)

    matchende = _finn_matchende_bedrift(samling, bedrift)
    if not matchende:
        return None

    res = samling.get(where={"bedrift": matchende}, limit=1, include=["metadatas"])
    if not res["ids"] or not res["ids"][0]:
        return None

    kilde_fil = res["metadatas"][0].get("kilde_fil")
    if not kilde_fil:
        return None

    fil_sti = transkripsjon_mappe / kilde_fil
    if not fil_sti.exists():
        return None

    return fil_sti.read_text(encoding=encoding)


def søk_chromadb(
    query: str,
    n_resultater: int = 5,
    bedrift: str | None = None,
) -> list[str]:
    """
    Søker ChromaDB og returnerer de N mest relevante dokumentchunkene som strenger.

    Filtrerer bort chunks med L2-distanse >= score_terskel fra rag_konfig.yaml.
    Hvis bedrift er oppgitt, begrenses søket til chunks med matchende bedrift-metadata.
    Bruker fuzzy navnmatch slik at «Prysmian» treffer «Prysmian Group» i databasen.
    Returnerer tom liste hvis samlingen er tom eller ingen chunks passerer terskelen.
    """
    konfig, rot = _last_konfig()

    db_sti = rot / konfig["vektor_db"]["sti"]
    samling_navn = konfig["vektor_db"]["samling"]
    modell_navn = konfig["embedding"]["modell"]
    enhet = konfig["embedding"]["enhet"]
    score_terskel = konfig.get("søk", {}).get("score_terskel", 1.0)

    klient = chromadb.PersistentClient(path=str(db_sti))
    samling = klient.get_or_create_collection(name=samling_navn)

    modell = SentenceTransformer(modell_navn, device=enhet)
    enc = modell.encode([query])
    embedding = enc.tolist() if hasattr(enc, "tolist") else enc

    søk_kwargs: dict = {"query_embeddings": embedding, "n_results": n_resultater}
    if bedrift:
        matchende = _finn_matchende_bedrift(samling, bedrift)
        if matchende:
            søk_kwargs["where"] = {"bedrift": matchende}

    resultat = samling.query(**søk_kwargs)
    dokumenter = resultat.get("documents", [[]])[0]
    distanser = resultat.get("distances", [[]])[0]

    if not dokumenter:
        return []

    return [
        dok
        for dok, dist in zip(dokumenter, distanser)
        if dist < score_terskel
    ]
