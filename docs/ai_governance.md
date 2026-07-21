# Analytical Copilot Controls

## Goal

The copilot answers questions about project data while keeping retrieval, SQL execution and audit behavior explicit.

Its context is limited to:

- dbt marts and model documentation;
- data dictionary and schema files;
- data quality checks;
- risk dashboard metrics.

## Safety Controls

- Offline deterministic mode works without external API keys.
- Retrieval is limited to local project files.
- SQL generation is allowlisted to documented marts.
- Only read-only `SELECT` and `WITH` statements are allowed.
- Multi-statement SQL is rejected.
- Destructive keywords such as `delete`, `drop`, `truncate`, `insert` and `update` are blocked.
- A default row limit is appended or enforced.
- Every provider path uses the same retrieval, SQL policy and audit boundary.
- Audit records default to `data/ai_audit/copilot_audit.jsonl` and include question, citations, guarded SQL, response and status.
- Evaluation cases run from `ai/evals/risk_copilot.yml`.

## Design Rationale

The useful boundary is narrow: assist an analyst without giving the model unrestricted database access. That means the feature must be:

- scoped to known data products;
- tested;
- explainable through citations;
- constrained by SQL policy;
- useful in an analyst workflow without bypassing governance.

The copilot is not a credit-decision model and has not been validated for regulated use. Provider-backed execution is optional; deterministic offline evaluation remains the release path.

## Local Commands

```bash
AI_DEMO_MODE=1 make ai-eval
AI_DEMO_MODE=1 DB_TARGET=duckdb make demo-local
AI_DEMO_MODE=1 DB_TARGET=duckdb make run-dashboard
```

## Future Enhancements

- Add a dedicated read-only database role in deployed environments.
- Add query result validation before final natural-language response.
- Add benchmark cases for hallucination and refusal quality.
