# CLAUDE.md — Arbeidsflyt og konvensjoner

Denne filen lastes automatisk av Claude Code og beskriver prosessen fra GitHub issue til ferdig PR.

---

## Arbeidsflyt (sekvens)

```
GitHub Issue  →  Plan  →  Godkjenning  →  Branch  →  Rød test  →  Implementering  →  PR
```

**Sekvensen gjelder alltid** — også når oppgaven kommer direkte i samtalen i VS Code uten et GitHub issue. Claude oppretter alltid feature-branch og PR. Bruker merger manuelt på GitHub. Ingen implementeringskode commites direkte til master.

---

## Trinn 1 — Hente krav fra GitHub

Bruker sier «hent issue #N» eller «hent nye issues».

```bash
gh issue view N
gh issue list
```

Krav hentes alltid fra GitHub. Aldri bare fra muntlig beskrivelse.

**Unntak:** Hvis oppgaven kommer direkte i samtalen uten GitHub issue, hoppes trinn 1 over. Resten av sekvensen (plan → branch → implementering → PR) følges uansett.

---

## Trinn 2 — Plan og spec

Opprett `specs/features/YYYY-MM-DD-navn/` med tre filer:

- `requirements.md` — scope, avgrensninger, arkitekturvalg
- `plan.md` — nummererte implementeringsgrupper
- `validation.md` — akseptansekriterier og merge-sjekkliste

**Tester defineres eksplisitt i plan.md** (TDD: skriv tester før kode).

Presenter planen og vent på eksplisitt godkjenning før noe kode skrives.

---

## Trinn 3 — Eksplisitt godkjenning

Ingen kode startes før bruker sier «kjør» eller tilsvarende. Bruker kan be om justeringer i planen.

---

## Trinn 4 — Branch

```bash
git checkout -b feature/YYYY-MM-DD-kort-navn   # ny funksjonalitet
git checkout -b fix/YYYY-MM-DD-kort-navn        # bugfix
```

Branchen knyttes til GitHub issue-nummeret i første commit-melding.

---

## Trinn 5 — TDD-implementering

1. Skriv tester først (rød)
2. Implementer kode (grønn)
3. Rydd opp (refaktorering)

Commit etter hver gruppe i plan.md.

**Commit-format (Conventional Commits):**

```
feat(modul): kort beskrivelse

Closes #N
```

Eksempler: `feat(rss): ...`, `fix(vault): ...`, `test(rss): ...`, `docs(changelog): ...`

**CHANGELOG.md oppdateres ved HVER commit.**
Tidsstempel-format: `*(YYYY-MM-DD HH:MM)*`

CHANGELOG-struktur:
- Nyeste øverst
- `[Uutgitt]` delt i `### Planlagte implementeringer` og `### Ad hoc-endringer`
- Subseksjoner `####`, endringstyper `#####`

**Etter hver gruppe:** kryss av i `plan.md` og `specs/veikart.md`.

---

## Trinn 6 — Pull request

```bash
gh pr create --title "feat: kort beskrivelse" --body "..."
```

PR-body skal inneholde:
- Summary (1-3 punkter)
- Test-plan (sjekkliste)
- Link til feature-spec (`specs/features/...`)
- Referanse til issue (`Closes #N`)

Siste commit på branchen bruker `Closes #N` — GitHub lukker issuet automatisk ved merge.

Claude oppretter PR og rapporterer URL i terminalen:

```bash
gh pr view
```

Bruker åpner PR i GitHub-utvidelsen i VS Code og merger manuelt.

---

## Definisjon av done

PR kan merges når:

- [ ] Alle tester grønne i CI (`pytest`)
- [ ] `validation.md` kryssav fullført
- [ ] CHANGELOG oppdatert med riktig tidsstempel

---

## Bugfikser (avvik fra normalflyten)

- Ingen feature-mappe opprettes
- Direkte CHANGELOG-oppføring + notat i `specs/veikart.md`
- Branch: `fix/YYYY-MM-DD-navn`

---

## Merge-rutine

Ved merge: kryss av `specs/features/.../validation.md` — alle gjennomførte punkter merkes `[x]`, uverifiserte beholdes `[ ]` med merknad.

---

## Lagringsansvar (strengt skilt)

| Lager | Innhold |
|-------|---------|
| Obsidian-vault | Artikkeltekst og bilder |
| SQLite | Metadata, sammendrag, triplets, vektorer (primærkilde) |
| Opik | API-spor, eksperimenter, synkronisert kopi av triplets |

**Filskrivingsrekkefølge:** UUID → fil → SQLite → rollback ved feil.

---

## Andre konvensjoner

- Alle norske enum-verdier bevares: `sammendrag`, `dommer_validering`, `rag_gjenfinning`, `rag_generering`
- Versjonering: Fase A=0.1.0, B=0.2.0, C=0.3.0, D=1.0.0
- Skrivestil: profesjonelt og nøkternt, ingen tankestreker i dokumentasjon
- Aldri kontraster av typen «ikke X, men Y» — skriv direkte hva det er
- Feature-mappe opprettes bare for features med substans (krav, arkitekturvalg)
