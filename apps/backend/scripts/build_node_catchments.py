"""Trace every node's catchment on GloFAS's river map and write the IMERG cell weights (run once, ADR-022).

Needs data/glofas/raw/ldd_glofas_v4_0.nc (ECMWF Confluence, CEMS "Auxiliary Data" page) and
app/ingest/glofas/node_grid_cells.csv. Writes data/imerg/processed/catchment_weights.csv.

Run from apps/backend:
    python -m scripts.build_node_catchments
"""

import argparse
import sys
from pathlib import Path

import pandas as pd
import xarray as xr

from app.ingest.imerg.catchment_builder import imerg_cell_weights, trace_catchments
from app.ingest.imerg.request_builder import BBOX

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_LDD_FILE = REPO_ROOT / "data" / "glofas" / "raw" / "ldd_glofas_v4_0.nc"
NODE_GRID_CELLS_FILE = Path(__file__).resolve().parents[1] / "app" / "ingest" / "glofas" / "node_grid_cells.csv"
WEIGHTS_FILE = REPO_ROOT / "data" / "imerg" / "processed" / "catchment_weights.csv"
# Trace on a window wider than the IMERG area, so a catchment running past it would show up in the check below.
TRACE_WINDOW = {"lat": slice(42, 20), "lon": slice(55, 90)}


def print_summary(weights: pd.DataFrame, cells: pd.DataFrame) -> None:
    areas = weights.pivot_table(index="node_id", columns="area_type", values="area_km2", aggfunc="sum").round()
    areas = areas.join(cells.set_index("node_id")["upstream_area_km2"].rename("glofas_upstream_km2"))
    areas["catchment_vs_glofas_pct"] = (100 * (areas["catchment"] / areas["glofas_upstream_km2"] - 1)).round(2)
    print(areas.to_string())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ldd-file", type=Path, default=DEFAULT_LDD_FILE)
    args = parser.parse_args()

    cells = pd.read_csv(NODE_GRID_CELLS_FILE)
    with xr.open_dataset(args.ldd_file) as dataset:
        ldd = dataset["ldd"].sel(TRACE_WINDOW).load()
    weights = imerg_cell_weights(trace_catchments(ldd, cells))

    west, south, east, north = BBOX
    outside = weights[~weights["lat"].between(south, north) | ~weights["lon"].between(west, east)]
    if len(outside):
        sys.exit(f"{len(outside)} catchment cells fall outside the IMERG area {BBOX}; widen BBOX in request_builder.py")

    print_summary(weights, cells)
    WEIGHTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    weights.to_csv(WEIGHTS_FILE, index=False)
    print(f"Wrote {len(weights)} rows to {WEIGHTS_FILE}")


if __name__ == "__main__":
    main()
