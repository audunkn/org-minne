import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from modeller import AnalyseForespørsel, AnalyseSvar, HealthSvar, LoggSteg

load_dotenv()

PORT = int(os.getenv("PORT", "8000"))
TOKEN = os.getenv("TOKEN", "")
VERSION = os.getenv("VERSION", "0.1.0")


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"[org-minne] backend v{VERSION} startet på port {PORT}")
    yield


app = FastAPI(
    title="Det Organisatoriske Minnet — Backend",
    version=VERSION,
    description="Lokal agent for anomalianalyse og RAG mot bedriftsdokumenter.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://localhost:3000",
        "https://localhost",
        "https://appsforoffice.microsoft.com",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def token_middleware(request: Request, call_next):
    if request.method == "OPTIONS" or request.url.path in ("/docs", "/openapi.json", "/redoc"):
        return await call_next(request)

    auth = request.headers.get("Authorization", "")
    if not TOKEN or auth != f"Bearer {TOKEN}":
        return JSONResponse(status_code=401, content={"detail": "Ugyldig eller manglende token."})

    return await call_next(request)


@app.get("/health", response_model=HealthSvar, tags=["Status"])
async def health():
    return HealthSvar(
        status="ok",
        version=VERSION,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.post("/v1/analyse", response_model=AnalyseSvar, tags=["Analyse"])
async def analyse(forespørsel: AnalyseForespørsel):
    nå = datetime.now(timezone.utc).isoformat()
    logg = [
        LoggSteg(steg=1, tid=nå, melding=f"Forespørsel mottatt. Kilde: {forespørsel.kilde}."),
        LoggSteg(steg=2, tid=nå, melding="Datahenting ikke implementert i Fase 1 (mock-modus)."),
        LoggSteg(steg=3, tid=nå, melding="Analyse fullført. Ingen avvik funnet (mock-respons)."),
    ]
    return AnalyseSvar(avvik=[], logg=logg)
