from __future__ import annotations

import re

import sqlparse
from sqlparse import tokens as sql_tokens


class SqlGuardrailError(ValueError):
    """Raised when generated SQL violates the assistant safety contract."""


_BLOCKED_KEYWORDS = {
    "alter",
    "analyze",
    "attach",
    "call",
    "comment",
    "copy",
    "create",
    "delete",
    "detach",
    "drop",
    "execute",
    "explain",
    "grant",
    "insert",
    "into",
    "load",
    "lock",
    "merge",
    "pragma",
    "refresh",
    "replace",
    "reset",
    "revoke",
    "set",
    "show",
    "truncate",
    "unload",
    "update",
    "use",
    "vacuum",
}
_IDENTIFIER = r'(?:"(?:[^"]|"")+"|[a-z_][\w$]*)'
_RELATION_PATTERN = re.compile(
    rf"\b(?:from|join)\s+({_IDENTIFIER})(?:\s*\.\s*({_IDENTIFIER}))?",
    flags=re.IGNORECASE,
)
_CTE_PATTERN = re.compile(
    rf"(?:\bwith|,)\s+(?:recursive\s+)?({_IDENTIFIER})\s+as\s*\(",
    flags=re.IGNORECASE,
)


def build_guarded_query(
    sql: str,
    *,
    allowed_schemas: tuple[str, ...],
    default_limit: int = 500,
) -> str:
    """Parse and constrain a single read-only analytical SELECT statement."""
    if default_limit <= 0:
        raise ValueError("default_limit must be greater than zero.")
    if not allowed_schemas:
        raise ValueError("At least one allowed schema is required.")

    statement = _parse_single_statement(sql)
    _reject_comments(statement)
    _validate_read_only_tokens(statement)

    query = _normalize_statement(str(statement))
    _validate_schema_scope(_without_string_literals(query), allowed_schemas)
    return _enforce_limit(query, default_limit)


def _parse_single_statement(sql: str):
    if not sql or not sql.strip():
        raise SqlGuardrailError("SQL statement is empty.")

    statements = [statement for statement in sqlparse.parse(sql) if str(statement).strip()]
    if len(statements) != 1:
        raise SqlGuardrailError("Only one SQL statement is allowed.")

    statement = statements[0]
    if statement.get_type() != "SELECT":
        raise SqlGuardrailError("Only SELECT statements are allowed.")
    return statement


def _reject_comments(statement) -> None:
    if any(token.ttype in sql_tokens.Comment for token in statement.flatten()):
        raise SqlGuardrailError("SQL comments are not allowed.")


def _validate_read_only_tokens(statement) -> None:
    for token in statement.flatten():
        if token.ttype in sql_tokens.Literal.String:
            continue
        keyword = token.normalized.lower()
        if keyword in _BLOCKED_KEYWORDS:
            raise SqlGuardrailError(f"Blocked SQL keyword: {keyword}")
        if token.ttype in sql_tokens.Keyword.DDL:
            raise SqlGuardrailError(f"Blocked SQL keyword: {keyword}")
        if token.ttype in sql_tokens.Keyword.DML and keyword != "select":
            raise SqlGuardrailError(f"Blocked SQL keyword: {keyword}")


def _normalize_statement(sql: str) -> str:
    query = sqlparse.format(sql.strip(), reindent=False, strip_whitespace=True)
    if query.endswith(";"):
        query = query[:-1].rstrip()
    return query


def _without_string_literals(sql: str) -> str:
    return re.sub(r"'(?:''|[^'])*'", "''", sql)


def _unquote_identifier(identifier: str) -> str:
    identifier = identifier.strip()
    if identifier.startswith('"') and identifier.endswith('"'):
        return identifier[1:-1].replace('""', '"').lower()
    return identifier.lower()


def _validate_schema_scope(sql: str, allowed_schemas: tuple[str, ...]) -> None:
    allowed = {schema.lower() for schema in allowed_schemas}
    cte_names = {_unquote_identifier(match) for match in _CTE_PATTERN.findall(sql)}
    physical_relations = 0

    for match in _RELATION_PATTERN.finditer(sql):
        first, second = match.groups()
        if second is None:
            relation = _unquote_identifier(first)
            if relation not in cte_names:
                raise SqlGuardrailError(
                    f"Relation must be schema-qualified or a declared CTE: {relation}"
                )
            continue

        schema = _unquote_identifier(first)
        physical_relations += 1
        if schema not in allowed:
            raise SqlGuardrailError(f"Schema is not allowlisted: {schema}")

    if physical_relations == 0:
        raise SqlGuardrailError("Query must reference an allowlisted schema-qualified table.")


def _enforce_limit(query: str, default_limit: int) -> str:
    limit_match = re.search(r"\blimit\s+(\d+)\s*$", query, flags=re.IGNORECASE)
    if limit_match:
        requested_limit = int(limit_match.group(1))
        if requested_limit <= 0:
            raise SqlGuardrailError("LIMIT must be greater than zero.")
        if requested_limit <= default_limit:
            return query
        return re.sub(
            r"\blimit\s+\d+\s*$",
            f"limit {default_limit}",
            query,
            flags=re.IGNORECASE,
        )

    # Non-literal top-level limits such as LIMIT ALL or LIMIT (expression) are
    # rejected instead of being followed by a second, potentially invalid limit.
    if re.search(r"\blimit\b[^)]*$", _without_string_literals(query), flags=re.IGNORECASE):
        raise SqlGuardrailError("LIMIT must be a positive integer literal.")
    return f"{query} limit {default_limit}"
