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

async function kjørAnomalideteksjon(): Promise<void> {
  const knapp = document.getElementById("btnAnomali") as HTMLButtonElement;
  knapp.disabled = true;
  skjulResultat();
  visStatus("Leser data fra arket…", "laster");

  const token = localStorage.getItem(TOKEN_KEY) ?? "";

  let inline_data: Record<string, unknown>[] = [];
  let startRow = 0;
  let startCol = 0;
  let rowCount = 0;
  let colCount = 0;

  try {
    await Excel.run(async (context) => {
      const sheet = context.workbook.worksheets.getActiveWorksheet();
      const range = sheet.getUsedRange();
      range.load("values, rowCount, columnCount, rowIndex, columnIndex");
      await context.sync();

      startRow = range.rowIndex;
      startCol = range.columnIndex;
      rowCount = range.rowCount;
      colCount = range.columnCount;

      const headers = range.values[0] as string[];
      const dataRows = range.values.slice(1) as unknown[][];
      inline_data = dataRows.map((row) =>
        Object.fromEntries(headers.map((h, i) => [h, row[i]]))
      );
    });
  } catch (err) {
    visStatus("Kunne ikke lese data fra arket.", "feil");
    knapp.disabled = false;
    return;
  }

  if (inline_data.length === 0) {
    visStatus("Arket er tomt eller mangler datarad.", "feil");
    knapp.disabled = false;
    return;
  }

  visStatus(`Kjører anomalideteksjon på ${inline_data.length} rader…`, "laster");

  try {
    const svar = await fetch(`${BACKEND_URL}/v1/analyse`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ kilde: "excel_tabell", inline_data }),
    });

    if (!svar.ok) {
      const detaljer = await svar.text();
      visStatus(`Feil fra backend (HTTP ${svar.status}): ${detaljer}`, "feil");
      return;
    }

    const data = await svar.json();
    const avvik: Array<{ er_anomali: boolean; antall_flagg: number }> = data.avvik;

    if (avvik.length === 0) {
      const siste = data.logg[data.logg.length - 1]?.melding ?? "Ingen avvik beregnet.";
      visResultat(siste);
      return;
    }

    // Skriv resultater tilbake til arket
    await Excel.run(async (context) => {
      const sheet = context.workbook.worksheets.getActiveWorksheet();

      // Headerrad
      const headerRange = sheet.getRangeByIndexes(startRow, startCol + colCount, 1, 2);
      headerRange.values = [["Anomali", "Flagg"]];
      headerRange.format.font.bold = true;

      // Datarad
      const dataRange = sheet.getRangeByIndexes(
        startRow + 1,
        startCol + colCount,
        avvik.length,
        2
      );
      dataRange.values = avvik.map((a) => [
        a.er_anomali ? "Ja" : "Nei",
        `${a.antall_flagg} av 4`,
      ]);

      await context.sync();
    });

    const antallAnomalier = avvik.filter((a) => a.er_anomali).length;
    visResultat(
      `Analyse fullført.\n${antallAnomalier} anomali(er) funnet av ${avvik.length} rader.\nResultater skrevet til arket.`
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
  const btnAnalyser = document.getElementById("btnAnalyser") as HTMLButtonElement;
  btnAnalyser.disabled = false;
  btnAnalyser.addEventListener("click", testTilkobling);

  const btnAnomali = document.getElementById("btnAnomali") as HTMLButtonElement;
  btnAnomali.disabled = false;
  btnAnomali.addEventListener("click", kjørAnomalideteksjon);
});
