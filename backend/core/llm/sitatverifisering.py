"""
Sitatverifisering: parser, verifiserer og filtrerer LLM-sitater mot transkripsjon.
"""
from __future__ import annotations

import logging
import re

log = logging.getLogger(__name__)


def parse_sitater(tekst: str) -> list[str]:
    """
    Trekker ut bullet-sitater fra Sitater-seksjonen i LLM-svar.

    Returnerer liste av sitatstrenger (uten bullet-tegn), eller tom liste.
    """
    if "Sitater:" not in tekst:
        return []

    etter_sitater = tekst.split("Sitater:", 1)[1]
    sitater = []
    for linje in etter_sitater.splitlines():
        stripped = linje.strip()
        if stripped.startswith("•"):
            sitat = stripped[1:].strip()
            if sitat:
                sitater.append(sitat)
    return sitater


def verifiser_sitat(sitat: str, transkripsjon: str) -> bool:
    """
    Returnerer True hvis sitatet finnes (verbatim) i transkripsjonen.

    Prosedyre:
    1. Fjern eventuell [Bedrift]-prefiks.
    2. Strip markdown-formatering (* / _) og anførselstegn fra start/slutt.
    3. Normaliser whitespace i både sitat og transkripsjon.
    4. Krev minimum 10 tegn etter normalisering.
    5. Sjekk substring-match (case-sensitiv).
    """
    renset = re.sub(r'^\[[^\]]+\]\s*', '', sitat)
    # Strip markdown (*/_) og anførselstegn (rett, typografisk, vinklet) fra begge ender
    renset = re.sub(r'^[\*_\"\u201c\u201d\u00ab\u00bb]+|[\*_\"\u201c\u201d\u00ab\u00bb]+$', '', renset).strip()
    normalisert_sitat = ' '.join(renset.split())
    if len(normalisert_sitat) < 10:
        return False
    normalisert_transkripsjon = ' '.join(transkripsjon.split())
    return normalisert_sitat in normalisert_transkripsjon


def filtrer_sitater(tekst: str, transkripsjon: str) -> str:
    """
    Beholder kun sitater som verifiseres mot transkripsjonen.

    Bevarer Analyse-seksjonen uendret. Sitater-linjen settes alltid med.
    Returnerer tekst uendret hvis ingen Sitater-seksjon finnes.
    """
    if "Sitater:" not in tekst:
        return tekst

    analyse_del = tekst.split("Sitater:", 1)[0].rstrip()
    sitater = parse_sitater(tekst)

    norm_transkripsjon = ' '.join(transkripsjon.split())
    log.info("[sitatverifisering] transkripsjon lengde=%d tegn", len(norm_transkripsjon))

    verifiserte = []
    for s in sitater:
        renset = re.sub(r'^\[[^\]]+\]\s*', '', s)
        renset = re.sub(r'^[\*_\"\u201c\u201d\u00ab\u00bb]+|[\*_\"\u201c\u201d\u00ab\u00bb]+$', '', renset).strip()
        norm = ' '.join(renset.split())
        treff = len(norm) >= 10 and norm in norm_transkripsjon
        log.info("[sitatverifisering] sitat=%r treff=%s", norm[:80], treff)
        if treff:
            verifiserte.append(s)

    deler = [analyse_del, "", "Sitater:"]
    for s in verifiserte:
        deler.append(f"• {s}")
    return "\n".join(deler)
