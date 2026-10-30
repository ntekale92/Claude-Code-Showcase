---
name: dq-audit
description: Audit data quality on the current warehouse and explain every failing or warning check by owner, with likely root cause. Use when asked about data quality, after a fetch of new real data, or when a number looks wrong.
context: fork
agent: data-quality-auditor
---

Audit the warehouse for the current `DATA_MODE`.

1. Run `PYTHONPATH=src python -m oda.quality --json` and read the results.
2. For each check that failed or warned, run one or two follow-up queries against the warehouse to
   find the rows behind it (use the duckdb MCP server if connected, otherwise
   `python -c "import duckdb; ..."` with `read_only=True`).
3. Report a table: check | severity | owner | value vs expected | rows behind it (count + 3 examples) | likely cause.
4. Separate **source problems** (bad data from the publisher) from **pipeline problems** (our parsing or SQL).
   Only pipeline problems need a code change.
5. Don't change any files. End with the 1–3 actions that matter most.
