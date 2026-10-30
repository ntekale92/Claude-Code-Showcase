---
paths:
  - "models/**/*.sql"
---

# SQL conventions (load when working on models)

- One model per file: `create or replace table <name> as ...`. File `NN_<name>.sql`; staging 01–09, marts 10+
- Lowercase keywords and snake_case names. CTEs over nested subqueries
- First comment block states the grain ("one row per ...") and which `metrics/*.yaml` cards it feeds
- Cast with `try_cast` / `try_strptime` in staging only. Marts assume typed inputs
- Staging flags problems in `flag_*` boolean columns plus one `is_clean`. Marts filter on `is_clean`
- Any exclusion must be countable in a mart (see `mart_nsw_monthly` excluded_* columns)
- YoY: join on `quarter_start - interval 1 year`, never `lag(n)` — gaps would misalign it
- Shares: compute with a window over the same filtered set as the numerator
- After changing a model, add or update a check in `quality/checks.yaml` that would catch it breaking
