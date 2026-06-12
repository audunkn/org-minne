# Requirements — RAG-indeksering av transkripsjoner (Fase 3, del 1)

## Scope

Bygge et Python-skript som indekserer norske resultatpresentasjoner (transkripsjoner) i en lokal ChromaDB-samling for senere RAG-søk.

## Avgrensninger

- Ingen FastAPI-integrasjon i dette steget
- Ingen TypeScript-kobling i dette steget
- Ingen RAG-søk-funksjon i dette steget
- Scriptet kjøres manuelt eller fra CI

## Arkitekturvalg

- ChromaDB PersistentClient for lokal lagring i `vector_db/`
- SentenceTransformer `paraphrase-multilingual-MiniLM-L12-v2` for norsk embedding
- Rekursiv chunking med konfigurerbar størrelse og overlapp
- Idempotent: filer som allerede er indeksert hoppes over ved ny kjøring
- Konfigurasjon i `rag_konfig.yaml` i prosjektroten

## Inndataformat

- 25 .txt-filer i `transcripts/`
- Norsk, konferansesamtaler, ca. 50-100 KB per fil

## Utdata

- ChromaDB-samling `transkripsjoner` i `vector_db/`
- Metadata per chunk: kilde_fil, chunk_nr, total_chunks, tegnstart
