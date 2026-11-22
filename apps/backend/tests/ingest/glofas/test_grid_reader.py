import datetime as dt

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from app.ingest.glofas.grid_reader import read_discharge

LATITUDES = [34.125, 34.075, 34.025]
LONGITUDES = [72.525, 72.575, 72.625]
CELLS = pd.DataFrame([
    {"node_id": "tarbela", "cell_lat": 34.075, "cell_lon": 72.575},
    {"node_id": "mangla", "cell_lat": 34.025, "cell_lon": 72.625},
])


def make_file(time_name="valid_time", stamps=("2022-08-29", "2022-08-30")) -> xr.Dataset:
    """A small GloFAS-like file: avg_dis in m³/s, each value stamped at 00 UTC at the end of its 24 hours."""
    times = pd.to_datetime(list(stamps))
    values = np.arange(len(times) * 9, dtype="float32").reshape(len(times), 3, 3)
    return xr.Dataset(
        {"avg_dis": ((time_name, "latitude", "longitude"), values)},
        coords={time_name: times, "latitude": LATITUDES, "longitude": LONGITUDES},
    )


def test_reads_one_row_per_node_per_day():
    rows = read_discharge(make_file(), CELLS, "consolidated", "consolidated_2022.nc")

    assert len(rows) == 4
    assert list(rows.columns) == ["node_id", "observed_on", "discharge_m3s", "product_type", "source_file"]
    assert set(rows["product_type"]) == {"consolidated"}
    assert set(rows["source_file"]) == {"consolidated_2022.nc"}


def test_takes_the_value_at_each_nodes_cell():
    rows = read_discharge(make_file(), CELLS, "consolidated", "f.nc").set_index(["node_id", "observed_on"])

    # first time step: tarbela is row 1, col 1 -> 4; mangla is row 2, col 2 -> 8
    assert rows.loc[("tarbela", dt.date(2022, 8, 28)), "discharge_m3s"] == 4
    assert rows.loc[("mangla", dt.date(2022, 8, 28)), "discharge_m3s"] == 8


def test_value_stamped_at_midnight_belongs_to_the_day_before():
    rows = read_discharge(make_file(), CELLS, "consolidated", "f.nc")

    assert sorted(set(rows["observed_on"])) == [dt.date(2022, 8, 28), dt.date(2022, 8, 29)]


def test_accepts_time_as_the_time_coordinate_name():
    rows = read_discharge(make_file(time_name="time"), CELLS, "consolidated", "f.nc")

    assert len(rows) == 4


def test_fails_when_a_cell_is_outside_the_file():
    far_cells = pd.DataFrame([{"node_id": "kotri", "cell_lat": 25.425, "cell_lon": 68.325}])

    with pytest.raises(KeyError):
        read_discharge(make_file(), far_cells, "consolidated", "f.nc")
