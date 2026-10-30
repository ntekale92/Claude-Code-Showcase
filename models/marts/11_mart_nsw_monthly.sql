-- Mart: statewide monthly market summary with a reconciliation of every excluded row.
-- included + each exclusion reason must add back to the staging row count (see quality/checks.yaml).
create or replace table mart_nsw_monthly as
select
    contract_month                                                  as month_start,
    dwelling_type,
    count(*) filter (where is_clean)                                as sales_count,
    median(purchase_price) filter (where is_clean)                  as median_price,
    median(days_to_settle) filter (where is_clean)                  as median_days_to_settle,
    count(*) filter (where flag_nominal_price)                      as excluded_nominal_price,
    count(*) filter (where flag_bad_dates)                          as excluded_bad_dates,
    count(*) filter (where flag_not_residential)                    as excluded_not_residential,
    count(*) filter (where not is_clean)                            as excluded_total,
    count(*)                                                        as staged_total
from stg_nsw_sales
where contract_month is not null
group by all;
