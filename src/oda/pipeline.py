"""Build the DuckDB warehouse: load raw files, then run every SQL model in filename order.

    python -m oda.pipeline            # sample data (default)
    DATA_MODE=real python -m oda.pipeline
"""

from __future__ import annotations

import re
import time
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import pandas as pd

from oda import config
from oda.parse_nsw import parse_dir

QUARTER_COL = re.compile(r"^\s*(\d{4})\s*Q([1-4])\s*$", re.IGNORECASE)
DFT_ALIASES = {"bodytype": "body_type", "genmodel": "gen_model", "make": "make", "model": "model", "fuel": "fuel"}


def load_dft_long(csv_path: Path) -> pd.DataFrame:
    """Read the wide DfT file (one column per quarter) and unpivot it to one row per quarter."""
    wide = pd.read_csv(csv_path, dtype=str, keep_default_na=False)
    quarter_cols = [c for c in wide.columns if QUARTER_COL.match(c)]
    if not quarter_cols:
        raise ValueError(f"No 'YYYY Qn' columns found in {csv_path.name}; DfT may have changed the layout.")
    id_cols = [c for c in wide.columns if c not in quarter_cols]
    renamed = {c: DFT_ALIASES.get(re.sub(r"[^a-z]", "", c.lower()), re.sub(r"\W+", "_", c.strip().lower())) for c in id_cols}
    long = wide.melt(id_vars=id_cols, value_vars=quarter_cols, var_name="quarter_label", value_name="units_raw")
    long = long.rename(columns=renamed)
    for col in ("body_type", "make", "gen_model", "model", "fuel"):
        if col not in long.columns:
            long[col] = ""
    return long[["body_type", "make", "gen_model", "model", "fuel", "quarter_label", "units_raw"]]


def model_files() -> list[Path]:
    return sorted(config.MODELS.rglob("*.sql"), key=lambda p: p.name)


def build(db_path: Path | None = None, verbose: bool = True) -> Path:
    db_path = Path(db_path or config.WAREHOUSE)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    src = config.raw_dir()
    t0 = time.perf_counter()
    nsw = parse_dir(src / "nsw")
    dft = load_dft_long(src / "dft" / "df_VEH0160_UK.csv")
    con = duckdb.connect(str(db_path))
    try:
        con.register("nsw_df", nsw)
        con.execute("create table raw_nsw_sales as select * from nsw_df")
        con.register("dft_df", dft)
        con.execute("create table raw_dft_veh0160 as select * from dft_df")
        for sql_file in model_files():
            con.execute(sql_file.read_text())
            if verbose:
                name = sql_file.stem.split("_", 1)[1]
                n = con.execute(f"select count(*) from {name}").fetchone()[0]
                print(f"  built {name:<34} {n:>9,} rows")
        con.execute(
            "create or replace table _build_meta as select ? as data_mode, ? as built_at_utc, ? as source_dir",
            [config.DATA_MODE, datetime.now(timezone.utc).isoformat(timespec="seconds"), str(src)],
        )
    finally:
        con.close()
    if verbose:
        print(f"Warehouse {db_path.name} built from {config.DATA_MODE} data in {time.perf_counter() - t0:.1f}s")
    return db_path


def export_marts(db_path: Path | None = None, out_dir: Path | None = None) -> list[Path]:
    """Write every mart_* table to CSV for Power BI or Excel."""
    db_path = Path(db_path or config.WAREHOUSE)
    out_dir = Path(out_dir or config.DATA / f"marts_{config.DATA_MODE}")
    out_dir.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db_path), read_only=True)
    paths = []
    try:
        for (table,) in con.execute("select table_name from information_schema.tables where table_name like 'mart_%'").fetchall():
            path = out_dir / f"{table}.csv"
            con.execute(f"copy {table} to '{path.as_posix()}' (header, delimiter ',')")
            paths.append(path)
    finally:
        con.close()
    return paths


if __name__ == "__main__":
    build()
    for p in export_marts():
        print(f"  exported {p.relative_to(config.ROOT)}")
