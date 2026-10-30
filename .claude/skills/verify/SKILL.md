---
name: verify
description: Run the full check (tests, data quality, evals) and report what failed. Use before any commit, after changing SQL, Python, metric cards or quality checks, or when asked "does it still work".
allowed-tools: Bash(make check) Bash(make build) Bash(make sample)
---

## Current state
!`git status --short -- src models quality metrics evals tests 2>/dev/null || true`

## Steps
1. If anything under `src/oda/samples.py` changed, run `make sample` first.
2. Run `make check`.
3. If it passes, say so in one line with the counts it printed (tests passed, checks passed, eval cases).
4. If it fails, report each failure as: what failed → the likely cause in the changed files → the fix.
   Fix it if the cause is clear and inside the change you just made. Otherwise stop and explain.
5. Never weaken a quality check or an eval case to make it pass. If a threshold really is wrong,
   say why and ask before changing it.
