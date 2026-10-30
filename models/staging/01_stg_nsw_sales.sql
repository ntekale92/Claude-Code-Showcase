-- Staging: NSW property sales ('B' records), typed, de-duplicated and flagged.
-- Grain: one row per sale (district_code, property_id, sale_counter, dealing_no).
-- Rows that fail a rule are FLAGGED, not dropped, so marts can be reconciled back to raw.
create or replace table stg_nsw_sales as
with typed as (
    select
        district_code,
        property_id,
        try_cast(sale_counter as integer)                              as sale_counter,
        nullif(trim(dealing_no), '')                                   as dealing_no,
        download_datetime,
        nullif(trim(unit_no), '')                                      as unit_no,
        nullif(trim(house_no), '')                                     as house_no,
        upper(trim(street_name))                                       as street_name,
        upper(trim(locality))                                          as suburb,
        trim(postcode)                                                 as postcode,
        try_cast(area as double)                                       as area,
        nullif(trim(area_type), '')                                    as area_type,
        try_strptime(nullif(trim(contract_date), ''), '%Y%m%d')::date   as contract_date,
        try_strptime(nullif(trim(settlement_date), ''), '%Y%m%d')::date as settlement_date,
        try_cast(purchase_price as bigint)                             as purchase_price,
        nullif(trim(zoning), '')                                       as zoning,
        upper(trim(nature_of_property))                                as nature_of_property,
        upper(trim(primary_purpose))                                   as primary_purpose,
        nullif(trim(strata_lot_no), '')                                as strata_lot_no,
        source_file
    from raw_nsw_sales
),
deduped as (
    -- the same sale can appear in several weekly files; keep the latest download
    select *,
           row_number() over (
               partition by district_code, property_id, sale_counter, dealing_no
               order by download_datetime desc, source_file desc
           ) as rn
    from typed
)
select
    * exclude (rn),
    case when strata_lot_no is not null or unit_no is not null then 'Unit' else 'House' end as dwelling_type,
    date_trunc('month', contract_date)::date                     as contract_month,
    date_trunc('quarter', contract_date)::date                   as contract_quarter,
    datediff('day', contract_date, settlement_date)              as days_to_settle,
    coalesce(purchase_price, 0) < 10000                          as flag_nominal_price,
    coalesce(settlement_date < contract_date, false)             as flag_bad_dates,
    contract_date is null                                        as flag_missing_contract_date,
    not (coalesce(nature_of_property, '') = 'R'
         and coalesce(primary_purpose, '') like '%RESID%')       as flag_not_residential,
    not (coalesce(purchase_price, 0) < 10000
         or coalesce(settlement_date < contract_date, false)
         or contract_date is null
         or not (coalesce(nature_of_property, '') = 'R'
                 and coalesce(primary_purpose, '') like '%RESID%')) as is_clean
from deduped
where rn = 1;
