# LinkedIn Carousel Plan

Use a 1080 x 1350 px portrait canvas, a white background, dark text and the restrained colors already used in `architecture-overview.svg`. Keep one message per page and preserve generous margins for LinkedIn cropping.

## Page 1 - Cover

**Title:** From Raw Banking Data to Governed Risk Analytics

**Short copy:** FinBank Risk Lakehouse

**Technology line:** Python • Rust • dbt • DuckDB • PostgreSQL

**Recommended visual:** Use the project name as the main visual signal with a narrow crop of the architecture diagram below it.

**Repository asset:** `docs/portfolio/screenshots/architecture-overview.svg`

**Suggested word limit:** 18 words, excluding the technology line.

**Do not include:** test counts, cloud logos, paragraphs, badges or claims about production use.

## Page 2 - Problem

**Title:** One portfolio, conflicting definitions

**Short copy:** Different definitions of exposure, delinquency and suspicious activity can produce inconsistent risk reports. FinBank keeps those definitions aligned from source validation to analytical marts.

**Recommended visual:** Show three conflicting metric cards converging into one documented definition and one mart.

**Repository asset:** Use terminology from `docs/business_context.md`; no screenshot is required.

**Suggested word limit:** 35 words.

**Do not include:** generic digital-transformation language, unsupported business impact or real bank/customer references.

## Page 3 - Architecture

**Title:** A reviewable path through the data

**Short copy:** Sources → Python ingestion → Rust contracts → Bronze / Silver / Gold → DuckDB / PostgreSQL → dbt marts → Streamlit → controlled analytical access.

**Recommended visual:** Use the canonical architecture diagram at full width and highlight the validation boundary before warehouse loading.

**Repository asset:** `docs/portfolio/screenshots/architecture-overview.svg`

**Suggested word limit:** 28 words outside the diagram.

**Do not include:** optional cloud blueprints in the main path, source code snippets or a second competing diagram.

## Page 4 - Reliability

**Title:** Reliability is part of the pipeline

**Short copy:** Invalid batches are rejected. Source and mart totals are reconciled. Event replay is idempotent. Read-only analytical access is audited. CI and CodeQL verify the release path.

**Recommended visual:** Use five compact proof points with simple check marks, plus a small GitHub Actions crop.

**Repository assets:** `docs/portfolio/screenshots/github-actions-release.png`, `docs/portfolio/screenshots/dbt-lineage.png`, and `docs/portfolio/screenshots/copilot-governance.png`

**Suggested word limit:** 40 words.

**Do not include:** unverified performance numbers, security guarantees, “production-ready” language or a wall of test output.

## Page 5 - Result

**Title:** Risk products that can be rerun and reviewed

**Short copy:** Built to be reviewed, rerun and questioned.

**Recommended visual:** Use the credit-risk dashboard as the main image. Add the repository URL below it and reserve a small corner for an optional QR code.

**Repository asset:** `docs/portfolio/screenshots/dashboard-credit-risk.png`

**Suggested word limit:** 16 words, excluding the URL.

**Do not include:** a required QR code, invented adoption metrics, employer/client logos or claims that the platform processes real customers.

