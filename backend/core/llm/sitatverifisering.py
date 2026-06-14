"""
Sitatverifisering: parser, verifiserer og filtrerer LLM-sitater mot transkripsjon.
"""
from __future__ import annotations

import re


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
    2. Normaliser whitespace i både sitat og transkripsjon.
    3. Krev minimum 10 tegn etter normalisering.
    4. Sjekk substring-match (case-sensitiv).
    """
    renset = re.sub(r'^\[[^\]]+\]\s*', '', sitat)
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
    verifiserte = [s for s in sitater if verifiser_sitat(s, transkripsjon)]

    deler = [analyse_del, "", "Sitater:"]
    for s in verifiserte:
        deler.append(f"• {s}")
    return "\n".join(deler)
