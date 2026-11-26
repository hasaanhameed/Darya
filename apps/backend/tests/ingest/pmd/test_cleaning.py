import datetime as dt

import pandas as pd
import pytest

from app.ingest.pmd.cleaning import clean_rows

SOURCE_FILE = "DAILY RAIN - ALL STATIONS - 1981-2015.xls"


def station_month(cells: dict[int, str], station_id="astore", year=1982, month=2, sheet_row=10) -> pd.DataFrame:
    """One station-month shaped like the parser output (+ station_id): 31 day rows, blank unless given."""
    return pd.DataFrame(
        {
            "station": station_id.upper(),
            "station_id": station_id,
            "year": year,
            "month": month,
            "day": range(1, 32),
            "rainfall_raw": [cells.get(day, "") for day in range(1, 32)],
            "sheet_row": sheet_row,
            "source_file": SOURCE_FILE,
        }
    )


def clean(*station_months: pd.DataFrame) -> pd.DataFrame:
    rows, _ = clean_rows(pd.concat(station_months, ignore_index=True))
    return rows


def row_on(rows: pd.DataFrame, day: int, month=2, year=1982) -> pd.Series:
    matches = rows[rows["observed_on"] == dt.date(year, month, day)]
    assert len(matches) == 1
    return matches.iloc[0]


# --- what becomes a row ---


def test_blank_cells_produce_no_rows():
    rows = clean(station_month({1: "0", 2: "3.5"}))
    assert sorted(rows["observed_on"]) == [dt.date(1982, 2, 1), dt.date(1982, 2, 2)]


def test_days_that_do_not_exist_are_not_stored():
    rows = clean(station_month({28: "0", 29: "***", 30: "***", 31: "***"}))  # Feb 1982 has 28 days
    assert rows["observed_on"].tolist() == [dt.date(1982, 2, 28)]


def test_numbers_are_converted_and_raw_text_is_kept():
    row = row_on(clean(station_month({5: "12.7"})), 5)
    assert row["rainfall_mm"] == pytest.approx(12.7)
    assert row["rainfall_raw"] == "12.7"
    assert row["flags"] == []


def test_output_keeps_provenance():
    rows = clean(station_month({1: "0"}, sheet_row=42))
    assert rows.iloc[0][["station_id", "source_file", "sheet_row"]].tolist() == ["astore", SOURCE_FILE, 42]


# --- flags (ADR-024) ---


@pytest.mark.parametrize("marker", ["----", "---", "-   ----", "*", "**", "-  ***"])
def test_no_reading_markers_are_flagged_with_an_empty_value(marker):
    row = row_on(clean(station_month({3: marker})), 3)
    assert pd.isna(row["rainfall_mm"])
    assert row["rainfall_raw"] == marker
    assert row["flags"] == ["missing_marker"]


def test_triple_star_on_a_real_day_is_a_missing_marker():
    row = row_on(clean(station_month({29: "***"}, year=1984)), 29, year=1984)  # 1984 is a leap year
    assert row["flags"] == ["missing_marker"]


@pytest.mark.parametrize("garbled", [".0   1", "e   .0", "0.1 ***", "/"])
def test_garbled_text_is_flagged_not_numeric(garbled):
    row = row_on(clean(station_month({3: garbled})), 3)
    assert pd.isna(row["rainfall_mm"])
    assert row["flags"] == ["not_numeric"]


def test_negative_values_are_kept_and_flagged():
    row = row_on(clean(station_month({4: "-1"})), 4)
    assert row["rainfall_mm"] == -1
    assert row["flags"] == ["suspect_negative"]


def test_more_than_300_mm_is_flagged_extreme():
    rows = clean(station_month({1: "300", 2: "591.9"}))
    assert row_on(rows, 1)["flags"] == []
    assert row_on(rows, 2)["flags"] == ["extreme_rainfall"]


def test_a_value_on_a_day_that_does_not_exist_flags_the_whole_month():
    rows = clean(station_month({1: "0", 2: "5", 30: "7"}))  # 30 Feb holds a value
    assert set(rows["observed_on"]) == {dt.date(1982, 2, 1), dt.date(1982, 2, 2)}
    assert all(flags == ["month_has_impossible_day"] for flags in rows["flags"])


def test_a_zero_on_a_day_that_does_not_exist_is_ignored():
    rows = clean(station_month({1: "5", 30: "0"}))
    assert row_on(rows, 1)["flags"] == []


def test_stations_with_modelled_looking_values_are_flagged():
    rows = clean(station_month({1: "24.6876"}, station_id="garhi_dupatta"), station_month({1: "1.66"}, station_id="kotli"))
    assert all(flags == ["not_gauge_precision"] for flags in rows["flags"])


def test_a_row_can_carry_several_flags():
    row = row_on(clean(station_month({1: "-16.8", 30: "2"}, station_id="kotli")), 1)
    assert row["flags"] == ["suspect_negative", "month_has_impossible_day", "not_gauge_precision"]


# --- duplicate station-months ---


def test_identical_duplicate_months_become_one():
    first = station_month({1: "0", 2: "5"}, sheet_row=10)
    copy = station_month({1: "0", 2: "5"}, sheet_row=11)
    rows = clean(first, copy)

    assert len(rows) == 2
    assert set(rows["sheet_row"]) == {10}
    assert all(flags == [] for flags in rows["flags"])


def test_differing_duplicate_months_keep_the_first_copy_and_flag_it():
    first = station_month({1: "0", 2: "5"}, sheet_row=10)
    other = station_month({1: "0", 2: "6"}, sheet_row=11)
    rows = clean(first, other)

    assert row_on(rows, 2)["rainfall_mm"] == 5
    assert set(rows["sheet_row"]) == {10}
    assert all(flags == ["duplicate_conflict"] for flags in rows["flags"])


def test_the_same_month_in_different_years_is_not_a_duplicate():
    rows = clean(station_month({1: "1"}, year=1982, sheet_row=10), station_month({1: "2"}, year=1983, sheet_row=22))
    assert len(rows) == 2
    assert all(flags == [] for flags in rows["flags"])


# --- report ---


def test_report_counts_what_was_not_stored():
    _, report = clean_rows(
        pd.concat(
            [
                station_month({1: "0", 30: "7"}, sheet_row=10),
                station_month({1: "1"}, station_id="badin", sheet_row=20),
                station_month({1: "2"}, station_id="badin", sheet_row=21),
            ],
            ignore_index=True,
        )
    )
    # Blanks are counted in the copies that are kept (the duplicate at row 21 is dropped):
    # two months, each with one filled real day out of 28
    assert report.blank_cells == (28 - 1) * 2
    assert report.impossible_day_values["sheet_row"].tolist() == [10]
    assert report.identical_duplicate_months == 0
    assert report.duplicate_conflicts[["station_id", "kept_sheet_row", "dropped_sheet_rows"]].values.tolist() == [
        ["badin", 20, "21"]
    ]
