import datetime as dt
from concurrent.futures import Future
from pathlib import Path

import pytest

from app.ingest.imerg.file_downloader import day_of_file, download_missing

AUG_1, AUG_2, AUG_3 = dt.date(2022, 8, 1), dt.date(2022, 8, 2), dt.date(2022, 8, 3)


def imerg_name(day: dt.date) -> str:
    return f"3B-DAY-L.MS.MRG.3IMERG.{day:%Y%m%d}-S000000-E235959.V07B.nc4"


class FakeHarmonyClient:
    """Stands in for harmony.Client: records requests and 'downloads' one small file per requested day."""

    def __init__(self, fail=False, failures_before_success=0):
        self.requests = []
        self.fail = fail
        self.failures_left = failures_before_success

    def submit(self, request):
        self.requests.append(request)
        return f"job-{len(self.requests)}"

    def wait_for_processing(self, job_id, show_progress=False):
        pass

    def download_all(self, job_id, directory, overwrite=False):
        request = self.requests[int(job_id.split("-")[1]) - 1]
        failing = self.fail or self.failures_left > 0
        self.failures_left = max(self.failures_left - 1, 0)
        day = request.temporal["start"].date()
        while day <= request.temporal["stop"].date():
            path = Path(directory) / imerg_name(day)
            path.write_bytes(b"data")
            future = Future()
            future.set_exception(OSError("connection lost")) if failing else future.set_result(str(path))
            yield future
            day += dt.timedelta(days=1)


def requested_days(request):
    return request.temporal["start"].date(), request.temporal["stop"].date()


def test_reads_the_day_from_an_imerg_file_name():
    assert day_of_file(imerg_name(AUG_2)) == AUG_2
    assert day_of_file("notes.txt") is None


def test_downloads_every_day_into_the_folder(tmp_path):
    client = FakeHarmonyClient()

    paths = download_missing(client, AUG_1, AUG_3, tmp_path)

    assert paths == [tmp_path / imerg_name(day) for day in (AUG_1, AUG_2, AUG_3)]
    assert [requested_days(r) for r in client.requests] == [(AUG_1, AUG_3)]


def test_asks_only_for_days_not_yet_downloaded(tmp_path):
    (tmp_path / imerg_name(AUG_1)).write_bytes(b"done")
    client = FakeHarmonyClient()

    paths = download_missing(client, AUG_1, AUG_3, tmp_path)

    assert [requested_days(r) for r in client.requests] == [(AUG_2, AUG_3)]
    assert len(paths) == 3


def test_makes_no_request_when_everything_is_downloaded(tmp_path):
    for day in (AUG_1, AUG_2):
        (tmp_path / imerg_name(day)).write_bytes(b"done")
    client = FakeHarmonyClient()

    download_missing(client, AUG_1, AUG_2, tmp_path)

    assert client.requests == []


def test_makes_one_request_per_month(tmp_path):
    client = FakeHarmonyClient()

    download_missing(client, dt.date(2022, 7, 31), AUG_1, tmp_path)

    assert [requested_days(r) for r in client.requests] == [(dt.date(2022, 7, 31),) * 2, (AUG_1, AUG_1)]


def test_retries_a_job_after_a_network_error(tmp_path):
    client = FakeHarmonyClient(failures_before_success=1)

    paths = download_missing(client, AUG_1, AUG_3, tmp_path, retry_wait_seconds=0)

    assert len(paths) == 3
    assert len(client.requests) == 2


def test_failed_download_leaves_no_files_behind(tmp_path):
    with pytest.raises(OSError):
        download_missing(FakeHarmonyClient(fail=True), AUG_1, AUG_3, tmp_path, retry_wait_seconds=0)

    assert list(tmp_path.iterdir()) == []
