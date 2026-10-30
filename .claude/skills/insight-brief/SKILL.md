---
name: insight-brief
description: Produce the stakeholder market brief for NSW property and UK new cars, grounded in warehouse facts and checked number-by-number. Use when asked for a summary, brief, commentary or "what's the story in the data".
allowed-tools: Bash(make build) Bash(make brief) Bash(python -m oda.*)
---

1. Run `make build` so the brief reflects the current data, then `make brief`.
2. If the grounding check fails, show the user the exact problems it listed. Don't hand-edit the
   brief to make numbers fit — fix the prompt in `src/oda/insights.py` or the fact pack instead, and
   re-run. If you change the prompt, run `python evals/run_evals.py --live 5` (needs an API key)
   and report the grounded rate before and after.
3. Show the user the brief from `reports/insight_brief_<mode>.md`.
4. If `DATA_MODE` is `sample`, say clearly that the numbers are synthetic.
5. Don't add numbers of your own in the chat summary. Quote the brief or the facts it cites.
