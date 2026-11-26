import datetime as dt

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from app.ingest.imerg.catchment_averager import average_over_catchments

DAY = dt.date(2022, 8, 25)


def make_file(rain_mm: list[list[float]]) -> xr.Dataset:
    """A small IMERG-like daily file: precipitation (mm/day) with dims (time, lon, lat), as IMERG stores it."""
    by_lat_lon = np.array(rain_mm, dtype="float32")  # written north row first for readability
    lats, lons = [34.15, 34.05], [72.05, 72.15]
    return xr.Dataset(
        {"precipitation": (("time", "lon", "lat"), by_lat_lon.T[np.newaxis])},
        coords={"time": pd.to_datetime([DAY]), "lat": lats, "lon": lons},
    )


def weights(rows) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["node_id", "area_type", "lat", "lon", "area_km2"])


TARBELA = weights([
    ("tarbela", "catchment", 34.15, 72.05, 100.0),
    ("tarbela", "catchment", 34.15, 72.15, 300.0),
    ("tarbela", "local", 34.15, 72.15, 300.0),
])


def test_area_weighted_average_for_full_and_local_areas():
    rows = average_over_catchments(make_file([[10.0, 20.0], [0.0, 0.0]]), TARBELA, "f.nc4")

    row = rows.iloc[0]
    assert (row["node_id"], row["observed_on"]) == ("tarbela", DAY)
    assert row["catchment_rainfall_mm"] == pytest.approx((10 * 100 + 20 * 300) / 400)
    assert row["local_rainfall_mm"] == pytest.approx(20.0)
    assert row["source_file"] == "f.nc4"


def test_missing_cells_are_left_out_and_reported_as_coverage():
    rows = average_over_catchments(make_file([[np.nan, 20.0], [0.0, 0.0]]), TARBELA, "f.nc4")

    row = rows.iloc[0]
    assert row["catchment_rainfall_mm"] == pytest.approx(20.0)
    assert row["catchment_coverage"] == pytest.approx(0.75)
    assert row["local_coverage"] == pytest.approx(1.0)


def test_negative_fill_values_count_as_missing():
    rows = average_over_catchments(make_file([[-9999.9, 20.0], [0.0, 0.0]]), TARBELA, "f.nc4")

    assert rows.iloc[0]["catchment_rainfall_mm"] == pytest.approx(20.0)


def test_no_valid_cells_gives_no_value():
    rows = average_over_catchments(make_file([[np.nan, np.nan], [0.0, 0.0]]), TARBELA, "f.nc4")

    assert np.isnan(rows.iloc[0]["catchment_rainfall_mm"])
    assert rows.iloc[0]["catchment_coverage"] == 0


def test_one_row_per_node():
    two_nodes = pd.concat([TARBELA, weights([
        ("mangla", "catchment", 34.05, 72.05, 50.0), ("mangla", "local", 34.05, 72.05, 50.0),
    ])])

    rows = average_over_catchments(make_file([[10.0, 20.0], [4.0, 0.0]]), two_nodes, "f.nc4")

    assert sorted(rows["node_id"]) == ["mangla", "tarbela"]
    assert rows.set_index("node_id").loc["mangla", "catchment_rainfall_mm"] == pytest.approx(4.0)


def test_catchment_cells_outside_the_file_count_as_missing():
    outside = pd.concat([TARBELA, weights([("tarbela", "catchment", 40.05, 80.05, 400.0)])])

    rows = average_over_catchments(make_file([[10.0, 20.0], [0.0, 0.0]]), outside, "f.nc4")

    assert rows.iloc[0]["catchment_coverage"] == pytest.approx(0.5)


def test_matches_cells_when_the_file_stores_coordinates_as_float32():
    # Real IMERG subsets store lon as float32, so 72.05 is really 72.0500030517578
    dataset = make_file([[10.0, 20.0], [0.0, 0.0]])
    dataset = dataset.assign_coords(lon=dataset["lon"].astype("float32"), lat=dataset["lat"].astype("float32"))

    rows = average_over_catchments(dataset, TARBELA, "f.nc4")

    assert rows.iloc[0]["catchment_coverage"] == pytest.approx(1.0)
