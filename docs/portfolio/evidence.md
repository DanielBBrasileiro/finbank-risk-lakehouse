# FinBank Portfolio Evidence Pack

## Public Repository

- Repository: https://github.com/DanielBBrasileiro/finbank-risk-lakehouse-starter
- Current branch: main
- Current commit: 196935b
- GitHub Actions CI: configured

## Local-first demo path

- Generate synthetic banking data.
- Validate raw CSV contracts with Rust.
- Build local Bronze/Silver/Gold lakehouse layers.
- Load PostgreSQL and run dbt marts when Docker is available.
- Run governed AI evals in deterministic offline mode.

## Artifact Status

- dbt manifest: present
- lakehouse manifest: present
- portfolio screenshots: 4 captured
- `docs/portfolio/screenshots/dashboard-account-health.png`
- `docs/portfolio/screenshots/dashboard-ai-governance.png`
- `docs/portfolio/screenshots/dashboard-credit-risk.png`
- `docs/portfolio/screenshots/dbt-docs-lineage.png`

## Verification Commands

- `make doctor`
- `make test`
- `make lint`
- `AI_DEMO_MODE=1 make ai-eval`
- `AI_DEMO_MODE=1 make pipeline-local`
- `make streaming-demo`

## Recruiter Narrative

This repository demonstrates a cost-aware data engineering lifecycle: generation, ingestion, storage, transformation, serving, governance, orchestration and AI controls.

## Evidence Captured

- Dashboard risk view captured after a local pipeline run.
- Account health dashboard captured after dbt marts were rebuilt.
- Governed AI audit captured with one answered and one rejected interaction.
- dbt docs lineage captured from the generated catalog.

## Publication Checklist

- Ensure the branch linked from LinkedIn contains the latest verified commits.
- Run `docs/portfolio/pre_linkedin_test_plan.md` before posting.
