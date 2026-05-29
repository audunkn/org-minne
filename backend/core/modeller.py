from pydantic import BaseModel, Field
from typing import Any
import uuid


class Referanse(BaseModel):
    tabell: str | None = None
    sti: str | None = None
    view: str | None = None


class AnalyseForespørsel(BaseModel):
    kilde: str = Field(..., examples=["excel_tabell", "lokal_fil", "fabric"])
    referanse: Referanse | None = None
    inline_data: list[dict[str, Any]] = Field(default_factory=list)


class LoggSteg(BaseModel):
    steg: int
    tid: str
    melding: str


class AnalyseSvar(BaseModel):
    analyse_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    avvik: list[dict[str, Any]] = Field(default_factory=list)
    logg: list[LoggSteg] = Field(default_factory=list)


class HealthSvar(BaseModel):
    status: str
    version: str
    timestamp: str
