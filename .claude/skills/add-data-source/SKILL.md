---
name: add-data-source
description: Onboard a new open dataset (fetch, sample generator, staging model, quality checks, licence notes, ADR). Use when the user wants to add another public dataset to the warehouse.
argument-hint: "[dataset name or URL]"
disable-model-invocation: true
---

Onboard: **$ARGUMENTS**

Start in plan mode. Present the plan and wait for approval before editing.

1. **Research** — find the official source page. Record publisher, licence (exact name and version),
   update frequency, file format and the documented column layout. Note anything the licence forbids
   (commercial use, derivatives, redistribution). If the licence blocks committing derived data, say so.
2. **Decision record** — write `docs/adr/NNNN-add-<source>.md` using the existing ADRs as the format:
   why this source, alternatives considered, licence constraints.
3. **Config + fetch** — add the URL to `src/oda/config.py` (overridable by env var) and a
   `fetch_<source>()` to `src/oda/fetch.py`. Never commit the raw files.
4. **Sample generator** — extend `src/oda/samples.py` to write a small synthetic file with the
   *exact* real layout, including realistic quality problems, so CI runs without downloads.
5. **Models** — a staging model (types, flags, dedupe) and at least one mart, following
   `.claude/rules/sql.md`.
6. **Quality + metrics** — checks in `quality/checks.yaml`; a card in `metrics/` for each published KPI.
7. **Docs** — add the source to `docs/data-sources.md` and a RAID entry for its risks.
8. **Verify** — `make sample && make check`.
