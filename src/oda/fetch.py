"""Download the real open data into data/raw/ (gitignored). Run this on your own machine.

    python -m oda.fetch --nsw-years 2024 2025 2026 --dft

NSW yearly archives contain one zip per week, each holding .DAT files, so extraction is recursive.
"""

from __future__ import annotations

import argparse
import io
import sys
import urllib.request
import zipfile
from pathlib import Path

from oda import config

USER_AGENT = "open-data-analytics-claude/0.1 (portfolio project; non-commercial)"


def _download(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=300) as resp:  # noqa: S310 - fixed, documented sources
        return resp.read()


def _extract_dat_files(blob: bytes, dest: Path) -> int:
    """Extract every .DAT file from a zip, descending into nested zips. Returns files written."""
    written = 0
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        for name in zf.namelist():
            lower = name.lower()
            if lower.endswith(".zip"):
                written += _extract_dat_files(zf.read(name), dest)
            elif lower.endswith(".dat"):
                target = dest / Path(name).name
                target.write_bytes(zf.read(name))
                written += 1
    return written


def fetch_nsw(years: list[int], weekly: list[str]) -> None:
    dest = config.DATA / "raw" / "nsw"
    dest.mkdir(parents=True, exist_ok=True)
    for year in years:
        url = config.NSW_PSI_YEARLY_URL.format(year=year)
        print(f"NSW {year}: {url}")
        n = _extract_dat_files(_download(url), dest)
        print(f"  extracted {n} .DAT files")
    for day in weekly:
        url = config.NSW_PSI_WEEKLY_URL.format(yyyymmdd=day)
        print(f"NSW week {day}: {url}")
        n = _extract_dat_files(_download(url), dest)
        print(f"  extracted {n} .DAT files")


def fetch_dft() -> None:
    dest = config.DATA / "raw" / "dft"
    dest.mkdir(parents=True, exist_ok=True)
    print(f"DfT VEH0160: {config.DFT_VEH0160_URL}")
    (dest / "df_VEH0160_UK.csv").write_bytes(_download(config.DFT_VEH0160_URL))
    print("  saved df_VEH0160_UK.csv")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--nsw-years", type=int, nargs="*", default=[], help="Yearly NSW archives, e.g. 2024 2025")
    p.add_argument("--nsw-weeks", nargs="*", default=[], help="Weekly NSW files for the current year, YYYYMMDD")
    p.add_argument("--dft", action="store_true", help="Download the UK DfT VEH0160 file")
    args = p.parse_args(argv)
    if not (args.nsw_years or args.nsw_weeks or args.dft):
        p.error("nothing to fetch: pass --nsw-years, --nsw-weeks and/or --dft")
    try:
        if args.nsw_years or args.nsw_weeks:
            fetch_nsw(args.nsw_years, args.nsw_weeks)
        if args.dft:
            fetch_dft()
    except Exception as exc:  # surface a plain message; URLs occasionally move
        print(f"Download failed: {exc}\nCheck the source URL in src/oda/config.py or override it with "
              "NSW_PSI_YEARLY_URL / NSW_PSI_WEEKLY_URL / DFT_VEH0160_URL.", file=sys.stderr)
        return 1
    print("Done. Now run: DATA_MODE=real make build")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
