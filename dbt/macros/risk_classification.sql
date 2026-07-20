{% macro portfolio_status(loan_count_expression, max_days_past_due_expression) -%}
case
    when {{ loan_count_expression }} = 0 then 'NO_CREDIT_EXPOSURE'
    when {{ max_days_past_due_expression }} >= 90 then 'DEFAULT_RISK'
    when {{ max_days_past_due_expression }} >= 30 then 'HIGH_RISK'
    when {{ max_days_past_due_expression }} > 0 then 'WATCHLIST'
    else 'PERFORMING'
end
{%- endmacro %}


{% macro risk_rating_score(risk_rating_expression) -%}
case {{ risk_rating_expression }}
    when 'AA' then 1
    when 'A' then 2
    when 'B' then 3
    when 'C' then 4
    when 'D' then 5
    when 'E' then 6
end
{%- endmacro %}


{% macro risk_rating_from_score(score_expression) -%}
case {{ score_expression }}
    when 1 then 'AA'
    when 2 then 'A'
    when 3 then 'B'
    when 4 then 'C'
    when 5 then 'D'
    when 6 then 'E'
end
{%- endmacro %}
