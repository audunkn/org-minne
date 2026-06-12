# Plan — RAG-indeksering av transkripsjoner

## Gruppe 1 — Konfigurasjon og avhengigheter

- [x] Opprett `rag_konfig.yaml` i prosjektrot
- [x] Legg til `chromadb==0.6.3`, `sentence-transformers==3.3.1`, `PyYAML==6.0.2` i `requirements.txt`
- [x] Legg til `vector_db/` i `.gitignore`

### Tester (gruppe 1)

- Test at `rag_konfig.yaml` leses korrekt og alle nøkler er tilgjengelige
- Test at ukjent nøkkel gir `KeyError`

## Gruppe 2 — Chunking-logikk

- [x] Implementer `chunk_tekst(tekst, chunk_størrelse, overlapp, separatorer)` i `indekser.py`
- [x] Rekursiv splitt på `["\n\n", "\n", " "]`
- [x] Returnerer liste av `(chunk_tekst, tegnstart)`-tupler

### Tester (gruppe 2)

- Test at chunking av kort tekst gir én chunk
- Test at lang tekst gir flere chunks med korrekt overlapp
- Test at tegnstart er korrekt for hver chunk
- Test at separatorer respekteres (splitter på `\n\n` fremfor `\n`)

## Gruppe 3 — Indekseringslogikk

- [x] Implementer `main()` i `indekser.py`
- [x] ChromaDB PersistentClient-initialisering
- [x] Hent-eller-opprett samling
- [x] Fil-for-fil prosessering med idempotens-sjekk
- [x] Logging av fremgang

### Tester (gruppe 3)

- Test at allerede-indeksert fil hoppes over (idempotens)
- Test at ny fil indekseres og gir korrekt antall chunks i samlingen
- Test at metadata (kilde_fil, chunk_nr, total_chunks, tegnstart) er korrekt
- Test at ID-format er `{filnavn}_{chunk_nr}`

## Kjøring

```bash
cd backend/core
python rag/indekser.py
```
