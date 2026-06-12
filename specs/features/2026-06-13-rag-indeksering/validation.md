# Validation — RAG-indeksering av transkripsjoner

## Akseptansekriterier

- [ ] `python backend/core/rag/indekser.py` kjører uten feil
- [ ] Første kjøring indekserer alle 25 filer og logger antall chunks
- [ ] Andre kjøring indekserer 0 nye filer (idempotens)
- [ ] Ny fil i `transcripts/` indekseres kun ved neste kjøring
- [ ] `col.count()` returnerer > 0 etter kjøring
- [ ] Søk på `"inntektsvekst"` returnerer relevante chunks

## Søk-test (manuell)

```python
import chromadb
client = chromadb.PersistentClient("vector_db")
col = client.get_collection("transkripsjoner")
print(col.count())
res = col.query(query_texts=["inntektsvekst"], n_results=3)
print(res["documents"])
```

## Merge-sjekkliste

- [ ] Alle pytest-tester grønne
- [ ] CHANGELOG oppdatert
- [ ] `vector_db/` er i `.gitignore` og ikke committet
- [ ] `rag_konfig.yaml` er committet
- [ ] `requirements.txt` inneholder nye avhengigheter
