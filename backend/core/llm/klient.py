"""
LLM-klientfabrikk. Leverandør styres via LLM_LEVERANDØR i .env.
"""
import os


def lag_llm_klient():
    """
    Returnerer initialisert LLM-klient basert på LLM_LEVERANDØR.

    Støttede verdier: 'openai' (standard), 'mistral'.
    Reiser ValueError ved ukjent leverandør.
    """
    leverandør = os.getenv("LLM_LEVERANDØR", "openai").lower()

    if leverandør == "openai":
        import openai
        return openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    if leverandør == "mistral":
        from mistralai.client import Mistral
        return Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

    raise ValueError(f"Ukjent LLM_LEVERANDØR: '{leverandør}'. Støttede verdier: 'openai', 'mistral'.")
