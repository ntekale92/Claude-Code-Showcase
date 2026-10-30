-- Mart: new-car registrations by make per quarter: market share, rank and each make's BEV mix.
-- KPI card: metrics/make_market_share.yaml.
create or replace table mart_make_quarterly as
with base as (
    select quarter_start, quarter_label, make,
           sum(units)                                         as units,
           sum(units) filter (where fuel_group = 'BEV')       as bev_units,
           sum(units) filter (where fuel_group in ('BEV', 'PHEV', 'HEV')) as electrified_units
    from stg_dft_registrations
    where lower(body_type) = 'cars'
    group by all
)
select
    *,
    round(100.0 * units / sum(units) over (partition by quarter_start), 2)       as market_share_pct,
    rank() over (partition by quarter_start order by units desc nulls last)      as rank_in_quarter,
    round(100.0 * coalesce(bev_units, 0) / nullif(units, 0), 1)                  as bev_mix_pct,
    round(100.0 * coalesce(electrified_units, 0) / nullif(units, 0), 1)          as electrified_mix_pct
from base
where units is not null;
