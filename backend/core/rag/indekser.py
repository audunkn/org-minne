"""
RAG-indeksering av norske resultatpresentasjoner.

Bruk:
    cd backend/core
    python rag/indekser.py

    eller fra prosjektrot:
    python backend/core/rag/indekser.py

Scriptet er idempotent: filer som allerede er indeksert hoppes over.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    import chromadb
    from sentence_transformers import SentenceTransformer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Konfigurasjon
# ---------------------------------------------------------------------------

def finn_konfig_sti(startmappe: Path) -> Path:
    """Traverserer opp fra startmappe til rot, returnerer første rag_konfig.yaml."""
    mappe = startmappe.resolve()
    while True:
        kandidat = mappe / "rag_konfig.yaml"
        if kandidat.exists():
            return kandidat
        forelder = mappe.parent
        if forelder == mappe:
            raise FileNotFoundError(
                "Fant ikke rag_konfig.yaml i noen overordnet mappe fra "
                f"{startmappe.resolve()}"
            )
        mappe = forelder


def last_konfig(sti: Path) -> dict:
    """Leser og returnerer rag_konfig.yaml som dict."""
    with open(sti, encoding="utf-8") as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

def chunk_tekst(
    tekst: str,
    chunk_størrelse: int = 800,
    overlapp: int = 150,
    separatorer: list[str] | None = None,
) -> list[tuple[str, int]]:
    """
    Deler tekst i overlappende chunks.

    Returnerer liste av (chunk_tekst, tegnstart)-tupler der tegnstart er
    posisjonen i originalteksten der chunken begynner.
    Splitter rekursivt på separatorer; faller tilbake på hardkut.
    """
    if not tekst:
        return []

    if separatorer is None:
        separatorer = ["\n\n", "\n", " "]

    chunks: list[tuple[str, int]] = []
    _chunk_rekursivt(tekst, 0, chunk_størrelse, overlapp, separatorer, chunks)
    return chunks


def _split_med_posisjon(tekst: str, sep: str) -> list[tuple[str, int]]:
    """Splitter tekst på sep og returnerer (del, startposisjon)-tupler."""
    deler: list[tuple[str, int]] = []
    pos = 0
    while pos <= len(tekst):
        idx = tekst.find(sep, pos)
        if idx == -1:
            if pos < len(tekst):
                deler.append((tekst[pos:], pos))
            break
        deler.append((tekst[pos:idx], pos))
        pos = idx + len(sep)
    return deler


def _chunk_rekursivt(
    tekst: str,
    global_offset: int,
    chunk_størrelse: int,
    overlapp: int,
    separatorer: list[str],
    resultat: list[tuple[str, int]],
) -> None:
    if len(tekst) <= chunk_størrelse:
        if tekst.strip():
            resultat.append((tekst, global_offset))
        return

    for sep in separatorer:
        deler = _split_med_posisjon(tekst, sep)
        if len(deler) == 1:
            continue  # Separatoren finnes ikke

        # Bygg chunks ved å akkumulere deler
        pågående: list[tuple[str, int]] = []  # (del_tekst, rel_pos)
        pågående_len = 0

        for del_tekst, rel_pos in deler:
            sep_len = len(sep) if pågående else 0
            tillegg = sep_len + len(del_tekst)

            if pågående_len + tillegg <= chunk_størrelse:
                pågående.append((del_tekst, rel_pos))
                pågående_len += tillegg
            else:
                if pågående:
                    # Lagre gjeldende chunk
                    chunk_str = sep.join(d[0] for d in pågående)
                    chunk_start = global_offset + pågående[0][1]
                    resultat.append((chunk_str, chunk_start))

                    # Bygg overlapp fra slutten av pågående
                    if overlapp > 0:
                        overlap_deler: list[tuple[str, int]] = []
                        overlap_len = 0
                        for d in reversed(pågående):
                            ekstra = len(d[0]) + (len(sep) if overlap_deler else 0)
                            if overlap_len + ekstra <= overlapp:
                                overlap_deler.insert(0, d)
                                overlap_len += ekstra
                            else:
                                break
                        pågående = overlap_deler + [(del_tekst, rel_pos)]
                        pågående_len = len(sep.join(d[0] for d in pågående))
                    else:
                        pågående = [(del_tekst, rel_pos)]
                        pågående_len = len(del_tekst)
                else:
                    # Enkeltdel er for stor; rekursiv splitt med neste separator
                    neste_seps = separatorer[separatorer.index(sep) + 1:]
                    if neste_seps:
                        _chunk_rekursivt(
                            del_tekst,
                            global_offset + rel_pos,
                            chunk_størrelse,
                            overlapp,
                            neste_seps,
                            resultat,
                        )
                    else:
                        # Hardkut
                        p = 0
                        while p < len(del_tekst):
                            resultat.append((
                                del_tekst[p: p + chunk_størrelse],
                                global_offset + rel_pos + p,
                            ))
                            p += chunk_størrelse - overlapp

        if pågående:
            chunk_str = sep.join(d[0] for d in pågående)
            chunk_start = global_offset + pågående[0][1]
            resultat.append((chunk_str, chunk_start))
        return

    # Ingen separator fungerte — hardkut
    pos = 0
    while pos < len(tekst):
        resultat.append((tekst[pos: pos + chunk_størrelse], global_offset + pos))
        pos += chunk_størrelse - overlapp


# ---------------------------------------------------------------------------
# Indeksering av én fil
# ---------------------------------------------------------------------------

def indekser_fil(
    fil_sti: Path,
    samling,
    modell,
    chunk_størrelse: int = 800,
    overlapp: int = 150,
    encoding: str = "utf-8",
) -> int:
    """
    Indekserer én fil i ChromaDB-samlingen.

    Returnerer antall nye chunks lagt til (0 hvis filen allerede er indeksert).
    """
    filnavn = fil_sti.name

    eksisterende = samling.get(where={"kilde_fil": filnavn}, limit=1)
    if eksisterende["ids"] and eksisterende["ids"][0]:
        log.info("  allerede indeksert: %s", filnavn)
        return 0

    tekst = fil_sti.read_text(encoding=encoding)
    chunk_liste = chunk_tekst(tekst, chunk_størrelse=chunk_størrelse, overlapp=overlapp)

    if not chunk_liste:
        log.warning("  ingen chunks generert for: %s", filnavn)
        return 0

    total = len(chunk_liste)
    chunks_tekst = [c[0] for c in chunk_liste]
    embeddings = modell.encode(chunks_tekst, show_progress_bar=False)

    metadatas = [
        {
            "kilde_fil": filnavn,
            "chunk_nr": i,
            "total_chunks": total,
            "tegnstart": chunk_liste[i][1],
        }
        for i in range(total)
    ]
    ids = [f"{filnavn}_{i}" for i in range(total)]

    samling.add(
        documents=chunks_tekst,
        embeddings=embeddings.tolist() if hasattr(embeddings, "tolist") else embeddings,
        metadatas=metadatas,
        ids=ids,
    )
    return total


# ---------------------------------------------------------------------------
# Hovedfunksjon
# ---------------------------------------------------------------------------

def main() -> None:
    skript_mappe = Path(__file__).resolve().parent
    konfig_sti = finn_konfig_sti(skript_mappe)
    log.info("Laster konfig fra: %s", konfig_sti)
    konfig = last_konfig(konfig_sti)

    # Avhengigheter importeres her for å holde dem utenfor testene
    import chromadb
    from sentence_transformers import SentenceTransformer

    # Prosjektrot = mappe der rag_konfig.yaml ligger
    prosjektrot = konfig_sti.parent

    transkripsjon_mappe = prosjektrot / konfig["transkripsjoner"]["mappe"]
    monster = konfig["transkripsjoner"]["mønster"]
    encoding = konfig["transkripsjoner"]["encoding"]
    chunk_størrelse = konfig["chunking"]["chunk_størrelse"]
    overlapp = konfig["chunking"]["chunk_overlapp"]
    db_sti = prosjektrot / konfig["vektor_db"]["sti"]
    samling_navn = konfig["vektor_db"]["samling"]
    modell_navn = konfig["embedding"]["modell"]
    enhet = konfig["embedding"]["enhet"]

    log.info("Initialiserer ChromaDB: %s", db_sti)
    klient = chromadb.PersistentClient(path=str(db_sti))
    samling = klient.get_or_create_collection(name=samling_navn)

    log.info("Laster embedding-modell: %s", modell_navn)
    modell = SentenceTransformer(modell_navn, device=enhet)

    filer = sorted(transkripsjon_mappe.glob(monster))
    if not filer:
        log.warning("Ingen filer funnet i %s med mønster %s", transkripsjon_mappe, monster)
        return

    log.info("Fant %d fil(er) i %s", len(filer), transkripsjon_mappe)

    nye_filer = 0
    totale_chunks = 0

    for fil in filer:
        log.info("Behandler: %s", fil.name)
        antall = indekser_fil(fil, samling, modell, chunk_størrelse, overlapp, encoding)
        if antall > 0:
            nye_filer += 1
            totale_chunks += antall
            log.info("  -> %d chunks lagt til", antall)

    log.info(
        "Ferdig. Nye filer: %d, nye chunks: %d, allerede indeksert: %d",
        nye_filer,
        totale_chunks,
        len(filer) - nye_filer,
    )


if __name__ == "__main__":
    main()
