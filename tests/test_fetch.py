"""Fetch helpers: nested-zip extraction, hand-downloaded zips, and the weekly date list. No network."""

import io
import zipfile
from datetime import date

from oda import fetch


def _zip(files: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, data in files.items():
            zf.writestr(name, data)
    return buf.getvalue()


def test_yearly_archive_with_nested_weekly_zips(tmp_path):
    weekly = _zip({"001_SALES_DATA_NNME_20250106.DAT": b"B;1;\n", "readme.txt": b"x"})
    yearly = _zip({"20250106.zip": weekly, "20250113.zip": _zip({"002.DAT": b"B;2;\n"})})
    n = fetch._extract_dat_files(yearly, tmp_path)
    assert n == 2
    assert sorted(p.name for p in tmp_path.iterdir()) == ["001_SALES_DATA_NNME_20250106.DAT", "002.DAT"]


def test_hand_downloaded_zips_are_extracted_and_bad_ones_skipped(tmp_path):
    src, dest = tmp_path / "downloads", tmp_path / "nsw"
    src.mkdir()
    (src / "2024.zip").write_bytes(_zip({"w1.zip": _zip({"a.DAT": b"B;1;\n"})}))
    (src / "broken.zip").write_bytes(b"not a zip")
    (src / "loose.DAT").write_bytes(b"B;3;\n")
    assert fetch.extract_local_zips(src, dest) == 2
    assert sorted(p.name for p in dest.iterdir()) == ["a.DAT", "loose.DAT"]


def test_missing_download_folder_is_fine(tmp_path):
    assert fetch.extract_local_zips(tmp_path / "nope", tmp_path / "out") == 0


def test_mondays_this_year():
    weeks = fetch.mondays_this_year(date(2026, 1, 20))
    assert weeks == ["20260105", "20260112", "20260119"]
