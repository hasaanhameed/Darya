import datetime as dt

import pandas as pd

from app.ingest.wapda.cleaning import clean_sheets, to_numbers

SAME_AS_EXPECTED = object()
STATION_LEVELS_FT = {"tarbela": 1500, "ghazi_barotha": 1090, "mangla": 1200, "warsak": 1270, "chashma": 645, "jinnah": 693}


def station_row(station, level, inflow, turbine, other, total, indent="-"):
    return {
        "station": station,
        "level_ft": level,
        "level_ft_last_year": None,
        "irrigation_indent": indent,
        "inflow_cfs": inflow,
        "inflow_cfs_last_year": None,
        "outflow_turbine_cfs": turbine,
        "outflow_other_cfs": other,
        "outflow_total_cfs": total,
        "outflow_total_cfs_last_year": None,
    }


def make_sheet(expected, date_in_sheet=SAME_AS_EXPECTED, values_from=None, changes=None, file_name=None):
    """The parsed rows of one sheet, with realistic values that differ from day to day.

    values_from: build the values for another day (to make a copied sheet).
    changes: {station: {field: value}} to plant a specific value.
    """
    day = (values_from or expected).toordinal() % 1000
    rows = {"tarbela_t4": station_row("tarbela_t4", None, None, 30000, None, None)}
    for station, level in STATION_LEVELS_FT.items():
        inflow = 50000 + day * 10
        rows[station] = station_row(station, level + day / 1000, inflow, 20000, inflow - 20000, inflow)
    # Tarbela's total also includes T-4's turbine flow
    rows["tarbela"]["outflow_other_cfs"] = rows["tarbela"]["inflow_cfs"] - 50000
    for station, fields in (changes or {}).items():
        rows[station].update(fields)

    sheet = pd.DataFrame(rows.values())
    sheet.insert(0, "source_file", file_name or f"{expected:%b-%Y}.xls")
    sheet.insert(1, "sheet", str(expected.day))
    sheet.insert(2, "expected_date", expected)
    sheet.insert(3, "date_in_sheet", expected if date_in_sheet is SAME_AS_EXPECTED else date_in_sheet)
    return sheet


def clean(*sheets):
    return clean_sheets(pd.concat(sheets, ignore_index=True))


def days(start, count):
    return [start + dt.timedelta(days=i) for i in range(count)]


def row_for(rows, station, observed_on):
    return rows[(rows["node_id"] == station) & (rows["observed_on"] == observed_on)].iloc[0]


def rows_on(rows, observed_on):
    return rows[rows["observed_on"] == observed_on]


def has_flag(rows, flag):
    return rows["flags"].map(lambda flags: flag in flags)


# --- numbers ---

def test_converts_dash_and_blank_to_none():
    numbers, unreadable = to_numbers(pd.Series([None, "", " - "], dtype=object))
    assert numbers.isna().all()
    assert not unreadable.any()


def test_converts_numbers_and_numeric_text():
    numbers, unreadable = to_numbers(pd.Series([1549, "313,000"], dtype=object))
    assert numbers.tolist() == [1549.0, 313000.0]
    assert not unreadable.any()


def test_flags_unparseable_text_as_not_numeric():
    rows, _ = clean(make_sheet(dt.date(2024, 8, 15), changes={"mangla": {"level_ft": "120.4.95"}}))

    mangla = row_for(rows, "mangla", dt.date(2024, 8, 15))
    assert pd.isna(mangla["level_ft"])
    assert "not_numeric_level_ft" in mangla["flags"]


def test_keeps_irrigation_indent_as_text():
    rows, _ = clean(make_sheet(dt.date(2024, 8, 15), changes={"tarbela": {"irrigation_indent": "1 Feet Rise"}}))
    assert row_for(rows, "tarbela", dt.date(2024, 8, 15))["irrigation_indent_raw"] == "1 Feet Rise"


def test_returns_rows_for_six_stations_without_t4():
    rows, _ = clean(make_sheet(dt.date(2024, 8, 15)))
    assert set(rows["node_id"]) == set(STATION_LEVELS_FT)


# --- dates (ADR-017) ---

def test_keeps_sheet_whose_date_matches_with_no_flags():
    rows, _ = clean(make_sheet(dt.date(2024, 8, 15)))

    assert (rows["observed_on"] == dt.date(2024, 8, 15)).all()
    assert (rows["flags"].map(len) == 0).all()


def test_skips_stale_copy_identical_to_claimed_date():
    october = make_sheet(dt.date(2023, 10, 1))
    stale = make_sheet(dt.date(2023, 11, 1), date_in_sheet=dt.date(2023, 10, 1), values_from=dt.date(2023, 10, 1))

    rows, report = clean(october, stale)

    assert set(rows["observed_on"]) == {dt.date(2023, 10, 1)}
    assert len(report.stale_copies) == 1


def test_uses_sheet_date_when_claimed_date_has_no_sheet():
    copied = make_sheet(dt.date(2023, 11, 8), date_in_sheet=dt.date(2023, 10, 8), values_from=dt.date(2023, 10, 8))

    rows, _ = clean(copied)

    assert set(rows["observed_on"]) == {dt.date(2023, 10, 8)}
    assert has_flag(rows, "date_from_sheet").all()


def test_uses_expected_date_for_date_typo():
    sep_5 = make_sheet(dt.date(2025, 9, 5))
    sep_6_dated_sep_5 = make_sheet(dt.date(2025, 9, 6), date_in_sheet=dt.date(2025, 9, 5))

    rows, _ = clean(sep_5, sep_6_dated_sep_5)

    assert has_flag(rows_on(rows, dt.date(2025, 9, 6)), "date_typo").all()
    assert (rows_on(rows, dt.date(2025, 9, 5))["flags"].map(len) == 0).all()


def test_uses_expected_date_when_date_cell_is_unreadable():
    rows, _ = clean(make_sheet(dt.date(2026, 8, 12), date_in_sheet=None))

    assert set(rows["observed_on"]) == {dt.date(2026, 8, 12)}
    assert has_flag(rows, "date_unreadable").all()


def test_flags_sheet_repeated_from_previous_day():
    april_14 = make_sheet(dt.date(2025, 4, 14))
    april_15 = make_sheet(dt.date(2025, 4, 15), values_from=dt.date(2025, 4, 14))

    rows, _ = clean(april_14, april_15)

    assert has_flag(rows_on(rows, dt.date(2025, 4, 15)), "repeated_previous_day").all()
    assert (rows_on(rows, dt.date(2025, 4, 14))["flags"].map(len) == 0).all()


def test_keeps_one_row_per_station_day():
    monthly = make_sheet(dt.date(2026, 7, 27), file_name="JULY- 2026 (24).xls")
    single_day = make_sheet(dt.date(2026, 7, 27), changes={"tarbela": {"inflow_cfs": 242900}}, file_name="Daily data July- 2026 (27).xlsx")

    rows, report = clean(monthly, single_day)

    assert (rows["node_id"] == "tarbela").sum() == 1
    assert len(report.conflicts) == 1


# --- suspect values ---

def test_flags_level_far_from_neighbours_as_suspect():
    week = days(dt.date(2024, 8, 12), 7)
    sheets = [make_sheet(d) for d in week]
    sheets[3] = make_sheet(week[3], changes={"mangla": {"level_ft": 121.3}})

    rows, _ = clean(*sheets)

    suspect = rows[has_flag(rows, "suspect_level_ft")]
    assert list(zip(suspect["node_id"], suspect["observed_on"])) == [("mangla", week[3])]


def test_flags_inflow_far_from_neighbours_as_suspect():
    week = days(dt.date(2022, 9, 11), 7)
    sheets = [make_sheet(d) for d in week]
    sheets[3] = make_sheet(week[3], changes={"warsak": {"inflow_cfs": 580060}})

    rows, _ = clean(*sheets)

    assert "suspect_inflow_cfs" in row_for(rows, "warsak", week[3])["flags"]


def test_flags_negative_inflow_as_suspect():
    rows, _ = clean(make_sheet(dt.date(2024, 10, 4), changes={"jinnah": {"inflow_cfs": -1431.6}}))
    assert "suspect_inflow_cfs" in row_for(rows, "jinnah", dt.date(2024, 10, 4))["flags"]


def test_does_not_change_suspect_values():
    week = days(dt.date(2024, 8, 12), 7)
    sheets = [make_sheet(d) for d in week]
    sheets[3] = make_sheet(week[3], changes={"mangla": {"level_ft": 121.3}})

    rows, _ = clean(*sheets)

    assert row_for(rows, "mangla", week[3])["level_ft"] == 121.3


# --- outflow check ---

def test_outflow_sum_includes_t4_for_tarbela():
    rows, _ = clean(make_sheet(dt.date(2024, 8, 15)))
    assert "outflow_sum_mismatch" not in row_for(rows, "tarbela", dt.date(2024, 8, 15))["flags"]


def test_flags_outflow_total_that_does_not_add_up():
    # Aug 2022 flood: spillway flow missing from the "other" column
    sheet = make_sheet(dt.date(2022, 8, 28), changes={"chashma": {"outflow_turbine_cfs": 14308, "outflow_other_cfs": 3125, "outflow_total_cfs": 516468}})
    rows, _ = clean(sheet)

    chashma = row_for(rows, "chashma", dt.date(2022, 8, 28))
    assert "outflow_sum_mismatch" in chashma["flags"]
    assert chashma["outflow_total_cfs"] == 516468
