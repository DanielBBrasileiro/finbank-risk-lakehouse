from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from src.ai_assistant.retrieval import build_corpus, retrieve_context
from src.ai_assistant.sql_guardrails import SqlGuardrailError, build_guarded_query


@dataclass(frozen=True)
class CopilotAnswer:
    response: str
    citations: list[str]
    guarded_sql: str | None


def _execute_query(sql: str) -> str:
    """Execute the guarded SQL query against Postgres or DuckDB and return the results as a string."""
    import os
    from pathlib import Path

    import pandas as pd
    from sqlalchemy import create_engine, text

    db_target = os.getenv("DB_TARGET", "").lower()
    duckdb_file = Path("data/warehouse.duckdb")

    if db_target == "duckdb" and duckdb_file.exists():
        engine = create_engine(f"duckdb:///{duckdb_file}")
    else:
        user = os.getenv("POSTGRES_USER", "finbank")
        password = os.getenv("POSTGRES_PASSWORD", "finbank")
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        db = os.getenv("POSTGRES_DB", "finbank")

        try:
            engine = create_engine(f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}")
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        except Exception:
            if duckdb_file.exists():
                engine = create_engine(f"duckdb:///{duckdb_file}")
            else:
                return "Error: Database is offline and no local DuckDB warehouse was found."

    try:
        df = pd.read_sql(sql, engine)
        if df.empty:
            return "No records found."
        return df.to_markdown(index=False)
    except Exception as e:
        return f"Error executing query: {e}"


def answer_question(
    question: str,
    *,
    corpus_paths: list[Path] | None = None,
    allowed_schemas: tuple[str, ...] = ("analytics_marts",),
    default_limit: int = 100,
    audit_path: Path | None = None,
) -> CopilotAnswer:
    """Return a deterministic or dynamic governed answer."""
    import os
    import sys

    if _looks_destructive(question):
        answer = CopilotAnswer(
            response=(
                "I cannot run destructive or administrative SQL. "
                "The FinBank copilot is limited to governed read-only portfolio analysis."
            ),
            citations=[],
            guarded_sql=None,
        )
        _write_audit_record(question=question, answer=answer, audit_path=audit_path, status="rejected")
        return answer

    corpus = build_corpus(corpus_paths or _default_corpus_paths())

    api_key = os.getenv("GOOGLE_API_KEY")
    demo_mode = os.getenv("AI_DEMO_MODE", "0").lower() in {"1", "true", "yes"}
    is_testing = "pytest" in sys.modules or os.getenv("PYTEST_CURRENT_TEST") is not None

    # Select between vector RAG and keyword RAG
    if api_key and not demo_mode and not is_testing:
        try:
            from src.ai_assistant.vector_retrieval import (
                get_qdrant_client,
                index_corpus,
                retrieve_vector_context,
            )

            q_client = get_qdrant_client()
            index_corpus(q_client, corpus, api_key)
            contexts = retrieve_vector_context(question, q_client, api_key, top_k=3)
        except Exception as vector_err:
            print(f"Vector RAG error: {vector_err}. Falling back to keyword matching.")
            contexts = retrieve_context(question, corpus, top_k=3)
    else:
        contexts = retrieve_context(question, corpus, top_k=3)

    citations = [context.source for context in contexts]
    context_text = "\n\n".join(f"[{c.source}]:\n{c.text}" for c in contexts)

    if api_key and not demo_mode and not is_testing:
        try:
            from google import genai

            model_name = os.getenv("GOOGLE_MODEL", "gemini-2.5-flash")
            client = genai.Client(api_key=api_key)

            # Step A: Draft SQL using Gemini
            sql_prompt = (
                "You are a SQL generator for the FinBank Risk Lakehouse.\n"
                "Based on the user's question and the retrieved project documentation below, generate a single, read-only SQL query to answer the question.\n\n"
                f"Retrieved Context:\n{context_text}\n\n"
                "Rules:\n"
                "1. ONLY return the raw SQL query. Do not wrap it in markdown code blocks (e.g. ```sql), do not explain it, and do not add comments.\n"
                "2. The query MUST reference allowlisted schema-qualified tables (e.g. `analytics_marts.mart_customer_exposure` or `analytics_marts.mart_daily_transactions`).\n"
                "3. Only use SELECT and WITH statements.\n"
                "4. If the question does not require database query (e.g. general explanation or data quality question), return the word 'NONE'.\n\n"
                f"User Question: {question}"
            )

            sql_response = client.models.generate_content(
                model=model_name,
                contents=sql_prompt,
            )
            draft_sql = (sql_response.text or "").strip()

            # Clean markdown code blocks if any
            if draft_sql.startswith("```"):
                lines = draft_sql.splitlines()
                if len(lines) >= 2:
                    if lines[0].strip().startswith("```"):
                        lines = lines[1:-1]
                    draft_sql = "\n".join(lines).strip()

            guarded_sql: str | None = None
            sql_results: str = ""

            if draft_sql and draft_sql.upper() != "NONE":
                try:
                    guarded_sql = build_guarded_query(
                        draft_sql,
                        allowed_schemas=allowed_schemas,
                        default_limit=default_limit,
                    )
                    sql_results = _execute_query(guarded_sql)
                except SqlGuardrailError as exc:
                    answer = CopilotAnswer(
                        response=f"The generated SQL was rejected by guardrails: {exc}",
                        citations=citations,
                        guarded_sql=None,
                    )
                    _write_audit_record(
                        question=question, answer=answer, audit_path=audit_path, status="rejected"
                    )
                    return answer

                # Check for database errors and enter self-correction loop
                if sql_results.startswith("Error executing query:"):
                    attempts = 0
                    max_attempts = 2
                    current_error = sql_results
                    current_sql = guarded_sql

                    while attempts < max_attempts:
                        attempts += 1
                        print(
                            f"SQL execution failed. Attempting self-correction {attempts}/{max_attempts}..."
                        )

                        correction_prompt = (
                            "You are a SQL debugging assistant for the FinBank Risk Lakehouse.\n"
                            "The SQL query you generated failed execution in the warehouse with the error below.\n"
                            "Write a corrected, read-only SQL query to answer the question without errors.\n\n"
                            f"User Question: {question}\n"
                            f"Retrieved Context:\n{context_text}\n"
                            f"Failing SQL Query:\n{current_sql}\n"
                            f"Database Error:\n{current_error}\n\n"
                            "Rules:\n"
                            "1. ONLY return the raw SQL query. Do not wrap it in markdown code blocks, explanations, or comments.\n"
                            "2. Ensure the query references allowlisted schema-qualified tables.\n"
                            "3. Do not use prohibited statements (use SELECT or WITH only)."
                        )

                        correction_response = client.models.generate_content(
                            model=model_name,
                            contents=correction_prompt,
                        )
                        corrected_draft = (correction_response.text or "").strip()

                        if corrected_draft.startswith("```"):
                            lines = corrected_draft.splitlines()
                            if len(lines) >= 2:
                                if lines[0].strip().startswith("```"):
                                    lines = lines[1:-1]
                                corrected_draft = "\n".join(lines).strip()

                        try:
                            guarded_sql = build_guarded_query(
                                corrected_draft,
                                allowed_schemas=allowed_schemas,
                                default_limit=default_limit,
                            )
                            sql_results = _execute_query(guarded_sql)
                            if not sql_results.startswith("Error executing query:"):
                                print("SQL self-correction succeeded!")
                                break
                            current_error = sql_results
                            current_sql = guarded_sql
                        except Exception as correction_err:
                            current_error = f"Error: {correction_err}"
                            current_sql = corrected_draft

                    # If all correction attempts failed, we raise/fail
                    if sql_results.startswith("Error executing query:"):
                        answer = CopilotAnswer(
                            response=f"The generated SQL failed after correction attempts: {sql_results}",
                            citations=citations,
                            guarded_sql=guarded_sql,
                        )
                        _write_audit_record(
                            question=question, answer=answer, audit_path=audit_path, status="rejected"
                        )
                        return answer

            # Step B: Synthesize final response
            synth_prompt = (
                "You are the FinBank Risk Expert Assistant. Answer the user's question using the retrieved documentation context and the actual results of the SQL query we ran on the warehouse.\n\n"
                f"User Question: {question}\n\n"
                f"Retrieved Documentation:\n{context_text}\n\n"
            )
            if guarded_sql:
                synth_prompt += f"SQL Query Run:\n{guarded_sql}\n\nSQL Query Results:\n{sql_results}\n\n"
            else:
                synth_prompt += "No SQL query was required for this question.\n\n"

            synth_prompt += "Answer the question professionally, explaining the SQL results if present. Ground your answers in the provided data."

            synth_response = client.models.generate_content(
                model=model_name,
                contents=synth_prompt,
            )
            response_text = synth_response.text or ""

            answer = CopilotAnswer(
                response=response_text,
                citations=citations,
                guarded_sql=guarded_sql,
            )
            _write_audit_record(question=question, answer=answer, audit_path=audit_path, status="answered")
            return answer
        except Exception as err:
            print(f"Error during dynamic generation: {err}. Falling back to deterministic mode.")

    draft_sql = _draft_sql(question)
    guarded_sql = None
    if draft_sql:
        try:
            guarded_sql = build_guarded_query(
                draft_sql,
                allowed_schemas=allowed_schemas,
                default_limit=default_limit,
            )
        except SqlGuardrailError as exc:
            answer = CopilotAnswer(
                response=f"The generated SQL was rejected by guardrails: {exc}",
                citations=citations,
                guarded_sql=None,
            )
            _write_audit_record(question=question, answer=answer, audit_path=audit_path, status="rejected")
            return answer

    answer = CopilotAnswer(
        response=_compose_response(question, citations, guarded_sql),
        citations=citations,
        guarded_sql=guarded_sql,
    )
    _write_audit_record(question=question, answer=answer, audit_path=audit_path, status="answered")
    return answer


def _default_corpus_paths() -> list[Path]:
    return [Path("docs"), Path("dbt/models"), Path("schemas")]


def _looks_destructive(question: str) -> bool:
    lowered = question.lower()
    return any(keyword in lowered for keyword in ("delete", "drop", "truncate", "update", "insert", "grant"))


def _draft_sql(question: str) -> str | None:
    lowered = question.lower()
    if "exposure" in lowered and "segment" in lowered:
        return (
            "select segment, sum(total_outstanding_balance) as total_outstanding_balance "
            "from analytics_marts.mart_customer_exposure "
            "group by segment "
            "order by total_outstanding_balance desc"
        )
    if "suspicious" in lowered or "transaction" in lowered:
        return (
            "select transaction_date, channel, sum(suspicious_count) as suspicious_count "
            "from analytics_marts.mart_daily_transactions "
            "group by transaction_date, channel "
            "order by transaction_date desc"
        )
    if "default" in lowered or "high risk" in lowered:
        return (
            "select portfolio_status, count(*) as customer_count, "
            "sum(total_outstanding_balance) as total_outstanding_balance "
            "from analytics_marts.mart_customer_exposure "
            "group by portfolio_status "
            "order by total_outstanding_balance desc"
        )
    if "account" in lowered and ("health" in lowered or "status" in lowered or "blocked" in lowered):
        return (
            "select account_health_status, count(*) as customer_count, "
            "sum(total_accounts) as total_accounts, "
            "avg(active_ratio_pct) as avg_active_ratio "
            "from analytics_marts.mart_account_health "
            "group by account_health_status "
            "order by customer_count desc"
        )
    return None


def _compose_response(question: str, citations: list[str], guarded_sql: str | None) -> str:
    response = (
        "FinBank governed offline mode: I can answer from project documentation and "
        "only propose read-only SQL against allowlisted risk marts."
    )
    if guarded_sql:
        response += f"\n\nGuarded SQL:\n```sql\n{guarded_sql}\n```"
    else:
        response += "\n\nI did not need SQL for this question."
    if citations:
        response += "\n\nSources:\n" + "\n".join(f"- {source}" for source in citations)
    else:
        response += "\n\nNo local source matched this question."
    return response


def _write_audit_record(
    *,
    question: str,
    answer: CopilotAnswer,
    audit_path: Path | None,
    status: str,
) -> None:
    if audit_path is None:
        return

    audit_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(UTC).isoformat(),
        "status": status,
        "question": question,
        "citations": answer.citations,
        "guarded_sql": answer.guarded_sql,
        "response": answer.response,
    }
    with audit_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
