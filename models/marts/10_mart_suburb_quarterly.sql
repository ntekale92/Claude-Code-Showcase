-- Mart: suburb x dwelling type x quarter price summary. KPI cards: metrics/median_sale_price.yaml,
-- metrics/price_growth_yoy.yaml, metrics/sales_volume.yaml.
-- Medians, not means: a few large sales skew averages badly at suburb level.
-- Completeness: a quarter is complete only if (a) it starts on/after the first quarter covered by the
-- extract (earlier contracts are only partly captured) and (b) a 90-day settlement-reporting lag has passed.
-- YoY joins on the date one year earlier (not lag(4)) and is null unless BOTH quarters are complete.
create or replace table mart_suburb_quarterly as
with bounds as (
    select
        min(try_strptime(left(download_datetime, 8), '%Y%m%d'))::date as first_download,
        max(try_strptime(left(download_datetime, 8), '%Y%m%d'))::date as last_download
    from stg_nsw_sales
),
q as (
    select
        suburb,
        postcode,
        dwelling_type,
        contract_quarter                                    as quarter_start,
        count(*)                                            as sales_count,
        median(purchase_price)                              as median_price,
        quantile_cont(purchase_price, 0.25)                 as p25_price,
        quantile_cont(purchase_price, 0.75)                 as p75_price,
        median(days_to_settle)                              as median_days_to_settle
    from stg_nsw_sales
    where is_clean
    group by all
),
flagged as (
    select
        q.*,
        strftime(q.quarter_start, '%Y') || ' Q' || cast(quarter(q.quarter_start) as varchar) as quarter_label,
        q.quarter_start >= date_trunc('quarter', b.first_download)
            and (q.quarter_start + interval 3 month + interval 90 day) <= b.last_download    as is_complete_quarter,
        q.sales_count < 10                                                                    as low_sample
    from q
    cross join bounds as b
)
select
    cur.*,
    case when cur.is_complete_quarter and prev.is_complete_quarter then prev.median_price end as median_price_prior_year,
    case when cur.is_complete_quarter and prev.is_complete_quarter
         then round(100.0 * (cur.median_price / nullif(prev.median_price, 0) - 1), 1) end     as median_price_yoy_pct
from flagged as cur
left join flagged as prev
    on  prev.suburb = cur.suburb
    and prev.postcode = cur.postcode
    and prev.dwelling_type = cur.dwelling_type
    and prev.quarter_start = (cur.quarter_start - interval 1 year)::date;
