import pandas as pd
import pytest

from app.ingest.pmd.station_names import add_station_ids, normalise_names, read_station_catalog

# Pakistan's extent, with a small margin
LAT_RANGE = (23.5, 37.5)
LON_RANGE = (60.5, 78.0)


def test_normalise_names_trims_and_collapses_spaces():
    names = pd.Series(["GUJRANWALA ", "T.T.  SINGH", " islamabad a/p"])
    assert normalise_names(names).tolist() == ["GUJRANWALA", "T.T. SINGH", "ISLAMABAD A/P"]


def test_normalise_names_applies_aliases():
    names = pd.Series(["LAHORE, UPPER MALL"])
    assert normalise_names(names).tolist() == ["LAHORE UPPER MALL"]


def test_add_station_ids_matches_by_normalised_name():
    catalog = pd.DataFrame({"id": ["gujranwala", "tt_singh"], "pmd_name": ["GUJRANWALA", "T.T. SINGH"]})
    rows = pd.DataFrame({"station": ["GUJRANWALA ", "T.T.  SINGH", "GUJRANWALA"]})

    assert add_station_ids(rows, catalog)["station_id"].tolist() == ["gujranwala", "tt_singh", "gujranwala"]


def test_add_station_ids_rejects_unknown_names():
    catalog = pd.DataFrame({"id": ["gujranwala"], "pmd_name": ["GUJRANWALA"]})
    rows = pd.DataFrame({"station": ["GUJRANWALA", "ATLANTIS"]})

    with pytest.raises(ValueError, match="ATLANTIS"):
        add_station_ids(rows, catalog)


def test_catalog_ids_and_names_are_unique():
    catalog = read_station_catalog()
    assert catalog["id"].is_unique
    assert catalog["pmd_name"].is_unique


def test_catalog_names_are_already_normalised():
    catalog = read_station_catalog()
    assert (normalise_names(catalog["pmd_name"]) == catalog["pmd_name"]).all()


def test_catalog_has_valid_basin_province_and_coordinates():
    catalog = read_station_catalog()
    assert set(catalog["basin"]) <= {"indus", "outside"}
    assert set(catalog["province"]) <= {"Punjab", "Sindh", "KP", "Balochistan", "GB", "AJK", "ICT"}
    assert catalog["lat"].between(*LAT_RANGE).all()
    assert catalog["lon"].between(*LON_RANGE).all()
