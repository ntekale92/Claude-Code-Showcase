-- Staging: UK first-time vehicle registrations (DfT VEH0160), one row per line x quarter.
-- Suppressed cells ('[c]' etc.) become NULL units with suppressed = true; they are never treated as zero.
create or replace table stg_dft_registrations as
with typed as (
    select
        trim(body_type)                                             as body_type,
        upper(trim(make))                                           as make,
        upper(trim(gen_model))                                      as gen_model,
        upper(trim(model))                                          as model,
        upper(trim(fuel))                                           as fuel,
        trim(quarter_label)                                         as quarter_label,
        try_cast(regexp_extract(quarter_label, '(\d{4})', 1) as integer)     as yr,
        try_cast(regexp_extract(quarter_label, 'Q([1-4])', 1) as integer)    as qtr,
        try_cast(replace(trim(units_raw), ',', '') as integer)      as units,
        trim(units_raw) like '[%]'                                  as suppressed
    from raw_dft_veh0160
)
select
    body_type, make, gen_model, model, fuel, quarter_label,
    make_date(yr, (qtr - 1) * 3 + 1, 1)                             as quarter_start,
    units,
    suppressed,
    case
        when fuel like '%BATTERY%'   then 'BEV'
        when fuel like '%PLUG-IN%'   then 'PHEV'
        when fuel like '%HYBRID%'    then 'HEV'
        when fuel like '%RANGE EXTENDED%' then 'PHEV'
        when fuel like 'PETROL%'     then 'Petrol'
        when fuel like 'DIESEL%'     then 'Diesel'
        else 'Other'
    end                                                             as fuel_group
from typed
where yr is not null and qtr is not null;
