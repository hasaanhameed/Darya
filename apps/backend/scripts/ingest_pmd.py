"""Read, clean and load the PMD daily rainfall workbook (a one-time historical load, ADR-023/024).

Run from apps/backend:
    python -m scripts.ingest_pmd --dry-run     # write review files to data/pmd/processed/, no database
    python -m scripts.ingest_pmd               # also replace rain_stations and pmd_rainfall in the database
"""

import argparse
import asyncio
from pathlib import Path

import pandas as pd

from app.core.database import SessionLocal, engine
from app.ingest.pmd.cleaning import CleaningReport, clean_rows
from app.ingest.pmd.load_to_db import load_rows
from app.ingest.pmd.sheet_parser import parse_rain_rows, read_rain_sheet
from app.ingest.pmd.station_names import add_station_ids, read_station_catalog

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATA_DIR = REPO_ROOT / "data" / "pmd"


def find_workbook(data_dir: Path) -> Path:
    """The single .xls workbook in the data folder (PMD sent one file)."""
    workbooks = sorted(data_dir.glob("*.xls"))
    if len(workbooks) != 1:
        raise SystemExit(f"Expected exactly one .xls in {data_dir}, found {[p.name for p in workbooks]}. Use --file.")
    return workbooks[0]


def write_review_files(rows: pd.DataFrame, report: CleaningReport, folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    rows.assign(flags=rows["flags"].str.join(";")).to_csv(folder / "review.csv", index=False)
    report.impossible_day_values.to_csv(folder / "impossible_day_values.csv", index=False)
    report.duplicate_conflicts.to_csv(folder / "duplicate_conflicts.csv", index=False)


def print_summary(cells: pd.DataFrame, rows: pd.DataFrame, report: CleaningReport) -> None:
    print(f"Station-months read: {cells['sheet_row'].nunique()} ({cells['station'].nunique()} names as written)")
    print(f"Blank cells on real days (no row): {report.blank_cells}")
    print(f"Filled cells on days that don't exist (not stored): {report.impossible_day_cells}")
    print(f"  of which non-zero numbers: {len(report.impossible_day_values)}")
    print(f"Duplicate station-months: {report.identical_duplicate_months} identical (merged), "
          f"{len(report.duplicate_conflicts)} differing (first copy kept and flagged)")
    print(f"Rows kept: {len(rows)} ({rows['station_id'].nunique()} stations, "
          f"{rows['observed_on'].min()} to {rows['observed_on'].max()})")
    print(f"Rows with a number: {rows['rainfall_mm'].notna().sum()}, with no flags: {(rows['flags'].str.len() == 0).sum()}")
    print("Rows per flag:")
    print(rows["flags"].explode().value_counts().sort_index().to_string())


async def load_into_database(stations: pd.DataFrame, rows: pd.DataFrame) -> int:
    async with SessionLocal() as session:
        inserted = await load_rows(session, stations, rows)
    await engine.dispose()
    return inserted


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR, help="folder with the PMD workbook")
    parser.add_argument("--file", type=Path, help="the workbook to read (default: the only .xls in --data-dir)")
    parser.add_argument("--dry-run", action="store_true", help="write review files instead of loading the database")
    args = parser.parse_args()

    workbook = args.file or find_workbook(args.data_dir)
    stations = read_station_catalog()
    cells = parse_rain_rows(read_rain_sheet(workbook), workbook.name)
    cells = add_station_ids(cells, stations)
    rows, report = clean_rows(cells)
    print_summary(cells, rows, report)

    review_folder = args.data_dir / "processed"
    write_review_files(rows, report, review_folder)
    print(f"Review files: {review_folder} (review.csv, impossible_day_values.csv, duplicate_conflicts.csv)")

    if not args.dry_run:
        # parsing and cleaning above are blocking pandas work, so only the database step runs async
        inserted = asyncio.run(load_into_database(stations, rows))
        print(f"Loaded {len(stations)} stations into rain_stations and {inserted} rows into pmd_rainfall")


if __name__ == "__main__":
    main()
