select
    observation_date,
    indicator_name,
    count(*) as row_count
from {{ ref('stg_macro_indicators') }}
group by observation_date, indicator_name
having count(*) > 1
