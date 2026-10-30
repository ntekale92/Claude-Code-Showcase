import duckdb

from oda.quality import run_checks


def q(db, sql):
    con = duckdb.connect(str(db), read_only=True)
    try:
        return con.execute(sql).fetchall()
    finally:
        con.close()


def test_all_models_build(warehouse):
    tables = {r[0] for r in q(warehouse, "select table_name from information_schema.tables")}
    for t in ["stg_nsw_sales", "stg_dft_registrations", "mart_suburb_quarterly",
              "mart_nsw_monthly", "mart_fuel_mix_quarterly", "mart_make_quarterly"]:
        assert t in tables
        assert q(warehouse, f"select count(*) from {t}")[0][0] > 0


def test_duplicates_removed_but_flagged_rows_kept(warehouse):
    raw, staged, flagged = q(warehouse, """
        select (select count(*) from raw_nsw_sales),
               (select count(*) from stg_nsw_sales),
               (select count(*) from stg_nsw_sales where not is_clean)""")[0]
    assert staged < raw          # the sample contains exact duplicates
    assert flagged > 0           # bad rows are flagged, not silently dropped


def test_suppressed_cells_are_null_not_zero(warehouse):
    zeros, nulls = q(warehouse, """
        select count(*) filter (where suppressed and units = 0),
               count(*) filter (where suppressed and units is null)
        from stg_dft_registrations""")[0]
    assert zeros == 0 and nulls > 0


def test_yoy_never_published_for_incomplete_quarters(warehouse):
    bad = q(warehouse, "select count(*) from mart_suburb_quarterly "
                       "where median_price_yoy_pct is not null and not is_complete_quarter")[0][0]
    assert bad == 0


def test_every_error_level_quality_check_passes(warehouse):
    failed = [r.name for r in run_checks(warehouse) if r.severity == "error" and not r.passed]
    assert failed == []


def test_broken_check_sql_counts_as_failure(warehouse, tmp_path):
    f = tmp_path / "checks.yaml"
    f.write_text("checks:\n  - name: broken\n    severity: error\n    sql: select * from no_such_table\n    expect: {eq: 0}\n")
    (res,) = run_checks(warehouse, f)
    assert not res.passed and res.error
