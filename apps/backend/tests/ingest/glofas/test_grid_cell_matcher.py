import numpy as np
import pandas as pd
import pytest
import xarray as xr

from app.ingest.glofas.grid_cell_matcher import match_nodes_to_cells

# A 0.05° grid like GloFAS: cell centres at .x25 / .x75, latitude running north to south.
LATITUDES = np.round(np.arange(34.475, 33.5, -0.05), 3)
LONGITUDES = np.round(np.arange(72.025, 73.0, 0.05), 3)
NODE = pd.DataFrame([{"node_id": "tarbela", "lat": 34.0, "lon": 72.5}])


def make_uparea(cells_km2: dict) -> xr.DataArray:
    """A small upstream-area grid in m², zero except for the given {(lat, lon): km²} cells."""
    values = np.zeros((len(LATITUDES), len(LONGITUDES)), dtype="float32")
    for (lat, lon), km2 in cells_km2.items():
        values[np.argmin(abs(LATITUDES - lat)), np.argmin(abs(LONGITUDES - lon))] = km2 * 1e6
    return xr.DataArray(values, coords={"latitude": LATITUDES, "longitude": LONGITUDES}, dims=["latitude", "longitude"])


def test_picks_the_largest_upstream_area_near_the_node():
    uparea = make_uparea({(34.075, 72.575): 170_000, (33.975, 72.475): 500})

    match = match_nodes_to_cells(uparea, NODE).iloc[0]

    assert match["node_id"] == "tarbela"
    assert (match["cell_lat"], match["cell_lon"]) == (34.075, 72.575)
    assert match["upstream_area_km2"] == pytest.approx(170_000)


def test_prefers_the_nearest_main_channel_cell_over_a_larger_one_downstream():
    # Upstream area grows downstream; the cell next to the node wins over the window's largest
    uparea = make_uparea({(34.025, 72.475): 170_000, (33.875, 72.475): 200_000})

    match = match_nodes_to_cells(uparea, NODE).iloc[0]

    assert (match["cell_lat"], match["cell_lon"]) == (34.025, 72.475)


def test_ignores_a_nearer_small_side_stream():
    # The side stream drains under half of the main river's area, so it is not the main channel
    uparea = make_uparea({(34.025, 72.475): 50_000, (33.925, 72.475): 170_000})

    match = match_nodes_to_cells(uparea, NODE).iloc[0]

    assert (match["cell_lat"], match["cell_lon"]) == (33.925, 72.475)


def test_ignores_cells_outside_the_search_window():
    # 5 cells north of the node: outside the ±3-cell window, even though it is larger
    uparea = make_uparea({(34.225, 72.525): 900_000, (33.975, 72.525): 20_000})

    match = match_nodes_to_cells(uparea, NODE).iloc[0]

    assert (match["cell_lat"], match["cell_lon"]) == (33.975, 72.525)


def test_reports_distance_from_node_to_cell():
    uparea = make_uparea({(34.075, 72.575): 170_000})

    match = match_nodes_to_cells(uparea, NODE).iloc[0]

    # 0.075° north (~8.3 km) and 0.075° east (~6.9 km at 34°N)
    assert match["distance_km"] == pytest.approx(10.8, abs=0.3)


def test_returns_one_row_per_node():
    nodes = pd.DataFrame([{"node_id": "a", "lat": 34.0, "lon": 72.5}, {"node_id": "b", "lat": 33.7, "lon": 72.8}])
    uparea = make_uparea({(34.025, 72.525): 100, (33.725, 72.825): 200})

    matches = match_nodes_to_cells(uparea, nodes)

    assert list(matches["node_id"]) == ["a", "b"]
    assert list(matches["upstream_area_km2"]) == pytest.approx([100, 200])


def test_uses_a_manually_chosen_cell_when_given():
    uparea = make_uparea({(34.025, 72.475): 170_000, (33.925, 72.575): 80_000})

    match = match_nodes_to_cells(uparea, NODE, manual_cells={"tarbela": (33.925, 72.575)}).iloc[0]

    assert (match["cell_lat"], match["cell_lon"]) == (33.925, 72.575)
    assert match["upstream_area_km2"] == pytest.approx(80_000)
    assert match["matched_by"] == "manual"


def test_marks_searched_cells_as_matched_by_search():
    uparea = make_uparea({(34.025, 72.475): 170_000})

    match = match_nodes_to_cells(uparea, NODE).iloc[0]

    assert match["matched_by"] == "search"
