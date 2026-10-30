# Delivery plan

Milestones are outcome-based: each one is done when its exit check passes, not when the code exists.

| # | Milestone | Exit check | Target | Status |
|---|---|---|---|---|
| M1 | Pipeline on sample data | `make check` green in CI | 2026-10-30 | ✅ Done |
| M2 | Governance layer | Every KPI has a card; `tests/test_governance.py` green | 2026-10-30 | ✅ Done |
| M3 | Claude brief with grounding | Checker suite 8/8; offline brief grounded | 2026-10-30 | ✅ Done |
| M4 | Real data run | `DATA_MODE=real make check` green on 2024–2026 NSW + DfT; DQ warnings explained | 2026-11-06 | 🔄 Next |
| M5 | Live model baseline | `run_evals.py --live 20` grounded rate recorded in README | 2026-11-06 | ⏳ |
| M6 | Power BI report | Report built on `data/marts_real/`; measures match SQL for 3 spot checks | 2026-11-13 | ⏳ |
| M7 | Quarterly runbook | A second person can run the refresh from `README` alone | 2026-11-20 | ⏳ |

## Next week (to 2026-11-06)
- Run `make fetch`, then `DATA_MODE=real make build` and `/dq-audit`
- Resolve or document every warning (expect real-data surprises in NSW zoning and DfT fuel labels)
- Record live eval baseline and add the first real-data brief to the README

## Dependencies
- NSW and DfT download URLs stay valid (overridable in `src/oda/config.py`)
- `ANTHROPIC_API_KEY` for M5
