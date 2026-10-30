# PRD: Open Data Market Briefs

| | |
|---|---|
| Owner | Nilay Tekale |
| Status | v1 built on sample data; real-data validation in progress |
| Last updated | 2026-10-30 |

## Problem
Teams that track a market (property, auto) get either raw government data they can't use or
dashboards nobody opens. Leaders want three things a quarter: what moved, by how much, and whether
to trust it. Analysts spend days each quarter re-cleaning the same public files and re-writing the
same commentary.

## Users and jobs
| User | Job to be done |
|---|---|
| Market lead (exec) | "Tell me in two minutes what changed this quarter and whether it matters." |
| Analyst | "Give me clean, reconciled tables I can slice without re-cleaning the source." |
| BI developer | "Give me governed measures that match the published numbers." |
| Data governance | "Show me where each published number comes from and who owns it." |

## Scope (v1)
**In:** NSW property sales (suburb medians, YoY, volumes, settlement time); UK new-car registrations
(fuel mix, BEV share, make share); data quality checks with owners; governed metric cards; Power BI
measures; a written brief where every number is traceable.
**Out (v1):** forecasting, suburb-level rent or yield, Australian car data (no open source; see
`docs/data-sources.md`), a hosted dashboard.

## Requirements
1. Rebuild from source in one command; sample mode runs in CI without downloads.
2. Every excluded row is countable; marts reconcile to staging (check: `nsw_monthly_reconciles_to_staging`).
3. YoY only for quarters past the 90-day reporting lag.
4. Each published KPI has a card with owner, definition, version and caveats.
5. The brief contains no number that isn't a cited fact (ADR-0002), and never gives investment advice.
6. Licence terms are enforced technically, not by convention (ADR-0003, ADR-0004).

## Success measures
| Measure | Target | How measured |
|---|---|---|
| Quarterly refresh effort | < 30 min analyst time | Time from `make fetch` to sent brief |
| Brief grounding | 100% of sent briefs pass the checker; ≥ 90% first-try pass rate live | `evals/run_evals.py --live 20` |
| Numbers disputed after send | 0 per quarter | Stakeholder feedback log |
| Error-level DQ checks failing at release | 0 | `make check` in CI |

## Risks
Tracked in `docs/pm/RAID.md`.
