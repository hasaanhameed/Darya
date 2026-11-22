"""Match every node to its GloFAS grid cell and write app/ingest/glofas/node_grid_cells.csv (run once).

Needs data/glofas/raw/uparea_glofas_v4_0.nc (ECMWF Confluence, CEMS "Auxiliary Data" page).
Review the output by hand before committing it: see docs/DATA.md "GloFAS".

Run from apps/backend:
    python -m scripts.match_glofas_cells
"""

import argparse
import asyncio
from pathlib import Path

import pandas as pd
import xarray as xr
from sqlalchemy import select

from app.core.database import SessionLocal, engine
from app.ingest.glofas.grid_cell_matcher import match_nodes_to_cells
from app.models import Node

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_UPAREA_FILE = REPO_ROOT / "data" / "glofas" / "raw" / "uparea_glofas_v4_0.nc"
NODE_GRID_CELLS_FILE = Path(__file__).resolve().parents[1] / "app" / "ingest" / "glofas" / "node_grid_cells.csv"

# Cells chosen by hand after looking at the upstream-area grid around the node (docs/DATA.md "GloFAS").
MANUAL_CELLS = {
    # The node sits where the Chenab (158k km²) and Sutlej (121k km²) meet; the headworks is below the junction.
    "panjnad": (29.325, 71.025),
    # GloFAS's 5 km river map joins the Chenab into the Jhelum at Rasul (73k km²); in reality they meet
    # at Trimmu. Use the Jhelum cell just above that false junction (38k km²).
    "rasul": (32.725, 73.575),
}


async def read_nodes() -> pd.DataFrame:
    async with SessionLocal() as session:
        nodes = (await session.execute(select(Node.id, Node.lat, Node.lon).order_by(Node.id))).all()
    await engine.dispose()
    return pd.DataFrame(nodes, columns=["node_id", "lat", "lon"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--uparea-file", type=Path, default=DEFAULT_UPAREA_FILE)
    args = parser.parse_args()

    nodes = asyncio.run(read_nodes())
    with xr.open_dataset(args.uparea_file) as dataset:
        matches = match_nodes_to_cells(dataset["uparea"], nodes, MANUAL_CELLS)

    matches.to_csv(NODE_GRID_CELLS_FILE, index=False)
    print(matches.to_string(index=False))
    print(f"Wrote {NODE_GRID_CELLS_FILE}")


if __name__ == "__main__":
    main()
