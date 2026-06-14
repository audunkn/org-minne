"""
Genererer LLM-forklaring på anomalier med RAG-kontekst.
"""
from __future__ import annotations

from fastapi import HTTPException
from rag.gjenfinning import søk_chromadb
from llm.klient import lag_llm_klient


_INGEN_KONTEKST_SVAR = (
    "Analyse: Ingen transkripsjon tilgjengelig for «{bedrift}». "
    "Anomalien kan ikke forklares uten kildegrunnlag.\n\nSitater:"
)

_PROMPT_MAL = """\
Du er finansanalytiker. Analyser anomalien nedenfor utelukkende basert på de nummererte utdragene fra selskapets resultatpresentasjon.

Bedrift: {bedrift}
Anomali: {anomali_forklaring}

Utdrag fra resultatpresentasjonen:
{nummererte_chunks}

Instruksjoner:
1. Analyse (2–4 setninger): Forklar anomalien med fakta som er eksplisitt oppgitt i utdragene. Oppgi konkrete tall og begreper direkte fra teksten. Ikke spekuler om forhold som ikke fremgår av utdragene.
2. Sitater: Kopier 1–3 setninger ordrett fra utdragene som belyser anomalien best. Gjør ingen endringer i ordlyden. Utelat Sitater-seksjonen hvis ingen setning i utdragene er direkte relevant.

Svar i dette formatet:
Analyse: [tekst]

Sitater:
• [ordrett kopi fra utdrag]\
"""


def _bygg_rag_query(bedrift: str, anomali_forklaring: str) -> str:
    """
    Lager en semantisk query som matcher transkripsjonstekst.

    Chunks er indeksert med «[Bedrift]»-prefiks, så queryen bruker samme format.
    «univariat: Omsetning=1890.0» → «[EDP] finansielle resultater Omsetning»
    «multivariat»                  → «[EDP] finansielle resultater»
    """
    kolonne = ""
    if "univariat:" in anomali_forklaring:
        del_etter = anomali_forklaring.split(":", 1)[1].strip()
        kolonne = del_etter.split("=")[0].strip()

    deler = [f"[{bedrift}]", "finansielle resultater"]
    if kolonne:
        deler.append(kolonne)
    return " ".join(deler)


def generer_forklaring(bedrift: str, anomali_forklaring: str) -> str:
    """
    Henter RAG-kontekst og kaller LLM for å generere forklaring på anomalien.

    Returnerer ferdigformatert streng:
        Analyse: [tekst]

        Sitater:
        • sitat 1
    """
    query = _bygg_rag_query(bedrift, anomali_forklaring)
    chunks = søk_chromadb(query, n_resultater=5, bedrift=bedrift)

    if not chunks:
        return _INGEN_KONTEKST_SVAR.format(bedrift=bedrift)

    nummererte = "\n".join(f"{i + 1}. {chunk}" for i, chunk in enumerate(chunks))
    prompt = _PROMPT_MAL.format(
        bedrift=bedrift,
        anomali_forklaring=anomali_forklaring,
        nummererte_chunks=nummererte,
    )

    klient = lag_llm_klient()

    import os
    leverandør = os.getenv("LLM_LEVERANDØR", "openai").lower()

    try:
        if leverandør == "openai":
            import openai as _openai
            modell = os.getenv("LLM_MODELL", "gpt-4o-mini")
            svar = klient.chat.completions.create(
                model=modell,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
            )
            return svar.choices[0].message.content.strip()

        if leverandør == "mistral":
            modell = os.getenv("LLM_MODELL", "mistral-small-latest")
            svar = klient.chat.complete(
                model=modell,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
            )
            return svar.choices[0].message.content.strip()

        raise ValueError(f"Ukjent LLM_LEVERANDØR ved generering: '{leverandør}'")

    except HTTPException:
        raise
    except Exception as e:
        feilmelding = str(e)
        if "insufficient_quota" in feilmelding or "RateLimitError" in type(e).__name__:
            raise HTTPException(status_code=502, detail="OpenAI: kvote overskredet. Legg til credits på platform.openai.com.")
        if "AuthenticationError" in type(e).__name__ or "authentication" in feilmelding.lower():
            raise HTTPException(status_code=502, detail="OpenAI: ugyldig API-nøkkel.")
        raise HTTPException(status_code=502, detail=f"LLM-feil: {feilmelding}")
