select
    cast(macro_source.observation_date as date) as observation_date,
    macro_source.indicator_name,
    cast(macro_source.series_id as integer) as series_id,
    cast(macro_source."value" as numeric) as indicator_value  -- noqa: RF06
from {{ source('raw', 'macro_indicators') }} as macro_source
