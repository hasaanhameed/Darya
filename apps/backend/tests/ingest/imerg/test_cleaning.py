import datetime as dt

import pandas as pd

from app.ingest.imerg.cleaning import OUTPUT_COLUMNS, clean_rainfall

DAY = dt.date(2026, 4, 30)


def raw_row(observed_on=DAY, node_id="tarbela", catchment=12.3, local=4.5, coverage=1.0, version="V07B"):
    return {
        "node_id": node_id, "observed_on": observed_on, "catchment_rainfall_mm": catchment, "local_rainfall_mm": local,
        "catchment_coverage": coverage, "local_coverage": 1.0,
        "source_file": f"3B-DAY-L.MS.MRG.3IMERG.{observed_on:%Y%m%d}-S000000-E235959.{version}.nc4",
    }


def clean(rows, start=DAY, end=DAY):
    return clean_rainfall(pd.DataFrame(rows), start, end)


def test_output_has_the_table_columns_run_and_version_label():
    row = clean([raw_row()]).iloc[0]

    assert list(clean([raw_row()]).columns) == OUTPUT_COLUMNS
    assert row["run"] == "late"
    assert row["version_label"] == "V07B"
    assert row["flags"] == []


def test_keeps_only_days_in_the_requested_range():
    rows = clean([raw_row(DAY - dt.timedelta(days=1)), raw_row(), raw_row(DAY + dt.timedelta(days=1))])

    assert list(rows["observed_on"]) == [DAY]


def test_keeps_the_newest_version_when_a_day_has_two_files():
    rows = clean([raw_row(catchment=1.0, version="V07C"), raw_row(catchment=2.0, version="V07B")])

    assert len(rows) == 1
    assert rows.iloc[0]["version_label"] == "V07C"
    assert rows.iloc[0]["catchment_rainfall_mm"] == 1.0


def test_flags_low_coverage_and_missing_values():
    rows = clean([
        raw_row(node_id="tarbela", coverage=0.8),
        raw_row(node_id="mangla", catchment=float("nan"), coverage=0.0),
    ]).set_index("node_id")

    assert rows.loc["tarbela", "flags"] == ["low_coverage"]
    assert rows.loc["mangla", "flags"] == ["low_coverage", "missing_value"]


def test_reads_the_version_label_from_a_harmony_file_name():
    harmony_name = "487701427_GPM_3IMERGDL.07_3B-DAY-L.MS.MRG.3IMERG.20260430-S000000-E235959.V07B_precipitation_subsetted.nc4"
    row = raw_row()
    row["source_file"] = harmony_name

    assert clean([row]).iloc[0]["version_label"] == "V07B"
