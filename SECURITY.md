# Security Policy

## Supported Version

Security fixes are applied to the latest release on `main`.

## Reporting

Do not open a public issue for a suspected vulnerability or exposed credential. Use GitHub private vulnerability reporting for this repository.

The repository contains synthetic data only. Never commit `.env`, cloud credentials, API keys, production financial data or customer identifiers.

## Controls

CI runs dependency auditing, CodeQL, tests and infrastructure validation. The AI assistant is limited to read-only analytical SQL and all provider paths must use the shared guardrail and audit boundary.
