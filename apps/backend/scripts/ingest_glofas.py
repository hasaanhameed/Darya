"""Download, read, clean and load GloFAS v4.0 reanalysis discharge for every node (ADR-021).

Needs EWDS_API_KEY in apps/backend/.env (and the CEMS-FLOODS licence accepted on the EWDS site)
unless every file is already downloaded. Files go to data/glofas/raw/<version>/ and are reused.

Run from apps/backend:
    python -m scripts.ingest_glofas --start 2015-01-01 --dry-run   # write data/glofas/processed/review.csv only
    python -m scripts.ingest_glofas --start 2015-01-01              # also replace those days in glofas_discharge
"""

import argparse
import asyncio
import datetime as dt
import sys
from pathlib import Path

import pandas as pd
import xarray as xr

from app.core.config import settings
from app.core.database import SessionLocal, engine
from app.ingest.glofas.cleaning import clean_discharge
from app.ingest.glofas.file_downloader import download_missing, make_client
from app.ingest.glofas.grid_reader import read_discharge
from app.ingest.glofas.load_to_db import load_rows
from app.ingest.glofas.request_builder import SYSTEM_VERSION, Download, plan_downloads

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATA_DIR = REPO_ROOT / "data" / "glofas"
NODE_GRID_CELLS_FILE = Path(__file__).resolve().parents[1] / "app" / "ingest" / "glofas" / "node_grid_cells.csv"
INTERMEDIATE_DELAY_DAYS = 5  # intermediate data is about 4 days behind real time


def download_files(downloads: list[Download], raw_dir: Path) -> list[Path]:
    missing = [d for d in downloads if not (raw_dir / d.file_name).exists()]
    if not missing:
        return [raw_dir / d.file_name for d in downloads]
    if not settings.ewds_api_key:
        sys.exit("EWDS_API_KEY is not set in apps/backend/.env (see .env.example)")
    print(f"Downloading {len(missing)} of {len(downloads)} files (EWDS queues each request; this can take a while)")
    return download_missing(make_client(settings.ewds_api_key), downloads, raw_dir)


def read_files(downloads: list[Download], paths: list[Path], cells: pd.DataFrame) -> pd.DataFrame:
    parts = []
    for download, path in zip(downloads, paths):
        with xr.open_dataset(path) as dataset:
            parts.append(read_discharge(dataset, cells, download.product_type, download.file_name))
    return pd.concat(parts, ignore_index=True)


def print_summary(rows: pd.DataFrame) -> None:
    print(f"Rows: {len(rows)} ({rows['node_id'].nunique()} nodes, {rows['observed_on'].nunique()} days, "
          f"{rows['observed_on'].min()} to {rows['observed_on'].max()})")
    print("Rows per product:")
    print(rows["product_type"].value_counts().to_string())
    print("Rows per flag:")
    print(rows["flags"].explode().value_counts().to_string() if rows["flags"].str.len().any() else "(none)")


def write_review_file(rows: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows.assign(flags=rows["flags"].str.join(";")).to_csv(path, index=False)


async def load_into_database(rows: pd.DataFrame, start: dt.date, end: dt.date) -> int:
    async with SessionLocal() as session:
        inserted = await load_rows(session, rows, start, end)
    await engine.dispose()
    return inserted


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--start", type=dt.date.fromisoformat, default=dt.date(2015, 1, 1), help="first day (YYYY-MM-DD)")
    parser.add_argument("--end", type=dt.date.fromisoformat,
                        default=dt.date.today() - dt.timedelta(days=INTERMEDIATE_DELAY_DAYS), help="last day (YYYY-MM-DD)")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--dry-run", action="store_true", help="write a review CSV instead of loading the database")
    args = parser.parse_args()

    cells = pd.read_csv(NODE_GRID_CELLS_FILE)
    downloads = plan_downloads(args.start, args.end)  # EWDS days are the days the 24-hour means cover
    paths = download_files(downloads, args.data_dir / "raw" / SYSTEM_VERSION)

    raw = read_files(downloads, paths, cells)
    rows = clean_discharge(raw, args.start, args.end)
    print_summary(rows)

    review_file = args.data_dir / "processed" / "review.csv"
    write_review_file(rows, review_file)
    print(f"Review file: {review_file}")

    if not args.dry_run:
        # downloading and reading above are blocking work, so only the database step runs async
        inserted = asyncio.run(load_into_database(rows, args.start, args.end))
        print(f"Loaded {inserted} rows into glofas_discharge")


if __name__ == "__main__":
    main()
