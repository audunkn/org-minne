/// <reference types="office-js" />

const BACKEND_URL = "http://localhost:8000";
// Token leses fra localStorage slik at den kan settes av administrator ved installasjon.
// I utvikling: localStorage.setItem("org_minne_token", "<token>") i konsollen.
const TOKEN_KEY = "org_minne_token";

function visStatus(melding: string, type: "laster" | "feil"): void {
  const el = document.getElementById("status") as HTMLDivElement;
  el.textContent = melding;
  el.className = type;
  el.style.display = "block";
}

function skjulStatus(): void {
  const el = document.getElementById("status") as HTMLDivElement;
  el.style.display = "none";
}

function visResultat(innhold: string): void {
  skjulStatus();
  const wrapper = document.getElementById("resultat") as HTMLDivElement;
  const innholdEl = document.getElementById("resultatInnhold") as HTMLDivElement;
  innholdEl.textContent = innhold;
  wrapper.style.display = "block";
}

function skjulResultat(): void {
  const el = document.getElementById("resultat") as HTMLDivElement;
  el.style.display = "none";
}

async function testTilkobling(): Promise<void> {
  const knapp = document.getElementById("btnAnalyser") as HTMLButtonElement;
  knapp.disabled = true;
  skjulResultat();
  visStatus("Kobler til backend…", "laster");

  const token = localStorage.getItem(TOKEN_KEY) ?? "";

  try {
    const svar = await fetch(`${BACKEND_URL}/health`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!svar.ok) {
      const detaljer = await svar.text();
      visStatus(`Feil fra backend (HTTP ${svar.status}): ${detaljer}`, "feil");
      return;
    }

    const data = await svar.json();
    visResultat(
      `Status: ${data.status}\nVersjon: ${data.version}\nTidsstempel: ${data.timestamp}`
    );
  } catch (err) {
    visStatus(
      "Kunne ikke nå backend. Sjekk at agent.exe kjører på localhost:8000.",
      "feil"
    );
  } finally {
    knapp.disabled = false;
  }
}

Office.onReady(() => {
  const knapp = document.getElementById("btnAnalyser") as HTMLButtonElement;
  knapp.disabled = false;
  knapp.addEventListener("click", testTilkobling);
});
