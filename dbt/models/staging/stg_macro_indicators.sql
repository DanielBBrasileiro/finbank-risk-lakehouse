select
    cast(observation_date as date) as observation_date,
    indicator_name,
    cast(series_id as integer) as series_id,
    cast(value as numeric) as value
from {{ source('raw', 'macro_indicators') }}
