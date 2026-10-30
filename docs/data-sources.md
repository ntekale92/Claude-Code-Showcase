# Data sources

| | NSW property sales | UK new-car registrations |
|---|---|---|
| Publisher | NSW Valuer General | UK Department for Transport |
| Dataset | Bulk Property Sales Information (PSI) | Vehicle licensing statistics, table VEH0160 |
| Coverage | Every recorded NSW sale since 1990 | First-time registrations, UK from 2014 Q3 |
| Frequency | Weekly files; yearly archives | Quarterly |
| Format | Zips of semicolon-delimited `.DAT` files with mixed record types | Wide CSV, one column per quarter |
| Licence | CC BY-NC-ND 4.0 for non-commercial use; commercial use needs a PSI licence | Open Government Licence v3.0 |
| What we keep | `B` (sale) records, 24 documented fields | Body type, make, generic model, model, fuel, quarter, units |
| Pages | [catalogue entry](https://catalogue.data.infrastructure.gov.au/dataset/rdh-bulk-property-sales-information-nsw), [how to find sales info](https://www.nsw.gov.au/housing-and-construction/land-values-nsw/how-to-find-property-sales-information) | [data files](https://www.gov.uk/government/statistical-data-sets/vehicle-licensing-statistics-data-files) |

## Licence consequences for this repo
- **NSW is "no derivatives" and non-commercial.** Raw files and anything derived from them
  (warehouse, mart CSVs) stay on the user's machine: `data/raw/`, `data/warehouse_*.duckdb` and
  `data/marts_*/` are gitignored, and Claude Code is blocked from editing `data/raw/` by both a
  permission rule and a hook. Using this data inside a commercial product needs a PSI licence.
- **DfT is OGL v3.0**, which allows reuse with attribution.
- **The committed `data/sample/` files are synthetic.** They copy the real layouts so tests and CI run,
  but every value is invented by `src/oda/samples.py`.

## Layout notes
**NSW `.DAT`** — one record per line, fields separated by `;`, record type in field 1:
`A` header · `B` sale · `C` legal description · `D` purchaser/vendor · `Z` trailer.
`B` fields, in order: record type, district code, property id, sale counter, download datetime,
property name, unit no, house no, street name, locality, postcode, area, area type (M = m², H = ha),
contract date (YYYYMMDD), settlement date, purchase price, zoning, nature of property (R = residence,
V = vacant, 3 = other), primary purpose, strata lot no, component code, sale code, % interest of sale,
dealing no. The same sale can appear in several weekly files; staging keeps the latest download.

**DfT VEH0160** — identifier columns then one column per quarter (`2026 Q2`, `2026 Q1`, …).
Small counts are suppressed as `[c]`. The loader finds quarter columns by pattern, so it survives
DfT adding or reordering columns, and fails loudly if no quarter columns exist.

## Why these two
They're real, current, free, and messy in different ways: NSW has record-type parsing, duplicates,
reporting lag and non-market transfers; DfT has a wide layout, suppression and changing fuel labels.
Between them they exercise most of the problems a production BI pipeline meets.

## Considered and not used
- **VicRoads monthly new vehicle registrations** (CC BY 4.0, make/model/colour/year) — the latest
  release found was July 2024, so it looks discontinued.
- **Australian new-car sales (VFACTS)** — not open data.
