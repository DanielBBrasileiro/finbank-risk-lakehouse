select
    cast(timestamp as timestamp) as audit_timestamp,
    status,
    question,
    citations,
    guarded_sql,
    response
from {{ source('raw', 'ai_copilot_audit') }}
