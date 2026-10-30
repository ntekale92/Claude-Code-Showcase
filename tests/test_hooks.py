"""The hooks are guardrails, so they get tests like any other code."""

import json
import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HOOKS = ROOT / ".claude" / "hooks"


def run_hook(name: str, payload: dict) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(HOOKS / name)], input=json.dumps(payload), text=True, capture_output=True,
        env={**os.environ, "CLAUDE_PROJECT_DIR": str(ROOT)},
    )


@pytest.mark.parametrize("path,blocked", [
    ("data/raw/nsw/001_SALES.DAT", True),
    (f"{ROOT}/data/raw/dft/df_VEH0160_UK.csv", True),
    (".env", True),
    ("data/sample/nsw/x.DAT", True),
    ("data/warehouse_real.duckdb", True),
    ("models/marts/10_mart_suburb_quarterly.sql", False),
    ("docs/pm/RAID.md", False),
])
def test_protect_paths(path, blocked):
    r = run_hook("protect-paths.sh", {"tool_name": "Edit", "tool_input": {"file_path": path}})
    assert (r.returncode == 2) is blocked, r.stderr


@pytest.mark.parametrize("cmd,blocked", [
    ("python -m oda.quality --json", False),
    ("python -c \"import duckdb; duckdb.connect('data/warehouse_sample.duckdb', read_only=True)"
     ".sql('select * from mart_suburb_quarterly where median_price > 5000000')\"", False),
    ("python -m oda.quality 2>&1 | tail -5", False),
    ("rm data/warehouse_sample.duckdb", True),
    ("python -m oda.quality --json > findings.json", True),
    ("sed -i 's/a/b/' quality/checks.yaml", True),
    ("python -c \"duckdb.connect('x.duckdb').sql('delete from stg_nsw_sales')\"", True),
    ("python -c \"duckdb.connect('x.duckdb', read_only=False)\"", True),
])
def test_read_only_agent_guard(cmd, blocked):
    r = run_hook("block-writes-in-bash.sh", {"tool_name": "Bash", "tool_input": {"command": cmd}})
    assert (r.returncode == 2) is blocked, r.stderr


def test_stop_hook_never_loops():
    r = run_hook("check-before-stop.sh", {"stop_hook_active": True})
    assert r.returncode == 0
