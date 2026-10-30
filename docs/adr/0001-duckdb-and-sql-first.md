# ADR-0001: DuckDB warehouse, SQL-first models

- **Status:** Accepted
- **Date:** 2026-10-30

## Context
The project needs a warehouse anyone can clone and run in seconds, in CI, with no cloud account.
The logic should be readable by BI developers who know SQL better than Python.

## Decision
- DuckDB file warehouse (`data/warehouse_<mode>.duckdb`).
- Python only for what SQL is bad at: parsing the NSW record-type files, unpivoting the wide DfT CSV,
  orchestration, quality checks and the Claude call.
- Transformations are plain SQL files run in filename order. No dbt yet.

## Consequences
- Whole build runs in under a second on sample data; CI needs no services.
- No dependency graph: ordering is by filename prefix. Fine at 6 models; revisit at ~20.
- Moving to Databricks, Snowflake or Redshift later means porting a few DuckDB-specific functions
  (`try_strptime`, `quantile_cont`, `median`). They're concentrated in staging and the price marts.

## Alternatives considered
- **dbt + DuckDB** — better lineage and tests, but more setup than the project needs today.
  Revisit when models pass ~20 or a second contributor joins.
- **Pandas end to end** — harder to review for BI developers and slower on the full NSW history.
