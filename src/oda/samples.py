"""Generate SYNTHETIC sample files that match the real file layouts exactly.

These exist so tests and CI run without downloading anything. Every number in them is invented.
They also contain deliberate data-quality problems (zero prices, duplicates, bad dates,
suppressed counts) so the quality checks have something to catch.

    python -m oda.samples
"""

from __future__ import annotations

import csv
from datetime import date, timedelta
from pathlib import Path

import numpy as np

from oda import config

SEED = 20261030

# suburb, postcode, district code, base house price, base unit price, weekly sales (house, unit)
SUBURBS = [
    ("PARRAMATTA", "2150", "241", 1_250_000, 640_000, (3, 9)),
    ("PENRITH", "2750", "199", 880_000, 520_000, (6, 3)),
    ("NEWCASTLE", "2300", "171", 1_050_000, 720_000, (3, 5)),
    ("WOLLONGONG", "2500", "267", 1_120_000, 690_000, (4, 4)),
    ("CHATSWOOD", "2067", "253", 2_900_000, 1_050_000, (2, 6)),
    ("BLACKTOWN", "2148", "045", 960_000, 560_000, (7, 3)),
    ("BONDI", "2026", "263", 3_600_000, 1_350_000, (1, 5)),
    ("ORANGE", "2800", "185", 690_000, 420_000, (4, 1)),
    ("DUBBO", "2830", "081", 560_000, 360_000, (4, 1)),
    ("LIVERPOOL", "2170", "145", 1_000_000, 530_000, (5, 4)),
]
STREETS = ["GEORGE ST", "CHURCH ST", "MAIN RD", "STATION ST", "PARK AVE", "HIGH ST", "VICTORIA RD", "KING ST"]

FIRST_WEEK = date(2023, 1, 2)
LAST_WEEK = date(2026, 10, 5)


def _nsw_weeks() -> list[date]:
    weeks, d = [], FIRST_WEEK
    while d <= LAST_WEEK:
        weeks.append(d)
        d += timedelta(days=7)
    return weeks


def write_nsw_samples(dest: Path, rng: np.random.Generator) -> int:
    dest.mkdir(parents=True, exist_ok=True)
    for old in dest.glob("*.DAT"):
        old.unlink()
    weeks = _nsw_weeks()
    total = 0
    prop_id = 4_000_000
    for i, wk in enumerate(weeks):
        years = (wk - FIRST_WEEK).days / 365.25
        # gentle market cycle: dip through 2023, recovery 2024-26, seasonal spring lift
        trend = 1 + 0.045 * years - 0.03 * np.sin(years * np.pi) + 0.02 * np.sin(2 * np.pi * (wk.month - 3) / 12)
        lines = [f"A;RTSALEDATA;001;{wk:%Y%m%d} 01:02;VALUER GENERAL;"]
        rows_this_week = 0
        for suburb, pc, district, house_base, unit_base, (n_house, n_unit) in SUBURBS:
            for is_unit, base, n in ((False, house_base, n_house), (True, unit_base, n_unit)):
                for _ in range(rng.poisson(n)):
                    prop_id += 1
                    contract = wk - timedelta(days=int(rng.integers(30, 75)))
                    settle = contract + timedelta(days=int(rng.integers(28, 60)))
                    price = int(round(base * trend * rng.lognormal(0, 0.22), -3))
                    area = round(float(rng.normal(110 if is_unit else 560, 25 if is_unit else 140)), 1)
                    unit_no = str(rng.integers(1, 40)) if is_unit else ""
                    fields = [
                        "B", district, str(prop_id), "1", f"{wk:%Y%m%d} 01:02", "", unit_no,
                        str(rng.integers(1, 300)), STREETS[int(rng.integers(len(STREETS)))], suburb, pc,
                        str(abs(area)), "M", f"{contract:%Y%m%d}", f"{settle:%Y%m%d}", str(price),
                        "R2", "R" if rng.random() > 0.03 else "V", "RESIDENCE",
                        unit_no, "R", "", "", f"AT{rng.integers(100000, 999999)}",
                    ]
                    lines.append(";".join(fields) + ";")
                    lines.append(f"C;{district};{prop_id};1;{wk:%Y%m%d} 01:02;LOT {rng.integers(1, 99)} DP{rng.integers(10000, 99999)};")
                    rows_this_week += 1
        # deliberate quality issues, a few per quarter
        if i % 13 == 5:  # zero-price (non-arm's-length style) sale
            lines.append(f"B;199;{prop_id + 1};1;{wk:%Y%m%d} 01:02;;;12;HIGH ST;PENRITH;2750;600;M;"
                         f"{wk - timedelta(days=40):%Y%m%d};{wk - timedelta(days=5):%Y%m%d};0;R2;R;RESIDENCE;;R;;;AT000001;")
            prop_id += 1
        if i % 17 == 3:  # exact duplicate of the last sale line
            last_b = next(l for l in reversed(lines) if l.startswith("B;"))
            lines.append(last_b)
        if i % 29 == 11:  # settlement before contract
            lines.append(f"B;145;{prop_id + 1};1;{wk:%Y%m%d} 01:02;;;8;KING ST;LIVERPOOL;2170;450;M;"
                         f"{wk - timedelta(days=10):%Y%m%d};{wk - timedelta(days=60):%Y%m%d};990000;R2;R;RESIDENCE;;R;;;AT000002;")
            prop_id += 1
        lines.append(f"Z;{rows_this_week};")
        (dest / f"001_SALES_DATA_NNME_{wk:%Y%m%d}.DAT").write_text("\n".join(lines) + "\n", encoding="latin-1")
        total += rows_this_week
    return total


# make, generic model, base quarterly units, fuel mix (petrol, diesel, hybrid, plug-in, battery electric)
CAR_LINES = [
    ("TOYOTA", "TOYOTA YARIS", 9_000, (0.15, 0.0, 0.85, 0.0, 0.0)),
    ("TOYOTA", "TOYOTA C-HR", 5_500, (0.05, 0.0, 0.80, 0.15, 0.0)),
    ("FORD", "FORD PUMA", 11_000, (0.70, 0.0, 0.25, 0.0, 0.05)),
    ("KIA", "KIA SPORTAGE", 9_500, (0.30, 0.05, 0.40, 0.25, 0.0)),
    ("KIA", "KIA EV3", 2_000, (0.0, 0.0, 0.0, 0.0, 1.0)),
    ("TESLA", "TESLA MODEL Y", 7_000, (0.0, 0.0, 0.0, 0.0, 1.0)),
    ("BYD", "BYD SEAL U", 1_500, (0.0, 0.0, 0.0, 0.6, 0.4)),
    ("VOLKSWAGEN", "VOLKSWAGEN GOLF", 7_500, (0.55, 0.10, 0.20, 0.10, 0.05)),
    ("NISSAN", "NISSAN QASHQAI", 10_000, (0.40, 0.0, 0.60, 0.0, 0.0)),
    ("MG", "MG HS", 4_000, (0.50, 0.0, 0.25, 0.25, 0.0)),
]
FUELS = ["PETROL", "DIESEL", "HYBRID ELECTRIC (PETROL)", "PLUG-IN HYBRID ELECTRIC (PETROL)", "BATTERY ELECTRIC"]


def _quarters() -> list[str]:
    qs = [f"{y} Q{q}" for y in range(2022, 2027) for q in range(1, 5)]
    return [q for q in qs if q <= "2026 Q2"]


def write_dft_sample(dest: Path, rng: np.random.Generator) -> int:
    dest.mkdir(parents=True, exist_ok=True)
    quarters = _quarters()
    header = ["BodyType", "Make", "GenModel", "Model", "Fuel"] + list(reversed(quarters))  # newest first, like DfT
    rows = []
    for make, gen, base, mix in CAR_LINES:
        for fuel, share in zip(FUELS, mix):
            if share == 0:
                continue
            row = ["Cars", make, gen, gen.replace(make + " ", "") + " BASE", fuel]
            vals = []
            for qi, q in enumerate(quarters):
                ev_lift = 1 + (0.06 * qi if fuel == "BATTERY ELECTRIC" else -0.012 * qi if fuel == "PETROL" else 0.01 * qi)
                seasonal = 1.35 if q.endswith(("Q1", "Q3")) else 0.85  # UK plate-change months lift Q1/Q3
                v = int(base * share * max(ev_lift, 0.2) * seasonal * rng.lognormal(0, 0.08))
                vals.append("[c]" if v < 5 else str(v))
            row += list(reversed(vals))
            rows.append(row)
    # one suppressed line and one non-car body type, as in the real file
    rows.append(["Cars", "MORGAN", "MORGAN PLUS FOUR", "PLUS FOUR", "PETROL"] + ["[c]"] * len(quarters))
    rows.append(["Motorcycles", "HONDA", "HONDA CB", "CB125F", "PETROL"] + [str(int(rng.integers(300, 900))) for _ in quarters])
    with (dest / "df_VEH0160_UK.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)
    return len(rows)


def main() -> None:
    rng = np.random.default_rng(SEED)
    n_sales = write_nsw_samples(config.DATA / "sample" / "nsw", rng)
    n_rows = write_dft_sample(config.DATA / "sample" / "dft", rng)
    print(f"Wrote {n_sales:,} synthetic NSW sales and {n_rows} synthetic DfT rows into data/sample/")


if __name__ == "__main__":
    main()
