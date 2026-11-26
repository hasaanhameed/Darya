"""Download IMERG daily files (already cut to our area) through NASA Harmony, skipping days we have."""

import datetime as dt
import re
import shutil
from pathlib import Path

from harmony import Client

from app.ingest.imerg.request_builder import build_request, split_into_months

# IMERG file names carry the day, e.g. 3B-DAY-L.MS.MRG.3IMERG.20220801-S000000-E235959.V07B.nc4
FILE_DAY_PATTERN = re.compile(r"\.(\d{8})-S\d{6}")
PARTIAL_FOLDER = ".partial"


def make_client(username: str, password: str) -> Client:
    return Client(auth=(username, password))


def day_of_file(name: str) -> dt.date | None:
    match = FILE_DAY_PATTERN.search(name)
    return dt.datetime.strptime(match.group(1), "%Y%m%d").date() if match else None


def download_missing(client: Client, start: dt.date, end: dt.date, folder: Path) -> list[Path]:
    """Download the days start..end not yet in `folder` (one Harmony job per month).

    Returns the files for all days start..end that are in `folder` afterwards, sorted by day.
    Files are downloaded into a temporary folder and moved in only when the whole job succeeded,
    so an interrupted download never looks like a finished file.
    """
    folder.mkdir(parents=True, exist_ok=True)
    for first, last in split_into_months(start, end):
        have = set(_files_by_day(folder))
        missing = [day for day in _days(first, last) if day not in have]
        if missing:
            _download_job(client, min(missing), max(missing), folder)

    return downloaded_files(folder, start, end)


def downloaded_files(folder: Path, start: dt.date, end: dt.date) -> list[Path]:
    """The files in `folder` for days start..end, sorted by day."""
    files = _files_by_day(folder) if folder.exists() else {}
    return [files[day] for day in sorted(files) if start <= day <= end]


def _download_job(client: Client, first: dt.date, last: dt.date, folder: Path) -> None:
    partial = folder / PARTIAL_FOLDER
    shutil.rmtree(partial, ignore_errors=True)
    partial.mkdir()
    try:
        job_id = client.submit(build_request(first, last))
        client.wait_for_processing(job_id, show_progress=False)
        for future in client.download_all(job_id, directory=str(partial), overwrite=True):
            future.result()  # raises if that file failed
        for path in partial.iterdir():
            path.replace(folder / path.name)
    finally:
        shutil.rmtree(partial, ignore_errors=True)


def _files_by_day(folder: Path) -> dict[dt.date, Path]:
    return {day: path for path in folder.iterdir() if path.is_file() and (day := day_of_file(path.name))}


def _days(first: dt.date, last: dt.date) -> list[dt.date]:
    return [first + dt.timedelta(days=n) for n in range((last - first).days + 1)]
