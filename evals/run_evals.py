"""Evaluate the insight brief.

Two suites:
  checker  - does the grounding checker accept good findings and reject bad ones? (offline, runs in CI)
  live     - how often does Claude produce a fully grounded brief? (needs ANTHROPIC_API_KEY)

    python evals/run_evals.py                 # checker suite
    python evals/run_evals.py --live 5        # plus 5 live Claude runs
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

import yaml

from oda import insights

HERE = Path(__file__).parent


def _resolve(pack: insights.FactPack) -> dict[str, str]:
    """Aliases so cases work on any data: TOP_YOY = biggest non-low-sample YoY rise."""
    yoy = sorted((f for f in pack.facts if f.id.endswith("median_yoy_pct") and not f.low_sample),
                 key=lambda f: f.value, reverse=True)
    top = yoy[0]
    return {
        "TOP_YOY": top.id,
        "TOP_PRICE": top.id.replace("median_yoy_pct", "median_price"),
        "suburb_top": top.label.split(":")[0],
        "suburb_top_name": top.label.split(":")[0].rsplit(" ", 1)[0],
    }


def render_case(case: dict, pack: insights.FactPack) -> dict:
    alias = _resolve(pack)
    facts = pack.by_id()

    def fid(x: str) -> str:
        return alias.get(x, x)

    def sub(m: re.Match) -> str:
        kind, *ids = m.group(1).split(":")
        if kind in alias and not ids:
            return alias[kind]
        vals = [facts[fid(i)].value for i in ids]
        return {
            "money": lambda: insights._money(vals[0]),
            "pct1": lambda: f"{vals[0]:.1f}",
            "pct2": lambda: f"{vals[0]:.2f}",
            "int": lambda: f"{vals[0]:,.0f}",
            "diff": lambda: f"{vals[0] - vals[1]:.2f}",
        }[kind]()

    text = re.sub(r"\{([^}]+)\}", sub, case["text"])
    return {"text": text, "fact_ids": [fid(i) for i in case["fact_ids"]]}


def run_checker_suite(pack: insights.FactPack) -> tuple[int, int, list[str]]:
    cases = yaml.safe_load((HERE / "cases.yaml").read_text())["cases"]
    passed, lines = 0, []
    for case in cases:
        finding = render_case(case, pack)
        problems = insights.check_brief({"headline": "x", "findings": [finding]}, pack)
        verdict = "fail" if problems else "pass"
        ok = verdict == case["expect"]
        passed += ok
        lines.append(f"[{'OK ' if ok else 'BAD'}] {case['id']:<32} expected {case['expect']:<4} got {verdict}"
                     + (f"  ({problems[0]})" if problems and not ok else ""))
    return passed, len(cases), lines


def run_live_suite(pack: insights.FactPack, n: int) -> tuple[int, list[dict]]:
    grounded, runs = 0, []
    for i in range(n):
        brief = insights.brief_with_claude(pack)
        problems = insights.check_brief(brief, pack)
        grounded += not problems
        runs.append({"run": i + 1, "grounded": not problems, "problems": problems})
    return grounded, runs


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--live", type=int, default=0, help="Number of live Claude runs")
    args = p.parse_args(argv)
    pack = insights.build_facts()

    passed, total, lines = run_checker_suite(pack)
    print("Checker suite\n" + "\n".join(lines) + f"\n{passed}/{total} cases behaved as expected\n")
    exit_code = 0 if passed == total else 1

    offline = insights.check_brief(insights.brief_offline(pack), pack)
    print(f"Offline template brief: {'grounded' if not offline else 'NOT grounded: ' + '; '.join(offline)}")
    exit_code |= bool(offline)

    if args.live:
        if not os.getenv("ANTHROPIC_API_KEY"):
            print("Skipping live suite: ANTHROPIC_API_KEY not set", file=sys.stderr)
        else:
            grounded, runs = run_live_suite(pack, args.live)
            print(f"Live suite ({insights.MODEL}): {grounded}/{args.live} briefs fully grounded")
            out = insights.REPORTS / "eval_live_results.json"
            out.parent.mkdir(exist_ok=True)
            out.write_text(json.dumps(runs, indent=2))
            print(f"Details: {out.relative_to(insights.config.ROOT)}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
