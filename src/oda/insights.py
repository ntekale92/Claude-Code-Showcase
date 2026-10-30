"""Write a plain-English market brief with Claude, grounded in numbers the warehouse computed.

Design (see docs/adr/0002-claude-writes-words-not-numbers.md):
  1. SQL computes every number and gives it a stable fact id.
  2. Claude only writes sentences, and must cite the fact ids each sentence relies on
     (forced tool call -> structured JSON, no free-text parsing).
  3. A deterministic checker rejects the brief if any number in the text doesn't match a cited fact.

    python -m oda.insights             # uses Claude if ANTHROPIC_API_KEY is set, else the offline template
    python -m oda.insights --offline   # never calls the API
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import duckdb

from oda import config

MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5")
REPORTS = config.ROOT / "reports"

SYSTEM_PROMPT = """You write short market briefs for a data team's stakeholders.

Rules you must follow:
- Use ONLY the facts provided. Every number you write must come from a fact you cite in fact_ids.
- Write numbers the way the fact gives them (you may round dollars to the nearest $1,000 or write $1.25m).
- Never compute new numbers (no differences, sums or averages of facts).
- If a fact has low_sample = true, say the sample is small, or leave it out.
- Describe what happened. Do not give investment, buying or selling advice.
- Australian English. Plain words. No hype.
"""

BRIEF_TOOL = {
    "name": "submit_brief",
    "description": "Submit the finished brief. Every finding must cite the fact ids it uses.",
    "input_schema": {
        "type": "object",
        "properties": {
            "headline": {"type": "string", "description": "One sentence, under 25 words."},
            "findings": {
                "type": "array",
                "minItems": 3,
                "maxItems": 6,
                "items": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string"},
                        "fact_ids": {"type": "array", "items": {"type": "string"}, "minItems": 1},
                    },
                    "required": ["text", "fact_ids"],
                },
            },
            "caveats": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["headline", "findings", "caveats"],
    },
}


@dataclass
class Fact:
    id: str
    label: str
    value: float
    unit: str  # 'aud', 'pct', 'count', 'units'
    low_sample: bool = False


@dataclass
class FactPack:
    property_quarter: str
    car_quarter: str
    data_mode: str
    facts: list[Fact] = field(default_factory=list)

    def by_id(self) -> dict[str, Fact]:
        return {f.id: f for f in self.facts}

    def to_prompt_json(self) -> str:
        return json.dumps(
            {"property_quarter": self.property_quarter, "car_quarter": self.car_quarter,
             "facts": [f.__dict__ for f in self.facts]},
            indent=1,
        )


# ------------------------------------------------------------------------------------------
# 1. Facts: every number comes from SQL
# ------------------------------------------------------------------------------------------
def build_facts(db_path: Path | None = None) -> FactPack:
    con = duckdb.connect(str(db_path or config.WAREHOUSE), read_only=True)
    try:
        mode = con.execute("select data_mode from _build_meta").fetchone()[0]
        pq = con.execute(
            "select max(quarter_start), any_value(quarter_label order by quarter_start desc) "
            "from mart_suburb_quarterly where is_complete_quarter"
        ).fetchone()
        cq = con.execute(
            "select max(quarter_start), any_value(quarter_label order by quarter_start desc) from mart_fuel_mix_quarterly"
        ).fetchone()
        pack = FactPack(property_quarter=pq[1], car_quarter=cq[1], data_mode=mode)

        rows = con.execute(
            """select suburb, dwelling_type, median_price, median_price_yoy_pct, sales_count, low_sample
               from mart_suburb_quarterly where quarter_start = ? order by suburb, dwelling_type""",
            [pq[0]],
        ).fetchall()
        for suburb, dtype, med, yoy, n, low in rows:
            key = f"nsw.{suburb.lower().replace(' ', '_')}.{dtype.lower()}"
            name = f"{suburb.title()} {dtype.lower()}s"
            pack.facts.append(Fact(f"{key}.median_price", f"{name}: median sale price, {pq[1]}", float(med), "aud", low))
            pack.facts.append(Fact(f"{key}.sales_count", f"{name}: sales, {pq[1]}", float(n), "count", low))
            if yoy is not None:
                pack.facts.append(Fact(f"{key}.median_yoy_pct", f"{name}: median price change vs a year earlier, %",
                                       float(yoy), "pct", low))

        for fuel, share, units, yoy in con.execute(
            "select fuel_group, share_pct, units, units_yoy_pct from mart_fuel_mix_quarterly where quarter_start = ?",
            [cq[0]],
        ).fetchall():
            key = f"uk.fuel.{fuel.lower()}"
            pack.facts.append(Fact(f"{key}.share_pct", f"UK new cars: {fuel} share of registrations, {cq[1]}, %", float(share), "pct"))
            pack.facts.append(Fact(f"{key}.units", f"UK new cars: {fuel} registrations, {cq[1]}", float(units), "units"))
            if yoy is not None:
                pack.facts.append(Fact(f"{key}.units_yoy_pct", f"UK new cars: {fuel} registrations change vs a year earlier, %",
                                       float(yoy), "pct"))
        prior = con.execute(
            "select share_pct from mart_fuel_mix_quarterly where fuel_group = 'BEV' and quarter_start = (?::date - interval 1 year)",
            [cq[0]],
        ).fetchone()
        if prior:
            pack.facts.append(Fact("uk.fuel.bev.share_pct_prior_year", "UK new cars: BEV share a year earlier, %",
                                   float(prior[0]), "pct"))

        for make, share, rank, bev_mix in con.execute(
            """select make, market_share_pct, rank_in_quarter, bev_mix_pct from mart_make_quarterly
               where quarter_start = ? and rank_in_quarter <= 5 order by rank_in_quarter""",
            [cq[0]],
        ).fetchall():
            key = f"uk.make.{make.lower().replace(' ', '_')}"
            pack.facts.append(Fact(f"{key}.share_pct", f"UK new cars: {make.title()} market share, {cq[1]}, % (rank {rank})",
                                   float(share), "pct"))
            pack.facts.append(Fact(f"{key}.bev_mix_pct", f"UK new cars: share of {make.title()} registrations that are BEV, %",
                                   float(bev_mix), "pct"))
        return pack
    finally:
        con.close()


# ------------------------------------------------------------------------------------------
# 2. Writing: Claude (forced tool call) or the offline template
# ------------------------------------------------------------------------------------------
def brief_with_claude(pack: FactPack, client=None) -> dict:
    import anthropic  # imported lazily so offline runs and tests don't need a key

    client = client or anthropic.Anthropic()
    resp = client.messages.create(
        model=MODEL,
        max_tokens=2000,
        # the rules are identical every run, so cache them; the facts change every build
        system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
        tools=[BRIEF_TOOL],
        tool_choice={"type": "tool", "name": "submit_brief"},
        messages=[{
            "role": "user",
            "content": (
                f"Data mode: {pack.data_mode}. Write the brief for NSW property ({pack.property_quarter}) "
                f"and UK new cars ({pack.car_quarter}).\n\nFacts:\n{pack.to_prompt_json()}"
            ),
        }],
    )
    for block in resp.content:
        if block.type == "tool_use" and block.name == "submit_brief":
            return block.input
    raise RuntimeError("Claude did not return a submit_brief tool call")


def _money(v: float) -> str:
    return f"${v / 1e6:.2f}m" if v >= 1e6 else f"${v:,.0f}"


def brief_offline(pack: FactPack) -> dict:
    """Deterministic template, used without an API key and as the eval baseline."""
    f = pack.by_id()
    yoy = [x for x in pack.facts if x.id.endswith("median_yoy_pct") and not x.low_sample]
    yoy.sort(key=lambda x: x.value, reverse=True)
    findings = []
    if yoy:
        top, low = yoy[0], yoy[-1]
        top_price = f[top.id.replace("median_yoy_pct", "median_price")]
        findings.append({"text": f"{top.label.split(':')[0]} had the biggest annual rise in median price, "
                                 f"up {top.value:.1f}% to {_money(top_price.value)} in {pack.property_quarter}.",
                         "fact_ids": [top.id, top_price.id]})
        findings.append({"text": f"{low.label.split(':')[0]} had the weakest change at {low.value:.1f}%.",
                         "fact_ids": [low.id]})
    if "uk.fuel.bev.share_pct" in f:
        ids = ["uk.fuel.bev.share_pct"]
        text = f"Battery electric cars were {f['uk.fuel.bev.share_pct'].value:.2f}% of UK new-car registrations in {pack.car_quarter}"
        if "uk.fuel.bev.share_pct_prior_year" in f:
            text += f", compared with {f['uk.fuel.bev.share_pct_prior_year'].value:.2f}% a year earlier"
            ids.append("uk.fuel.bev.share_pct_prior_year")
        findings.append({"text": text + ".", "fact_ids": ids})
    leader = next((x for x in pack.facts if x.id.startswith("uk.make.") and x.id.endswith(".share_pct")), None)
    if leader:
        mix = f[leader.id.replace("share_pct", "bev_mix_pct")]
        findings.append({"text": f"{leader.label.split(':')[1].split(' market')[0].strip()} led with a "
                                 f"{leader.value:.2f}% market share; {mix.value:.1f}% of its registrations were BEV.",
                         "fact_ids": [leader.id, mix.id]})
    caveats = ["Suburb medians with fewer than 10 sales are flagged low-sample and left out of the rankings.",
               f"Property figures cover contracts in {pack.property_quarter}, the latest quarter past the 90-day reporting lag."]
    if pack.data_mode != "real":
        caveats.insert(0, "SAMPLE DATA: these numbers are synthetic and only demonstrate the pipeline.")
    return {"headline": f"{pack.property_quarter} NSW property and {pack.car_quarter} UK new-car snapshot",
            "findings": findings, "caveats": caveats}


# ------------------------------------------------------------------------------------------
# 3. Grounding check: deterministic, no model involved
# ------------------------------------------------------------------------------------------
_QUARTER = re.compile(r"\b(19|20)\d{2}\s*Q[1-4]\b", re.IGNORECASE)
_YEAR = re.compile(r"\b(19|20)\d{2}\b")
_NUM = re.compile(r"(?<![\w.])-?\$?\d[\d,]*(?:\.\d+)?\s*(?:m\b|k\b|million\b)?", re.IGNORECASE)
ADVICE = re.compile(r"\b(should (buy|sell|invest)|good time to (buy|sell)|buy now|we recommend (buying|selling))\b", re.I)


def _parse_number(tok: str) -> float:
    t = tok.lower().replace("$", "").replace(",", "").strip()
    mult = 1.0
    for suffix, m in (("million", 1e6), ("m", 1e6), ("k", 1e3)):
        if t.endswith(suffix):
            t, mult = t[: -len(suffix)].strip(), m
            break
    return float(t) * mult


def _decimals(tok: str) -> int:
    core = re.sub(r"[^\d.]", "", tok)
    return len(core.split(".", 1)[1]) if "." in core else 0


def _matches(n: float, fact: Fact, decimals: int = 0) -> bool:
    v = fact.value
    if fact.unit == "pct":
        # precision-aware: '27.0' must equal the fact rounded to 1 dp, '26.99' to 2 dp.
        # A loose tolerance let 26.99 match an unrelated 27.0 fact (caught by evals/cases.yaml).
        # Sign is ignored so 'fell 6.3%' can quote a -6.3 fact.
        return abs(abs(n) - abs(round(v, decimals))) < 1e-9
    if fact.unit == "aud":
        return abs(n - v) <= max(0.006 * v, 1000)  # allows $1.25m or nearest $1,000
    return abs(n - v) <= max(0.005 * v, 0.5)


def check_brief(brief: dict, pack: FactPack) -> list[str]:
    """Return a list of problems. Empty list = grounded."""
    problems: list[str] = []
    facts = pack.by_id()
    for i, item in enumerate(brief.get("findings", []), 1):
        cited = [facts.get(fid) for fid in item.get("fact_ids", [])]
        unknown = [fid for fid, fobj in zip(item.get("fact_ids", []), cited) if fobj is None]
        if unknown:
            problems.append(f"finding {i}: cites unknown fact ids {unknown}")
        cited = [c for c in cited if c]
        if not cited:
            problems.append(f"finding {i}: cites no valid facts")
        text = _QUARTER.sub("", item["text"])
        text = _YEAR.sub("", text)
        for tok in _NUM.findall(text):
            n = _parse_number(tok)
            if not any(_matches(n, c, _decimals(tok)) for c in cited):
                problems.append(f"finding {i}: number '{tok.strip()}' doesn't match any cited fact")
        if any(c.low_sample for c in cited) and "sample" not in item["text"].lower():
            problems.append(f"finding {i}: uses a low-sample fact without saying so")
        if ADVICE.search(item["text"]):
            problems.append(f"finding {i}: reads as investment advice")
    if ADVICE.search(brief.get("headline", "")):
        problems.append("headline reads as investment advice")
    return problems


def render_markdown(brief: dict, pack: FactPack, source: str) -> str:
    facts = pack.by_id()
    lines = [f"# {brief['headline']}", "", f"_Written by {source}; every number checked against the warehouse._", ""]
    refs: list[str] = []
    for item in brief["findings"]:
        marks = []
        for fid in item["fact_ids"]:
            if fid not in refs:
                refs.append(fid)
            marks.append(f"[{refs.index(fid) + 1}]")
        lines.append(f"- {item['text']} {''.join(marks)}")
    if brief.get("caveats"):
        lines += ["", "**Caveats**", ""] + [f"- {c}" for c in brief["caveats"]]
    lines += ["", "**Facts cited**", ""]
    for i, fid in enumerate(refs, 1):
        f = facts.get(fid)
        if f:
            lines.append(f"{i}. `{fid}` — {f.label}: {f.value:,.2f}{' (low sample)' if f.low_sample else ''}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--offline", action="store_true", help="Use the template, never call the API")
    args = p.parse_args(argv)
    pack = build_facts()
    use_claude = not args.offline and bool(os.getenv("ANTHROPIC_API_KEY"))
    brief = brief_with_claude(pack) if use_claude else brief_offline(pack)
    source = f"Claude ({MODEL})" if use_claude else "offline template"
    problems = check_brief(brief, pack)
    REPORTS.mkdir(exist_ok=True)
    out = REPORTS / f"insight_brief_{pack.data_mode}.md"
    out.write_text(render_markdown(brief, pack, source))
    print(f"Wrote {out.relative_to(config.ROOT)} ({source})")
    if problems:
        print("Grounding check FAILED:\n  " + "\n  ".join(problems), file=sys.stderr)
        return 1
    print("Grounding check passed: every number traces to a cited fact.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
