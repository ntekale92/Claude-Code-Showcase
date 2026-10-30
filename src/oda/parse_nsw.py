"""Parse NSW Valuer General .DAT files into one flat table of 'B' (sale) records.

The files are semicolon delimited with mixed record types on each line:
A = header, B = sale, C = legal description, D = purchaser/vendor, Z = trailer.
Only B records are kept. Fields beyond the documented 24 are ignored so a format tweak
does not shift every column.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from oda.config import NSW_B_FIELDS


def parse_dat_file(path: Path) -> list[list[str]]:
    rows: list[list[str]] = []
    with path.open("r", encoding="latin-1") as fh:  # source files are not guaranteed UTF-8
        for line in fh:
            if not line.startswith("B;"):
                continue
            parts = line.rstrip("\r\n").split(";")
            parts = (parts + [""] * len(NSW_B_FIELDS))[: len(NSW_B_FIELDS)]
            rows.append(parts)
    return rows


def parse_dir(folder: Path) -> pd.DataFrame:
    files = sorted(p for p in folder.rglob("*") if p.suffix.lower() == ".dat")
    if not files:
        raise FileNotFoundError(f"No .DAT files in {folder}. Run `python -m oda.fetch` or use DATA_MODE=sample.")
    frames = []
    for f in files:
        rows = parse_dat_file(f)
        if rows:
            df = pd.DataFrame(rows, columns=NSW_B_FIELDS, dtype="string")
            df["source_file"] = f.name
            frames.append(df)
    return pd.concat(frames, ignore_index=True)
