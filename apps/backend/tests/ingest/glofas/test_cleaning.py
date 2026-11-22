import datetime as dt

import pandas as pd

from app.ingest.glofas.cleaning import OUTPUT_COLUMNS, clean_discharge
from app.ingest.glofas.request_builder import SYSTEM_VERSION

DAY = dt.date(2026, 6, 30)


def raw_row(discharge_m3s=7420.5, product_type="consolidated", observed_on=DAY, node_id="tarbela"):
    return {
        "node_id": node_id, "observed_on": observed_on, "discharge_m3s": discharge_m3s,
        "product_type": product_type, "source_file": f"{product_type}.nc",
    }


def clean(rows, start=DAY, end=DAY):
    return clean_discharge(pd.DataFrame(rows), start, end)


def test_output_has_the_table_columns_and_version():
    rows = clean([raw_row()])

    assert list(rows.columns) == OUTPUT_COLUMNS
    assert rows.iloc[0]["system_version"] == SYSTEM_VERSION
    assert rows.iloc[0]["flags"] == []


def test_keeps_consolidated_when_both_products_cover_a_day():
    rows = clean([raw_row(100.0, "intermediate"), raw_row(200.0, "consolidated")])

    assert len(rows) == 1
    assert rows.iloc[0]["product_type"] == "consolidated"
    assert rows.iloc[0]["discharge_m3s"] == 200.0


def test_keeps_only_days_in_the_requested_range():
    rows = clean([raw_row(observed_on=DAY - dt.timedelta(days=1)), raw_row(), raw_row(observed_on=DAY + dt.timedelta(days=1))])

    assert list(rows["observed_on"]) == [DAY]


def test_flags_missing_and_negative_values_without_changing_them():
    rows = clean([raw_row(float("nan"), node_id="tarbela"), raw_row(-3.0, node_id="mangla")]).set_index("node_id")

    assert rows.loc["tarbela", "flags"] == ["missing_value"]
    assert rows.loc["mangla", "flags"] == ["negative_value"]
    assert rows.loc["mangla", "discharge_m3s"] == -3.0


def test_rows_are_sorted_by_node_and_day():
    rows = clean([raw_row(node_id="mangla"), raw_row(node_id="chashma")])

    assert list(rows["node_id"]) == ["chashma", "mangla"]
