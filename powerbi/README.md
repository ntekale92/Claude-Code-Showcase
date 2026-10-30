# Power BI

1. `DATA_MODE=real make build` (or `make build` for sample) writes CSVs to `data/marts_<mode>/`.
2. Get Data → Folder → `data/marts_<mode>/`, load each CSV as a table.
3. Add a Date table and mark it; relate it to `mart_nsw_sales_clean[contract_date]`,
   `mart_fuel_mix_quarterly[quarter_start]` and `mart_make_quarterly[quarter_start]`.
4. Paste the measures from `measures.dax`. Put property measures in a "Property" display folder and
   car measures in "New cars".

**Why sale-level rows for property:** a median can't be rebuilt from other medians. Averaging
`mart_suburb_quarterly[median_price]` across suburbs gives a wrong number, so `[Median Sale Price]`
recomputes from `mart_nsw_sales_clean` for whatever is in filter context.

**Spot-check before publishing:** for three suburb-quarters, compare `[Median Sale Price]` and
`[Median Price YoY %]` with `mart_suburb_quarterly`. They must match exactly.

**Licence:** NSW-derived tables are for non-commercial use (CC BY-NC-ND). Don't publish the .pbix
with NSW data to the web or use it in a commercial product without a PSI licence.
