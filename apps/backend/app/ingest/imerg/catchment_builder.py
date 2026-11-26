"""Trace each node's catchment on GloFAS's flow-direction map, and weight IMERG cells by it (ADR-022)."""

import numpy as np
import pandas as pd
import pyflwdir
import xarray as xr
from rasterio.transform import from_origin

GRID_DEG = 0.05  # GloFAS cell size
IMERG_DEG = 0.1  # IMERG cell size
NO_FLOW = 255  # pyflwdir's code for "no flow direction" (sea, outside the map)


def trace_catchments(ldd: xr.DataArray, cells: pd.DataFrame) -> pd.DataFrame:
    """Every GloFAS cell inside each node's catchment, as rows: node_id, area_type, lat, lon, area_km2.

    `ldd` is the GloFAS local-drain-direction grid (PCRaster codes) with `lat` (north to south) and
    `lon` coordinates; `cells` holds node_id, cell_lat, cell_lon (see ingest/glofas/node_grid_cells.csv).

    Two area types per node:
    - "catchment": all land draining to the node's cell;
    - "local": only the land between the node and the next nodes upstream.
    """
    lats, lons = ldd["lat"].to_numpy(), ldd["lon"].to_numpy()
    codes = np.where(np.isnan(ldd.to_numpy()), NO_FLOW, ldd.to_numpy()).astype("uint8")
    transform = from_origin(lons[0] - GRID_DEG / 2, lats[0] + GRID_DEG / 2, GRID_DEG, GRID_DEG)
    flow = pyflwdir.from_array(codes, ftype="ldd", transform=transform, latlon=True)
    cell_km2 = pyflwdir.gis_utils.reggrid_area(lats, lons) / 1e6

    node_ids = cells["node_id"].to_numpy()
    xs, ys = cells["cell_lon"].to_numpy(), cells["cell_lat"].to_numpy()
    labels = np.arange(1, len(cells) + 1)
    # With all outlets at once, each cell gets the label of the first node downstream of it.
    local_labels = flow.basins(xy=(xs, ys), ids=labels)

    parts = []
    for node_id, x, y, label in zip(node_ids, xs, ys, labels):
        full_mask = flow.basins(xy=([x], [y])) > 0
        parts.append(_cells_in(full_mask, node_id, "catchment", lats, lons, cell_km2))
        parts.append(_cells_in(local_labels == label, node_id, "local", lats, lons, cell_km2))
    return pd.concat(parts, ignore_index=True)


def imerg_cell_weights(catchments: pd.DataFrame) -> pd.DataFrame:
    """Land area (km²) of each catchment inside each 0.1° IMERG cell: node_id, area_type, lat, lon, area_km2.

    Each 0.05° GloFAS cell is assigned to the IMERG cell that contains its centre (by coordinate),
    so four GloFAS cells make one IMERG cell. Weighting by real area keeps cells near the poles from
    counting as much as cells near the equator.
    """
    return (
        catchments.assign(lat=_imerg_centre(catchments["lat"]), lon=_imerg_centre(catchments["lon"]))
        .groupby(["node_id", "area_type", "lat", "lon"], as_index=False, sort=False)["area_km2"]
        .sum()
    )


def _imerg_centre(degrees: pd.Series) -> pd.Series:
    """Centre of the 0.1° IMERG cell containing each coordinate, e.g. 34.125 -> 34.15."""
    return np.round(np.floor(degrees / IMERG_DEG) * IMERG_DEG + IMERG_DEG / 2, 2)


def _cells_in(mask, node_id, area_type, lats, lons, cell_km2) -> pd.DataFrame:
    rows, cols = np.nonzero(mask)
    return pd.DataFrame({
        "node_id": node_id,
        "area_type": area_type,
        "lat": np.round(lats[rows], 3),
        "lon": np.round(lons[cols], 3),
        "area_km2": cell_km2[rows, cols],
    })
