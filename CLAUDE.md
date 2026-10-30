# Open Data Analytics — project memory for Claude Code

Two public datasets, one DuckDB warehouse, governed metrics, and a Claude-written brief that is
checked number-by-number. Python 3.11+, DuckDB SQL, pytest.

## Commands
- `make sample` — regenerate synthetic sample files (same layout as the real files)
- `make build` — build the warehouse from `DATA_MODE` (default `sample`) and export marts to CSV
- `make check` — tests + data quality + evals. Must pass before any commit
- `make brief` — write `reports/insight_brief_<mode>.md` (uses Claude if `ANTHROPIC_API_KEY` is set)
- `make fetch` — download real data. Only the user runs this, on their own machine

## How the repo is laid out
- `src/oda/` — Python: fetch, parse, pipeline, quality, insights
- `models/staging/`, `models/marts/` — SQL, run in filename order (`01_` … `21_`). Table name = filename without the number
- `metrics/*.yaml` — governed KPI definitions. A mart column that feeds a KPI must match its card
- `quality/checks.yaml` — data quality rules; `error` fails the build
- `docs/adr/` — decisions and why. Read the relevant ADR before changing an approach it covers
- `docs/pm/` — PRD, delivery plan, RAID log, stakeholder updates

## Rules that matter here
- Claude writes words, SQL computes numbers. Never put a number into a brief, doc or commit message
  that didn't come from a query you ran (ADR-0002)
- Flag bad rows in staging; never silently drop them. Marts must reconcile back to staging
- Use medians for prices. Never publish YoY for a quarter inside the 90-day reporting lag
- DfT suppressed cells (`[c]`) are NULL, never zero
- Never edit or commit anything in `data/raw/` — NSW data is CC BY-NC-ND (no derivatives, non-commercial)
- New metric → `/new-metric`. New dataset → `/add-data-source`. Both keep code, cards, checks and DAX in step
- Australian English in docs and briefs
