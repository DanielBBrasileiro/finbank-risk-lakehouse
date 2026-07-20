select
    observation_date,
    max(case when indicator_name = 'selic' then indicator_value end) as selic_rate,
    max(case when indicator_name = 'credit_free_total' then indicator_value end) as credit_free_total
from {{ ref('stg_macro_indicators') }}
group by observation_date
