from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen


def main() -> int:
    if not Path("data/warehouse.duckdb").exists():
        print("data/warehouse.duckdb is required; run make demo-local first.", file=sys.stderr)
        return 2

    env = os.environ.copy()
    env.update({"PYTHONPATH": ".", "DB_TARGET": "duckdb", "AI_DEMO_MODE": "1"})
    command = [
        ".venv/bin/streamlit",
        "run",
        "dashboards/streamlit_app.py",
        "--server.headless=true",
        "--server.port=8765",
        "--browser.gatherUsageStats=false",
    ]
    process = subprocess.Popen(command, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        for _ in range(40):
            if process.poll() is not None:
                output = process.stdout.read() if process.stdout else ""
                print(output, file=sys.stderr)
                return process.returncode or 1
            try:
                with urlopen("http://127.0.0.1:8765/_stcore/health", timeout=1) as response:
                    if response.status == 200 and response.read().decode().strip() == "ok":
                        print("Streamlit health check passed.")
                        return 0
            except URLError:
                time.sleep(0.5)
        print("Streamlit did not become healthy within 20 seconds.", file=sys.stderr)
        return 1
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


if __name__ == "__main__":
    raise SystemExit(main())
