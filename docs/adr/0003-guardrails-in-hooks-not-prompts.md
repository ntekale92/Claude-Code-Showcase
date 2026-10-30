# ADR-0003: Rules that can't have exceptions go in hooks and permissions, not prompts

- **Status:** Accepted
- **Date:** 2026-10-30

## Context
CLAUDE.md and skills are instructions; Claude follows them well but not with certainty, especially
late in a long session or after compaction. Some rules here are legal (licence) or protect trust in
the numbers, so "usually followed" isn't enough.

## Decision
| Rule | Enforced by |
|---|---|
| Never modify licensed raw data, secrets, generated files | `permissions.deny` **and** `PreToolUse` hook `protect-paths.sh` |
| A broken SQL model is caught on the edit that broke it | `PostToolUse` hook `rebuild-on-sql-edit.sh` (rebuild takes <1s) |
| Don't finish with failing tests, quality checks or evals | `Stop` hook `check-before-stop.sh` (guarded by `stop_hook_active`) |
| Key rules survive context compaction | `SessionStart` hook with `compact` matcher re-injects them |
| Read-only agents stay read-only | `data-quality-auditor` frontmatter `PreToolUse` hook `block-writes-in-bash.sh` |
| Downloads only through the documented fetch script | `Bash(curl *)`, `Bash(wget *)` denied; `make fetch` asks first |

Judgement calls (SQL style, how to word a brief, metric definitions) stay in CLAUDE.md, rules and skills.

## Consequences
- Hooks are code, so they're tested (`tests/test_hooks.py`). Writing those tests found a real gap:
  the sample-data guard missed relative paths.
- Hooks need `python3` and `bash`; Windows users need Git Bash or WSL.
- A `PreToolUse` deny applies in every permission mode, including bypass, which is the point.
