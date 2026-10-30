"""Governance as code: every metric card must point at things that actually exist."""

import re
from pathlib import Path

import duckdb
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
CARDS = sorted(p for p in (ROOT / "metrics").glob("*.yaml") if not p.name.startswith("_"))
REQUIRED = set(yaml.safe_load((ROOT / "metrics" / "_template.yaml").read_text()))
CHECK_NAMES = {c["name"] for c in yaml.safe_load((ROOT / "quality" / "checks.yaml").read_text())["checks"]}
DAX = (ROOT / "powerbi" / "measures.dax").read_text()


@pytest.mark.parametrize("card_path", CARDS, ids=lambda p: p.stem)
def test_metric_card_is_complete_and_wired_up(card_path, warehouse):
    card = yaml.safe_load(card_path.read_text())
    missing = REQUIRED - set(card)
    assert not missing, f"missing fields: {missing}"
    assert card["metric_id"] == card_path.stem

    table = card["source"]["table"]
    column = card["source"]["column"].split()[0]  # allow "share_pct (where ...)"
    con = duckdb.connect(str(warehouse), read_only=True)
    try:
        cols = {r[0] for r in con.execute(
            "select column_name from information_schema.columns where table_name = ?", [table]).fetchall()}
    finally:
        con.close()
    assert column in cols, f"{table}.{column} does not exist"

    measure = card["source"]["dax_measure"].strip("[]")
    assert re.search(rf"^{re.escape(measure)}\s*=", DAX, re.M), f"DAX measure [{measure}] not in powerbi/measures.dax"

    unknown = set(card["quality_checks"]) - CHECK_NAMES
    assert not unknown, f"unknown quality checks: {unknown}"

    versions = [c["version"] for c in card["change_log"]]
    assert card["definition_version"] == max(versions), "definition_version must match the latest change_log entry"
