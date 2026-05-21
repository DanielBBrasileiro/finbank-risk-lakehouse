from __future__ import annotations

import importlib
import shutil
import subprocess
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class CheckResult:
    name: str
    ok: bool
    detail: str
    critical: bool


def run_import_check(module_name: str, *, critical: bool) -> CheckResult:
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:
        return CheckResult(
            name=f"python package: {module_name}",
            ok=False,
            detail=f"{type(exc).__name__}: {exc}",
            critical=critical,
        )

    version = getattr(module, "__version__", "available")
    return CheckResult(name=f"python package: {module_name}", ok=True, detail=str(version), critical=critical)


def run_tool_check(tool_name: str, *, critical: bool) -> CheckResult:
    path = shutil.which(tool_name)
    if not path:
        return CheckResult(
            name=f"cli tool: {tool_name}",
            ok=False,
            detail="not found on PATH",
            critical=critical,
        )
    return CheckResult(name=f"cli tool: {tool_name}", ok=True, detail=path, critical=critical)


def run_command_check(name: str, command: list[str], *, critical: bool) -> CheckResult:
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True, timeout=30)
    except Exception as exc:
        return CheckResult(name=name, ok=False, detail=f"{type(exc).__name__}: {exc}", critical=critical)
    detail = result.stdout.strip() or result.stderr.strip() or "ok"
    return CheckResult(name=name, ok=True, detail=detail.splitlines()[0], critical=critical)


def run_checks() -> list[CheckResult]:
    return [
        run_command_check("python runtime", [sys.executable, "--version"], critical=True),
        run_import_check("numpy", critical=True),
        run_import_check("pandas", critical=True),
        run_import_check("pytest", critical=True),
        run_import_check("dbt", critical=True),
        run_import_check("pyarrow", critical=True),
        run_tool_check("cargo", critical=True),
        run_tool_check("docker", critical=False),
        run_tool_check("terraform", critical=False),
    ]


def overall_exit_code(results: list[CheckResult]) -> int:
    return 1 if any(result.critical and not result.ok for result in results) else 0


def format_markdown(results: list[CheckResult]) -> str:
    lines = ["# FinBank Environment Doctor", "", "| Check | Status | Detail | Critical |", "| --- | --- | --- | --- |"]
    for result in results:
        status = "PASS" if result.ok else "WARN" if not result.critical else "FAIL"
        lines.append(f"| {result.name} | {status} | {result.detail} | {result.critical} |")
    return "\n".join(lines)


def main() -> int:
    results = run_checks()
    print(format_markdown(results))
    return overall_exit_code(results)


if __name__ == "__main__":
    raise SystemExit(main())
