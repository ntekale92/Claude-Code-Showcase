---
name: new-metric
description: Add or change a governed KPI end to end — definition card, SQL, quality check, DAX measure and docs kept in step. Use when the user asks for a new metric, KPI, measure, or to change how one is calculated.
argument-hint: "[metric name and plain-English definition]"
---

Add or change the metric: **$ARGUMENTS**

A metric isn't done until all five pieces agree. Work through them in order.

1. **Definition card** — create or update `metrics/<metric_id>.yaml` from `metrics/_template.yaml`.
   Fill every field. If the business definition is ambiguous (grain, filters, what counts as
   excluded), ask the user one question before writing SQL. Don't guess on definitions.
2. **SQL** — add the column to the mart named in the card's `source.table`, following
   `.claude/rules/sql.md`. If no mart fits, create the next-numbered mart file.
3. **Quality check** — add at least one `error`-severity check to `quality/checks.yaml` that would
   fail if the metric broke (e.g. shares sum to 100, value within plausible range, reconciles).
4. **DAX** — add the equivalent measure to `powerbi/measures.dax` in the card's display folder.
   The DAX must give the same answer as the SQL at the card's grain.
5. **Verify** — run `make check`. Then query the new column for the latest period and show the
   user 3–5 sample values so they can sanity-check them.

Finish with a short summary listing the five files touched. Hand the diff to the `metric-steward`
subagent for review if the change alters an existing metric's definition.
