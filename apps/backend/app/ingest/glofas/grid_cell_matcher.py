"""Match each river node to the GloFAS grid cell that represents its river channel."""

import numpy as np
import pandas as pd
import xarray as xr

SEARCH_CELLS = 3  # look ±3 cells (about ±15 km at 0.05°) around the node
MAIN_CHANNEL_SHARE = 0.5  # cells draining at least half the window's largest area are on the main river
KM_PER_DEGREE = 111.2


def match_nodes_to_cells(
    uparea: xr.DataArray,
    nodes: pd.DataFrame,
    manual_cells: dict[str, tuple[float, float]] | None = None,
    search_cells: int = SEARCH_CELLS,
) -> pd.DataFrame:
    """For each node (node_id, lat, lon), pick the nearest cell on the main river.

    Our coordinates are approximate and the model's river can run a cell or two off the real one.
    Cells draining at least half the largest upstream area nearby are on the main river (not a side
    stream); of those, the closest to the node wins. Taking simply the largest area would drift to the
    downstream edge of the search window, because upstream area grows downstream.

    `manual_cells` maps node_id -> (lat, lon) for nodes where a person chose the cell after
    reviewing the grid (e.g. a node right at a confluence); those nodes skip the search.
    `uparea` is the GloFAS upstream-area grid in m² with `latitude` and `longitude` coordinates.
    """
    manual_cells = manual_cells or {}
    matches = [
        _describe(node, _manual_cell(uparea, node, manual_cells[node.node_id]), "manual")
        if node.node_id in manual_cells
        else _describe(node, _search_cell(uparea, node, search_cells), "search")
        for node in nodes.itertuples()
    ]
    return pd.DataFrame(matches)


def _search_cell(uparea: xr.DataArray, node, search_cells: int) -> pd.Series:
    lat_index = int(np.argmin(abs(uparea["latitude"].values - node.lat)))
    lon_index = int(np.argmin(abs(uparea["longitude"].values - node.lon)))
    window = uparea.isel(
        latitude=slice(max(lat_index - search_cells, 0), lat_index + search_cells + 1),
        longitude=slice(max(lon_index - search_cells, 0), lon_index + search_cells + 1),
    )
    cells = _with_distance(window, node)
    main_channel = cells[cells["uparea_m2"] >= MAIN_CHANNEL_SHARE * cells["uparea_m2"].max()]
    return main_channel.loc[main_channel["distance_km"].idxmin()]


def _manual_cell(uparea: xr.DataArray, node, cell: tuple[float, float]) -> pd.Series:
    lat, lon = cell
    chosen = uparea.sel(latitude=[lat], longitude=[lon], method="nearest")
    return _with_distance(chosen, node).iloc[0]


def _with_distance(cells_grid: xr.DataArray, node) -> pd.DataFrame:
    cells = cells_grid.to_dataframe(name="uparea_m2").reset_index()
    cells["distance_km"] = _distance_km(node.lat, node.lon, cells["latitude"], cells["longitude"])
    return cells


def _describe(node, best: pd.Series, matched_by: str) -> dict:
    return {
        "node_id": node.node_id,
        "node_lat": node.lat,
        "node_lon": node.lon,
        "cell_lat": round(float(best["latitude"]), 3),
        "cell_lon": round(float(best["longitude"]), 3),
        "upstream_area_km2": round(float(best["uparea_m2"]) / 1e6),
        "distance_km": round(float(best["distance_km"]), 2),
        "matched_by": matched_by,  # "search" or "manual"
    }


def _distance_km(lat: float, lon: float, cell_lats: pd.Series, cell_lons: pd.Series) -> pd.Series:
    """Straight-line distance; accurate enough over a few kilometres."""
    north_km = (cell_lats - lat) * KM_PER_DEGREE
    east_km = (cell_lons - lon) * KM_PER_DEGREE * np.cos(np.radians((lat + cell_lats) / 2))
    return np.hypot(north_km, east_km)
