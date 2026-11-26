import numpy as np
import pandas as pd
import pytest
import xarray as xr

from app.ingest.imerg.catchment_builder import imerg_cell_weights, trace_catchments

# A 4 x 4 piece of a 0.05° GloFAS grid, north row first. PCRaster LDD codes: 2 = flows south,
# 4 = west, 6 = east, 5 = outlet. Every cell drains into column 1, which flows south to the outlet.
LDD = [
    [6, 2, 4, 4],
    [6, 2, 4, 4],
    [6, 2, 4, 4],
    [6, 5, 4, 4],
]
LATS = [34.175, 34.125, 34.075, 34.025]
LONS = [72.025, 72.075, 72.125, 72.175]
CELL_KM2 = 25.6  # a 0.05° cell at 34°N is about 5.56 km x 4.61 km

# "up" sits on the river in row 1 and drains rows 0-1 (8 cells); "down" is the outlet and drains all 16.
CELLS = pd.DataFrame([
    {"node_id": "up", "cell_lat": 34.125, "cell_lon": 72.075},
    {"node_id": "down", "cell_lat": 34.025, "cell_lon": 72.075},
])


def make_ldd() -> xr.DataArray:
    return xr.DataArray(np.array(LDD, dtype="float32"), coords={"lat": LATS, "lon": LONS}, dims=["lat", "lon"])


def area_km2(catchments, node_id, area_type):
    rows = catchments[(catchments["node_id"] == node_id) & (catchments["area_type"] == area_type)]
    return rows["area_km2"].sum()


def test_full_catchment_is_all_land_draining_to_the_node():
    catchments = trace_catchments(make_ldd(), CELLS)

    assert area_km2(catchments, "up", "catchment") == pytest.approx(8 * CELL_KM2, rel=0.02)
    assert area_km2(catchments, "down", "catchment") == pytest.approx(16 * CELL_KM2, rel=0.02)


def test_local_area_stops_at_the_next_node_upstream():
    catchments = trace_catchments(make_ldd(), CELLS)

    assert area_km2(catchments, "up", "local") == pytest.approx(8 * CELL_KM2, rel=0.02)  # nothing above it
    assert area_km2(catchments, "down", "local") == pytest.approx(8 * CELL_KM2, rel=0.02)  # rows 2-3 only


def test_lists_each_cell_with_its_centre():
    catchments = trace_catchments(make_ldd(), CELLS)

    up_cells = catchments[(catchments["node_id"] == "up") & (catchments["area_type"] == "catchment")]
    assert set(zip(up_cells["lat"], up_cells["lon"])) == {(lat, lon) for lat in LATS[:2] for lon in LONS}
    assert list(catchments.columns) == ["node_id", "area_type", "lat", "lon", "area_km2"]


def test_imerg_weights_add_up_the_land_inside_each_0_1_degree_cell():
    weights = imerg_cell_weights(trace_catchments(make_ldd(), CELLS))

    up = weights[(weights["node_id"] == "up") & (weights["area_type"] == "catchment")]
    # rows 0-1 fall in the IMERG row centred at 34.15; columns 0-1 and 2-3 in IMERG columns 72.05 and 72.15
    assert sorted(zip(up["lat"], up["lon"])) == [(34.15, 72.05), (34.15, 72.15)]
    assert list(up["area_km2"]) == pytest.approx([4 * CELL_KM2] * 2, rel=0.02)


def test_imerg_weights_keep_the_total_area():
    catchments = trace_catchments(make_ldd(), CELLS)

    weights = imerg_cell_weights(catchments)

    assert weights["area_km2"].sum() == pytest.approx(catchments["area_km2"].sum())
