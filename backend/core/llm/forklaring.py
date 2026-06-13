"""
Genererer LLM-forklaring på anomalier med RAG-kontekst.
"""
from __future__ import annotations

from rag.gjenfinning import søk_chromadb
from llm.klient import lag_llm_klient


_PROMPT_MAL = """\
Du er finansanalytiker. Bedriften «{bedrift}» viser følgende anomali: {anomali_forklaring}.

{rag_seksjon}\
Forklar anomalien på norsk basert på utdragene. Velg 1-3 illustrerende sitater.
Svar i dette formatet:
Analyse: [forklaringstekst]

Sitater:
• [sitat 1]
• [sitat 2]\
"""

_RAG_SEKSJON_MAL = """\
Relevante utdrag fra resultatpresentasjoner:
{nummererte_chunks}

"""


def generer_forklaring(bedrift: str, anomali_forklaring: str) -> str:
    """
    Henter RAG-kontekst og kaller LLM for å generere forklaring på anomalien.

    Returnerer ferdigformatert streng:
        Analyse: [tekst]

        Sitater:
        • sitat 1
    """
    chunks = søk_chromadb(f"{bedrift} {anomali_forklaring}", n_resultater=5)

    if chunks:
        nummererte = "\n".join(f"{i + 1}. {chunk}" for i, chunk in enumerate(chunks))
        rag_seksjon = _RAG_SEKSJON_MAL.format(nummererte_chunks=nummererte)
    else:
        rag_seksjon = ""

    prompt = _PROMPT_MAL.format(
        bedrift=bedrift,
        anomali_forklaring=anomali_forklaring,
        rag_seksjon=rag_seksjon,
    )

    klient = lag_llm_klient()

    import os
    leverandør = os.getenv("LLM_LEVERANDØR", "openai").lower()

    if leverandør == "openai":
        svar = klient.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        return svar.choices[0].message.content.strip()

    if leverandør == "mistral":
        svar = klient.chat.complete(
            model="mistral-small-latest",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        return svar.choices[0].message.content.strip()

    raise ValueError(f"Ukjent LLM_LEVERANDØR ved generering: '{leverandør}'")
