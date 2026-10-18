"""Read, clean and load the WAPDA daily reports (a one-time historical load).

Run from apps/backend:
    python -m scripts.ingest_wapda --dry-run     # write data/wapda/processed/review.csv, no database
"""

import argparse
from collections import defaultdict
from pathlib import Path

import pandas as pd

from app.ingest.wapda.cleaning import CleaningReport, clean_sheets
from app.ingest.wapda.sheet_finder import find_day_sheets
from app.ingest.wapda.sheet_parser import parse_sheet, read_grids

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATA_DIR = REPO_ROOT / "data" / "wapda"


def read_all_sheets(data_dir: Path) -> tuple[pd.DataFrame, list[Path]]:
    """Parse every day sheet into one DataFrame of raw station rows."""
    day_sheets, unreadable = find_day_sheets(data_dir)

    sheets_by_file = defaultdict(list)
    for day_sheet in day_sheets:
        sheets_by_file[day_sheet.path].append(day_sheet)

    parsed = []
    for path, sheets in sheets_by_file.items():
        grids = read_grids(path, [s.sheet for s in sheets])
        parsed.extend(parse_sheet(grids[s.sheet], s) for s in sheets)
    return pd.concat(parsed, ignore_index=True), unreadable


def write_review_file(rows: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows.assign(flags=rows["flags"].str.join(";")).to_csv(path, index=False)


def print_summary(raw: pd.DataFrame, unreadable: list[Path], rows: pd.DataFrame, report: CleaningReport) -> None:
    sheets = raw.drop_duplicates(["source_file", "sheet"])
    print(f"Sheets read: {len(sheets)}")
    print(f"Unreadable files: {len(unreadable)} {[p.name for p in unreadable]}")
    print(f"Sheets whose date matches: {(sheets['date_in_sheet'] == sheets['expected_date']).sum()}")
    print(f"Stale copies skipped: {len(report.stale_copies)}")
    print(f"Conflicts (two sheets for one day): {len(report.conflicts)}")
    for conflict in report.conflicts:
        print(f"  {conflict}")
    print(f"Rows kept: {len(rows)} ({rows['observed_on'].nunique()} days)")
    print("Rows per flag:")
    print(rows["flags"].explode().value_counts().sort_index().to_string())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR, help="folder with the extracted workbooks")
    parser.add_argument("--dry-run", action="store_true", help="write a review CSV instead of loading the database")
    args = parser.parse_args()

    if not args.dry_run:
        raise SystemExit("Loading into the database isn't built yet. Use --dry-run.")

    raw, unreadable = read_all_sheets(args.data_dir)
    rows, report = clean_sheets(raw)
    print_summary(raw, unreadable, rows, report)

    review_file = args.data_dir / "processed" / "review.csv"
    write_review_file(rows, review_file)
    print(f"Review file: {review_file}")


if __name__ == "__main__":
    main()
