from oda.config import NSW_B_FIELDS
from oda.parse_nsw import parse_dat_file
from oda.pipeline import load_dft_long


def test_nsw_parser_keeps_only_b_records_and_pads_short_lines(tmp_path):
    f = tmp_path / "x.DAT"
    f.write_text(
        "A;RTSALEDATA;001;20260105 01:02;VALUER GENERAL;\n"
        "B;199;123;1;20260105 01:02;;;12;HIGH ST;PENRITH;2750;600;M;20251101;20251215;900000;R2;R;RESIDENCE;;R;;;AT1;\n"
        "C;199;123;1;20260105 01:02;LOT 1 DP123;\n"
        "B;199;124;1;20260105 01:02;;;14;HIGH ST\n"
        "Z;2;\n",
        encoding="latin-1",
    )
    rows = parse_dat_file(f)
    assert len(rows) == 2
    assert all(len(r) == len(NSW_B_FIELDS) for r in rows)
    first = dict(zip(NSW_B_FIELDS, rows[0]))
    assert first["locality"] == "PENRITH"
    assert first["purchase_price"] == "900000"
    assert first["contract_date"] == "20251101"


def test_dft_loader_unpivots_quarters_and_keeps_suppressed_markers(tmp_path):
    f = tmp_path / "df_VEH0160_UK.csv"
    f.write_text(
        "BodyType,Make,GenModel,Model,Fuel,2026 Q2,2026 Q1\n"
        "Cars,TESLA,TESLA MODEL Y,MODEL Y,BATTERY ELECTRIC,7000,[c]\n"
    )
    long = load_dft_long(f)
    assert list(long.columns) == ["body_type", "make", "gen_model", "model", "fuel", "quarter_label", "units_raw"]
    assert len(long) == 2
    assert set(long["units_raw"]) == {"7000", "[c]"}


def test_dft_loader_fails_loudly_if_layout_changes(tmp_path):
    f = tmp_path / "bad.csv"
    f.write_text("Make,Units\nTESLA,5\n")
    try:
        load_dft_long(f)
    except ValueError as exc:
        assert "YYYY Qn" in str(exc)
    else:
        raise AssertionError("expected a ValueError")
