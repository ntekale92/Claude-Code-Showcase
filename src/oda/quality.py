"""Run the data quality checks in quality/checks.yaml against the warehouse.

    python -m oda.quality            # prints a table, exits 1 if any `error` check fails
    python -m oda.quality --json     # machine-readable, used by the dq-audit skill
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import duckdb
import yaml

from oda import config


@dataclass
class CheckResult:
    name: str
    severity: str
    owner: str
    value: float | None
    expect: dict
    passed: bool
    description: str
    error: str | None = None


def _passes(value: float | None, expect: dict) -> bool:
    if value is None:
        return False
    if "eq" in expect and value != expect["eq"]:
        return False
    if "max" in expect and value > expect["max"]:
        return False
    if "min" in expect and value < expect["min"]:
        return False
    return True


def run_checks(db_path: Path | None = None, checks_file: Path | None = None) -> list[CheckResult]:
    checks = yaml.safe_load(Path(checks_file or config.QUALITY / "checks.yaml").read_text())["checks"]
    con = duckdb.connect(str(db_path or config.WAREHOUSE), read_only=True)
    results = []
    try:
        for c in checks:
            try:
                raw = con.execute(c["sql"]).fetchone()[0]
                value = None if raw is None else float(raw)
                results.append(CheckResult(c["name"], c["severity"], c.get("owner", ""), value, c["expect"],
                                           _passes(value, c["expect"]), c.get("description", "")))
            except duckdb.Error as exc:  # a broken check is a failed check, never a silent pass
                results.append(CheckResult(c["name"], c["severity"], c.get("owner", ""), None, c["expect"],
                                           False, c.get("description", ""), error=str(exc).splitlines()[0]))
    finally:
        con.close()
    return results


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)
    results = run_checks()
    if args.json:
        print(json.dumps([asdict(r) for r in results], indent=2))
    else:
        for r in results:
            mark = "PASS" if r.passed else ("FAIL" if r.severity == "error" else "WARN")
            shown = r.error or (f"{r.value:g}" if r.value is not None else "null")
            print(f"[{mark}] {r.name:<38} value={shown:<10} expect={r.expect}")
    failed = [r for r in results if not r.passed and r.severity == "error"]
    warned = [r for r in results if not r.passed and r.severity == "warn"]
    print(f"\n{len(results) - len(failed) - len(warned)} passed, {len(warned)} warnings, {len(failed)} errors",
          file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
