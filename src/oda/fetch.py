"""Download the real open data into data/raw/ (gitignored). Run this on your own machine.

    python -m oda.fetch --nsw-years 2024 2025 --dft
    python -m oda.fetch --nsw-weeks 20261026 --dft      # weekly files for the current year
    python -m oda.fetch --nsw-local                     # zips you downloaded by hand (see below)

NSW yearly archives contain one zip per week, each holding .DAT files, so extraction is recursive.

If an NSW download fails (the Valuer General has moved its site before), download the zips
yourself from the property sales portal into data/raw/nsw_downloads/ and run with --nsw-local.
Every run also extracts any zips already in that folder, so mixing both routes is fine.
"""

from __future__ import annotations

import argparse
import io
import sys
import urllib.error
import urllib.request
import zipfile
from datetime import date, timedelta
from pathlib import Path

from oda import config

USER_AGENT = "open-data-analytics-claude/0.1 (portfolio project; non-commercial)"
PORTAL = "https://valuation.property.nsw.gov.au/embed/propertySalesInformation"


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
                (dest / Path(name).name).write_bytes(zf.read(name))
                written += 1
    return written


def extract_local_zips(src: Path, dest: Path) -> int:
    """Extract .DAT files from every zip the user saved into `src` (and loose .DAT files)."""
    if not src.exists():
        return 0
    dest.mkdir(parents=True, exist_ok=True)
    total = 0
    for f in sorted(src.iterdir()):
        if f.suffix.lower() == ".zip":
            try:
                n = _extract_dat_files(f.read_bytes(), dest)
            except zipfile.BadZipFile:
                print(f"  skipped {f.name}: not a valid zip (re-download it)")
                continue
            print(f"  {f.name}: {n} .DAT files")
            total += n
        elif f.suffix.lower() == ".dat":
            (dest / f.name).write_bytes(f.read_bytes())
            total += 1
    return total


def fetch_nsw(years: list[int], weekly: list[str], dest: Path) -> list[str]:
    """Try each requested NSW file; keep going past failures and return what failed."""
    dest.mkdir(parents=True, exist_ok=True)
    jobs = [(f"NSW {y}", config.NSW_PSI_YEARLY_URL.format(year=y)) for y in years]
    jobs += [(f"NSW week {d}", config.NSW_PSI_WEEKLY_URL.format(yyyymmdd=d)) for d in weekly]
    failed = []
    for label, url in jobs:
        print(f"{label}: {url}")
        try:
            n = _extract_dat_files(_download(url), dest)
            print(f"  extracted {n} .DAT files")
        except (urllib.error.URLError, zipfile.BadZipFile, TimeoutError, OSError) as exc:
            reason = getattr(exc, "code", None) or getattr(exc, "reason", None) or exc
            print(f"  FAILED ({reason})")
            failed.append(label)
    return failed


def mondays_this_year(today: date | None = None) -> list[str]:
    today = today or date.today()
    d = date(today.year, 1, 1)
    d += timedelta(days=(7 - d.weekday()) % 7)
    out = []
    while d <= today:
        out.append(d.strftime("%Y%m%d"))
        d += timedelta(days=7)
    return out


def fetch_dft(dest: Path) -> bool:
    dest.mkdir(parents=True, exist_ok=True)
    print(f"DfT VEH0160: {config.DFT_VEH0160_URL}")
    try:
        (dest / "df_VEH0160_UK.csv").write_bytes(_download(config.DFT_VEH0160_URL))
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        print(f"  FAILED ({getattr(exc, 'code', None) or exc})")
        return False
    print("  saved df_VEH0160_UK.csv")
    return True


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--nsw-years", type=int, nargs="*", default=[], help="Yearly NSW archives, e.g. 2024 2025")
    p.add_argument("--nsw-weeks", nargs="*", default=[], help="Weekly NSW files for the current year, YYYYMMDD")
    p.add_argument("--nsw-this-year", action="store_true",
                   help="Try the weekly file for every Monday so far this year (missing weeks are skipped)")
    p.add_argument("--nsw-local", action="store_true", help=f"Only extract zips saved in {config.NSW_MANUAL_DIR}")
    p.add_argument("--dft", action="store_true", help="Download the UK DfT VEH0160 file")
    args = p.parse_args(argv)
    if args.nsw_this_year:
        args.nsw_weeks = list(args.nsw_weeks) + mondays_this_year()
    if not (args.nsw_years or args.nsw_weeks or args.nsw_local or args.dft):
        p.error("nothing to fetch: pass --nsw-years, --nsw-weeks, --nsw-local and/or --dft")

    nsw_dest = config.DATA / "raw" / "nsw"
    problems = []
    if args.nsw_years or args.nsw_weeks:
        problems += fetch_nsw(args.nsw_years, args.nsw_weeks, nsw_dest)
    if args.nsw_years or args.nsw_weeks or args.nsw_local:
        print(f"Local NSW zips in {config.NSW_MANUAL_DIR}:")
        n_local = extract_local_zips(config.NSW_MANUAL_DIR, nsw_dest)
        if not n_local:
            print("  none found")
    if args.dft and not fetch_dft(config.DATA / "raw" / "dft"):
        problems.append("DfT VEH0160")

    have_nsw = nsw_dest.exists() and any(f.suffix.lower() == ".dat" for f in nsw_dest.iterdir())
    if problems:
        print(f"\nSome downloads failed: {', '.join(problems)}", file=sys.stderr)
        if any(x.startswith("NSW") for x in problems):
            print(f"For NSW: download the yearly/weekly zips from {PORTAL}\n"
                  f"into {config.NSW_MANUAL_DIR}, then run: python -m oda.fetch --nsw-local", file=sys.stderr)
        if "DfT VEH0160" in problems:
            print("For DfT: the file's address changes each release. Get the current df_VEH0160_UK.csv link from\n"
                  "https://www.gov.uk/government/statistical-data-sets/vehicle-licensing-statistics-data-files\n"
                  "and set DFT_VEH0160_URL to it.", file=sys.stderr)
    have_dft = (config.DATA / "raw" / "dft" / "df_VEH0160_UK.csv").exists()
    print(f"\nNSW .DAT files ready: {'yes' if have_nsw else 'NO'}  |  DfT file ready: {'yes' if have_dft else 'NO'}")
    if have_nsw and have_dft:
        print("Ready. Next: build the warehouse with DATA_MODE=real (scripts/run_real.ps1 on Windows, "
              "or DATA_MODE=real make check).")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
