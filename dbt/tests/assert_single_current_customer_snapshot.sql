select
    customer_id,
    count(*) as current_version_count
from {{ ref('customer_exposure_snapshot') }}
where dbt_valid_to is null
group by customer_id
having count(*) > 1
