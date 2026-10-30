---
name: stakeholder-update
description: Draft the weekly stakeholder update from git history, the RAID log, quality results and the delivery plan.
argument-hint: "[week, e.g. 2026-W44]"
disable-model-invocation: true
context: fork
agent: delivery-pm
---

Write the stakeholder update for **$ARGUMENTS** (default: the current ISO week).

## Inputs
- Commits this week: !`git log --since="7 days ago" --pretty="- %s (%h)" 2>/dev/null || echo "no git history"`
- Quality summary: !`PYTHONPATH=src python3 -m oda.quality 2>&1 | tail -n 15`
- RAID log: read `docs/pm/RAID.md`
- Plan: read `docs/pm/delivery-plan.md`
- Last update: the newest file in `docs/pm/stakeholder-updates/`

## Output
Write `docs/pm/stakeholder-updates/<week>.md` with these sections, plain English, under 300 words:
1. **Status** — one line: On track / At risk / Off track, and why
2. **Done this week** — from commits, in outcome language ("users can now…"), not file names
3. **Next week** — from the delivery plan
4. **Risks and issues** — only open RAID items that changed or need a decision, each with an owner
5. **Decisions needed** — specific question, who decides, by when. Leave out the section if none

Update RAID item statuses if the commits show they're resolved. Don't invent progress that isn't in
the commits or the plan.
