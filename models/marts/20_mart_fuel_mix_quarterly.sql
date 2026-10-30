-- Mart: new-car registrations by fuel group per quarter, with share of the quarter.
-- KPI card: metrics/bev_share.yaml. Cars only. Suppressed cells are excluded from both
-- numerator and denominator and counted in suppressed_lines so the gap is visible.
create or replace table mart_fuel_mix_quarterly as
with base as (
    select quarter_start, quarter_label, fuel_group,
           sum(units)                          as units,
           count(*) filter (where suppressed)  as suppressed_lines
    from stg_dft_registrations
    where lower(body_type) = 'cars'
    group by all
)
select
    cur.*,
    round(100.0 * cur.units / sum(cur.units) over (partition by cur.quarter_start), 2) as share_pct,
    prev.units                                                                       as units_prior_year,
    round(100.0 * (cur.units / nullif(prev.units, 0) - 1), 1)                        as units_yoy_pct
from base as cur
left join base as prev
    on  prev.fuel_group = cur.fuel_group
    and prev.quarter_start = (cur.quarter_start - interval 1 year)::date;
