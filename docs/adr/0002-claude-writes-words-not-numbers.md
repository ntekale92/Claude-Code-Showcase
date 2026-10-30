# ADR-0002: Claude writes the words; SQL computes the numbers

- **Status:** Accepted
- **Date:** 2026-10-30

## Context
Stakeholders want a short written brief, not a dashboard. A language model writes good prose but
can state a wrong number confidently, and one wrong number in an exec brief costs more trust than
the brief earns.

## Decision
1. SQL computes every number. `build_facts()` turns mart rows into facts with stable ids
   (`uk.fuel.bev.share_pct`) and a `low_sample` flag.
2. Claude gets only the facts and must return a **forced tool call** (`submit_brief`) with each
   finding's `fact_ids`. No free-text parsing.
3. A deterministic checker (`check_brief`) rejects the brief if any number in a finding doesn't match
   a fact that finding cites, at the precision written; if it cites an unknown fact; if it uses a
   low-sample fact without saying so; or if it reads as investment advice.
4. The system prompt is cached (it's identical every run); facts aren't.
5. Without an API key a template writes the brief, so the pipeline never depends on the model.

## Consequences
- Claude can't do arithmetic in the brief. "BEV share rose 2.51 points" fails even though it's true,
  because 2.51 isn't a fact. If stakeholders want differences, add them as facts in SQL.
- `evals/cases.yaml` holds good and bad findings; CI fails if the checker accepts a bad one or rejects
  a good one. `--live N` measures how often the live model produces a fully grounded brief.
- The evals caught a real bug during build: a ±0.05 tolerance let "26.99%" match an unrelated fact
  worth 27.0. Matching is now precision-aware.

## Alternatives considered
- **Let Claude query the warehouse directly (MCP) and write freely** — great for exploration, which is
  why the duckdb MCP server is configured, but not verifiable enough for a published brief.
- **LLM-as-judge for accuracy** — useful for tone, but a second model checking numbers is weaker than
  a deterministic comparison.
