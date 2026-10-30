# RAID log

Every entry needs an owner, a trigger to watch, and a next action. Status: Open / Watching / Closed.

## Risks
| ID | Risk | Likelihood / impact | Trigger to watch | Owner | Next action | Status |
|---|---|---|---|---|---|---|
| R1 | Publisher moves a download URL and refresh fails | Med / Med | `make fetch` errors | Nilay | URLs are env-overridable; check publisher page and update `config.py` | Watching |
| R2 | Real NSW file layout differs from documented 24 fields | Med / High | `nsw_unparsed_contract_dates` > 0.5% | Nilay | Run `/dq-audit` on first real build; adjust parser | Open |
| R3 | New DfT fuel labels fall into "Other" and understate BEV share | Med / Med | `dft_unmapped_fuel_types` warning | Nilay | Extend the CASE mapping; bump `bev_share` card version | Watching |
| R4 | Live model brief fails grounding often enough to slow the refresh | Low / Med | Live grounded rate < 90% | Nilay | Tighten prompt; offline template is the fallback | Open |
| R5 | NSW data used beyond non-commercial terms | Low / High | Any commercial reuse request | Nilay | Needs a PSI licence first; raw and derived data are gitignored and edit-blocked | Watching |

## Assumptions
| ID | Assumption | Validated by |
|---|---|---|
| A1 | 90 days after quarter end is enough for most NSW sales to be reported | Compare quarter counts across two consecutive real refreshes (M4) |
| A2 | Under 10 sales is too few for a suburb median to headline | Review with a property analyst |
| A3 | Pattern-mapping DfT fuel labels is stable quarter to quarter | `dft_unmapped_fuel_types` stays at 0 across refreshes |

## Issues
| ID | Issue | Owner | Action | Status |
|---|---|---|---|---|
| I1 | Percentage matching tolerance let a wrong citation pass the grounding check | Nilay | Fixed: precision-aware matching; eval case `right_number_wrong_citation` added | Closed |
| I2 | Sample-data edit guard missed relative paths | Nilay | Fixed in `protect-paths.sh`; covered by `tests/test_hooks.py` | Closed |

## Dependencies
| ID | Depends on | For | Status |
|---|---|---|---|
| D1 | NSW Valuer General bulk PSI files | M4 | Available |
| D2 | DfT VEH0160 quarterly file | M4 | Available (last updated 2026-09-23) |
| D3 | Anthropic API key | M5 | Needed |
