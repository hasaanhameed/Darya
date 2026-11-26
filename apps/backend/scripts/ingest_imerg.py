"""Download, average, clean and load IMERG daily Late rainfall for every node (ADR-022).

Needs EARTHDATA_USERNAME / EARTHDATA_PASSWORD in apps/backend/.env (with the "NASA GESDISC DATA ARCHIVE"
application approved in the Earthdata profile) unless every day is already downloaded, and
data/imerg/processed/catchment_weights.csv (python -m scripts.build_node_catchments).
Files go to data/imerg/raw/ and are reused.

Run from apps/backend:
    python -m scripts.ingest_imerg --start 2015-01-01 --dry-run   # write data/imerg/processed/review.csv only
    python -m scripts.ingest_imerg --start 2015-01-01              # also replace those days in imerg_rainfall
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
from app.ingest.imerg.catchment_averager import average_over_catchments
from app.ingest.imerg.cleaning import clean_rainfall
from app.ingest.imerg.file_downloader import download_missing, downloaded_files, make_client
from app.ingest.imerg.load_to_db import load_rows

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATA_DIR = REPO_ROOT / "data" / "imerg"
LATE_RUN_DELAY_DAYS = 2  # the Late run appears ~14 h after the UTC day ends


def download_files(start: dt.date, end: dt.date, raw_dir: Path) -> list[Path]:
    files = downloaded_files(raw_dir, start, end)
    if len(files) == (end - start).days + 1:
        return files
    if not (settings.earthdata_username and settings.earthdata_password):
        sys.exit("EARTHDATA_USERNAME / EARTHDATA_PASSWORD are not set in apps/backend/.env (see .env.example)")
    print("Downloading missing days through NASA Harmony (one job per month; each job is queued)")
    client = make_client(settings.earthdata_username, settings.earthdata_password)
    return download_missing(client, start, end, raw_dir)


def read_files(paths: list[Path], weights: pd.DataFrame) -> pd.DataFrame:
    parts = []
    for path in paths:
        with xr.open_dataset(path) as dataset:
            parts.append(average_over_catchments(dataset, weights, path.name))
    return pd.concat(parts, ignore_index=True)


def print_summary(rows: pd.DataFrame) -> None:
    print(f"Rows: {len(rows)} ({rows['node_id'].nunique()} nodes, {rows['observed_on'].nunique()} days, "
          f"{rows['observed_on'].min()} to {rows['observed_on'].max()})")
    print("Rows per version label:")
    print(rows["version_label"].value_counts(dropna=False).to_string())
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
                        default=dt.date.today() - dt.timedelta(days=LATE_RUN_DELAY_DAYS), help="last day (YYYY-MM-DD)")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--dry-run", action="store_true", help="write a review CSV instead of loading the database")
    args = parser.parse_args()

    weights_file = args.data_dir / "processed" / "catchment_weights.csv"
    if not weights_file.exists():
        sys.exit(f"{weights_file} is missing; run: python -m scripts.build_node_catchments")
    weights = pd.read_csv(weights_file)

    paths = download_files(args.start, args.end, args.data_dir / "raw")
    raw = read_files(paths, weights)
    rows = clean_rainfall(raw, args.start, args.end)
    print_summary(rows)

    review_file = args.data_dir / "processed" / "review.csv"
    write_review_file(rows, review_file)
    print(f"Review file: {review_file}")

    if not args.dry_run:
        # downloading and averaging above are blocking work, so only the database step runs async
        inserted = asyncio.run(load_into_database(rows, args.start, args.end))
        print(f"Loaded {inserted} rows into imerg_rainfall")


if __name__ == "__main__":
    main()
