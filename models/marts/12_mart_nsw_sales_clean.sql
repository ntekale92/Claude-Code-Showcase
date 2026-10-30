-- Mart: one row per clean residential sale, for Power BI.
-- Medians can't be averaged, so BI needs sale-level rows to recompute [Median Sale Price] for any
-- slice (region, dwelling type, period). Carries the quarter completeness flag so YoY measures
-- can blank themselves inside the reporting lag. Local export only: NSW data is CC BY-NC-ND.
create or replace table mart_nsw_sales_clean as
select
    s.district_code,
    s.property_id,
    s.sale_counter,
    s.suburb,
    s.postcode,
    s.dwelling_type,
    s.contract_date,
    s.contract_month,
    s.contract_quarter,
    s.settlement_date,
    s.days_to_settle,
    s.purchase_price,
    s.area,
    s.area_type,
    case when q.is_complete_quarter then 1 else 0 end as quarter_complete_flag
from stg_nsw_sales as s
left join (
    select distinct quarter_start, is_complete_quarter from mart_suburb_quarterly
) as q
    on q.quarter_start = s.contract_quarter
where s.is_clean;
