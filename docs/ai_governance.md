# Governed AI Risk Copilot

## Goal

The AI component demonstrates that AI can be integrated into a data platform with controls that a risk, finance or analytics team could review.

The copilot is designed to answer questions about trusted project assets:

- dbt marts and model documentation;
- data dictionary and schema files;
- data quality checks;
- risk dashboard metrics.

## Safety Controls

- Offline deterministic mode works without external API keys.
- Retrieval is limited to local project files.
- SQL generation is allowlisted to governed marts.
- Only read-only `SELECT` and `WITH` statements are allowed.
- Multi-statement SQL is rejected.
- Destructive keywords such as `delete`, `drop`, `truncate`, `insert` and `update` are blocked.
- A default row limit is appended or enforced.
- Every provider path uses the same retrieval, SQL policy and audit boundary.
- Audit records default to `data/ai_audit/copilot_audit.jsonl` and include question, citations, guarded SQL, response and status.
- Evaluation cases run from `ai/evals/risk_copilot.yml`.

## Why This Matters For Recruiters

The goal is not to show that an LLM can produce text. The goal is to show that AI usage can be:

- scoped to trusted data products;
- tested;
- explainable through citations;
- constrained by SQL policy;
- useful in an analyst workflow without bypassing governance.

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
