# How Claude is used in this repo

The design principle: **put each instruction where it's enforced at the right strength.**
Facts Claude can't derive go in CLAUDE.md. Procedures go in skills. Judgement-heavy side work goes to
subagents with narrow tools. Rules that must never break go in hooks and permissions. Numbers go
through SQL, never through the model.

## Feature map

| Need | Claude feature | Where | Why this and not something else |
|---|---|---|---|
| Project facts and commands | CLAUDE.md | `CLAUDE.md` | Short (~30 lines) so it's read every session. Only what Claude can't infer from the code |
| SQL conventions only when editing SQL | Path-scoped rule | `.claude/rules/sql.md` (`paths: models/**/*.sql`) | Loads on demand instead of costing context on every turn |
| Repeatable procedures | Skills | `.claude/skills/*` | Body loads only when used. `new-metric` keeps five files in step; `add-data-source` starts in plan mode |
| Side-effect workflows the user triggers | `disable-model-invocation: true` | `stakeholder-update`, `add-data-source` | Claude shouldn't decide on its own to rewrite the RAID log or onboard a dataset |
| Isolated, focused review | Subagents | `.claude/agents/*` | `sql-reviewer` (read-only), `metric-steward` (governance), `data-quality-auditor` (Haiku, read-only, project memory), `delivery-pm` (edits `docs/pm/` only) |
| Skill that runs in its own context | `context: fork` + `agent:` | `dq-audit`, `stakeholder-update` | Long query output stays out of the main conversation; only the summary returns |
| Live data in prompts | Dynamic context injection | `` !`git log …` `` in `stakeholder-update`, `` !`git status …` `` in `verify` | Claude starts from the real state, not a guess |
| Ad-hoc warehouse questions | MCP | `.mcp.json` → DuckDB server, read-only by default | Exploration without giving write access |
| Hard rules | Permissions + hooks | `.claude/settings.json`, `.claude/hooks/*` | See ADR-0003. Tested in `tests/test_hooks.py` |
| Agent-specific guardrail | Hook in subagent frontmatter | `data-quality-auditor` → `block-writes-in-bash.sh` | Read-only is enforced, not requested |
| Context loss on long sessions | `SessionStart` hook, `compact` matcher | `after-compact.txt` | Key rules come back after compaction |
| CI collaboration | Claude Code GitHub Action | `.github/workflows/claude.yml`, `claude-sql-review.yml` | `@claude` on issues/PRs; automatic SQL + metric review using the repo's own subagents |
| Product feature using Claude | Claude API | `src/oda/insights.py` | Forced tool call for structured output, cached system prompt, deterministic grounding check |
| Knowing it works | Evals | `evals/` | Checker suite in CI; live suite measures the real model's grounded rate |

## A typical change, end to end

**"Add median days-to-settle as a governed KPI"**

1. `/new-metric median days to settle — middle number of days between contract and settlement`
   → the skill asks one clarifying question (include sales over 365 days?) before writing SQL.
2. Claude writes the card, SQL column, quality check and DAX. The **PostToolUse hook** rebuilds the
   warehouse after each SQL edit, so a typo is caught on that edit.
3. Claude asks the **metric-steward** subagent to review card ↔ SQL ↔ DAX ↔ check.
4. Claude tries to finish; the **Stop hook** runs `make check` and sends any failure back.
5. PR opened → **claude-sql-review.yml** runs `sql-reviewer` and `metric-steward` in CI and posts one comment.
6. Friday: `/stakeholder-update 2026-W45` → **delivery-pm** reads commits and RAID, writes the update.

## Patterns worth copying

- **Enforce, don't ask.** Anything legal or trust-critical is a hook or permission, with a test.
- **Verification is the work.** Every skill ends in a check; the Stop hook makes it non-optional.
- **Model at the edges.** SQL owns numbers, Claude owns words, a deterministic check sits between.
- **Least privilege per agent.** Reviewers can't edit; the PM can only edit `docs/pm/`; the auditor
  runs on a cheaper model because it reads and counts.
- **Evals for the guardrails too.** The grounding checker has its own pass/fail cases, and they caught
  a real bug during the build (ADR-0002).

## Five-minute demo

1. `make check` — 37 tests, 11 quality checks, 8 eval cases, in seconds, no downloads.
2. Open `.claude/settings.json` and `docs/adr/0003…` — explain hooks vs prompts.
3. In Claude Code, ask it to edit `data/raw/…` → blocked by the hook, with the reason.
4. Break a SQL model on purpose → the PostToolUse hook reports the error on that edit.
5. `/dq-audit` → forked subagent returns a source-vs-pipeline table.
6. `make brief` → open `reports/insight_brief_sample.md`; then show `evals/cases.yaml` and the
   `computed_difference` case: why "rose 2.51 points" is rejected even though it's true.
