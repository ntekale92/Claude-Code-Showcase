# ADR-0004: Real open data locally, synthetic fixtures in the repo

- **Status:** Accepted
- **Date:** 2026-10-30

## Context
A portfolio project is more convincing on real data. But the NSW licence forbids derivatives and
commercial use, the files are large, and CI shouldn't depend on government servers being up or URLs
staying put.

## Decision
- `python -m oda.fetch` downloads the real data into gitignored `data/raw/`. URLs live in
  `src/oda/config.py` and can be overridden by environment variables when publishers move files.
- `src/oda/samples.py` generates small synthetic files with the **exact** real layouts, including the
  real files' quality problems (duplicates across weekly files, zero-price transfers, settlement before
  contract, suppressed `[c]` cells, non-car body types). They're committed and deterministic (fixed seed);
  CI regenerates them and fails if they drift.
- `DATA_MODE=sample|real` switches the whole pipeline. Every output says which mode produced it, and
  sample-mode briefs carry a "SAMPLE DATA" caveat.

## Consequences
- Anyone can clone, `make check`, and see the full system work in seconds.
- Sample numbers mean nothing. Results shown in the README come from real-mode runs on the author's
  machine; the sample brief exists only to prove the mechanics.
- The fixtures can drift from reality if a publisher changes layout. The loaders fail loudly on
  layout changes (no quarter columns, unparseable dates) and the quality checks track parse rates.
