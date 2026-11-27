"""Download IMERG daily files (already cut to our area) through NASA Harmony, skipping days we have."""

import datetime as dt
import re
import shutil
import time
from pathlib import Path

from harmony import Client

from app.ingest.imerg.request_builder import build_request, split_into_months

# IMERG file names carry the day, e.g. 3B-DAY-L.MS.MRG.3IMERG.20220801-S000000-E235959.V07B.nc4
FILE_DAY_PATTERN = re.compile(r"\.(\d{8})-S\d{6}")
PARTIAL_FOLDER = ".partial"
JOB_ATTEMPTS = 3  # a short network drop shouldn't end a download that runs for hours
RETRY_WAIT_SECONDS = 60


def make_client(username: str, password: str) -> Client:
    return Client(auth=(username, password))


def day_of_file(name: str) -> dt.date | None:
    match = FILE_DAY_PATTERN.search(name)
    return dt.datetime.strptime(match.group(1), "%Y%m%d").date() if match else None


def download_missing(
    client: Client, start: dt.date, end: dt.date, folder: Path, retry_wait_seconds: float = RETRY_WAIT_SECONDS
) -> list[Path]:
    """Download the days start..end not yet in `folder` (one Harmony job per month).

    Returns the files for all days start..end that are in `folder` afterwards, sorted by day.
    Files are downloaded into a temporary folder and moved in only when the whole job succeeded,
    so an interrupted download never looks like a finished file. A failed job is tried again
    (JOB_ATTEMPTS in all) after a pause, since most failures are short network drops.
    """
    folder.mkdir(parents=True, exist_ok=True)
    for first, last in split_into_months(start, end):
        have = set(_files_by_day(folder))
        missing = [day for day in _days(first, last) if day not in have]
        if missing:
            _download_job_with_retries(client, min(missing), max(missing), folder, retry_wait_seconds)

    return downloaded_files(folder, start, end)


def downloaded_files(folder: Path, start: dt.date, end: dt.date) -> list[Path]:
    """The files in `folder` for days start..end, sorted by day."""
    files = _files_by_day(folder) if folder.exists() else {}
    return [files[day] for day in sorted(files) if start <= day <= end]


def _download_job_with_retries(client: Client, first: dt.date, last: dt.date, folder: Path, wait: float) -> None:
    for attempt in range(1, JOB_ATTEMPTS + 1):
        try:
            _download_job(client, first, last, folder)
            return
        except OSError as error:  # network errors (requests' ConnectionError is an OSError)
            if attempt == JOB_ATTEMPTS:
                raise
            print(f"Download of {first}..{last} failed ({error.__class__.__name__}); retrying in {wait:.0f} s")
            time.sleep(wait)


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
