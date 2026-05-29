# Utviklerveiledning — Fase 1

## Forutsetninger

| Verktøy | Versjon | Formål |
|---------|---------|--------|
| Python | 3.11+ | Backend |
| Node.js | 18+ | Frontend build |
| Excel Desktop | 365 | Sidelasting av Add-in |
| WebView2 Runtime | Siste | Kjøres i Excel |

---

## Oppstart — backend

```bash
cd backend/core
cp .env.mal .env
# Rediger .env: sett TOKEN til en tilfeldig streng (f.eks. output fra: python -c "import secrets; print(secrets.token_hex(32))")

pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Verifiser: `curl -H "Authorization: Bearer <TOKEN>" http://localhost:8000/health`

Forventet svar:
```json
{ "status": "ok", "version": "0.1.0", "timestamp": "2026-05-29T..." }
```

---

## Oppstart — frontend (dev-server)

```bash
cd frontend
npm install
npm run dev-server   # HTTPS på localhost:3000
```

---

## Sidelasting av Add-in i Excel Desktop

1. Excel → Fil → Alternativer → Klareringssenter → Innstillinger for klareringssenter
2. Klarerte App-kataloger → legg til sti til `frontend/`-mappen
3. Start Excel på nytt
4. Sett inn → Mine tillegg → velg "AI-Revisor"

---

## Sette token i Task Pane

Åpne nettleserkonsollen i Task Pane (høyreklikk → Inspiser):

```javascript
localStorage.setItem("org_minne_token", "<TOKEN-fra-.env>")
```

Klikk deretter "Test tilkobling" — svaret fra backend vises i panelet.

---

## Kjøre tester

```bash
# Fra repo-roten:
pytest backend/core/tester/ -v
```

---

## Bygge agent.exe

```powershell
# Fra repo-roten (PowerShell):
.\infra\build.ps1
```

Krever at `backend/core/.env` eksisterer (ikke `.env.mal`).

---

## Installere agent.exe med Windows-autostart

1. Kopier `infra/dist/AI-Revisor.exe` til `C:\Users\[navn]\AppData\Local\AI-Revisor\`
2. Opprett snarvei i `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\`
   som peker på `AI-Revisor.exe`
3. Start Windows på nytt og verifiser i Task Manager

---

## Fase 1 — Handshake-test (manuell)

1. Start backend (`uvicorn`)
2. Start frontend dev-server (`npm run dev-server`)
3. Åpne Excel, last Add-in
4. Klikk "Test tilkobling" — versjon og tidsstempel skal vises
5. Stopp backend og klikk igjen — lesbar feilmelding skal vises
