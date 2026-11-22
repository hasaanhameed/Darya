import datetime as dt
from pathlib import Path

import pytest

from app.ingest.glofas.file_downloader import download_missing
from app.ingest.glofas.request_builder import GLOFAS_DATASET, plan_downloads


class FakeClient:
    """Stands in for cdsapi.Client: records requests and writes a small file instead of downloading."""

    def __init__(self, fail=False):
        self.calls = []
        self.fail = fail

    def retrieve(self, dataset, request, target):
        self.calls.append((dataset, request))
        Path(target).write_bytes(b"partial")
        if self.fail:
            raise RuntimeError("connection lost")


DOWNLOADS = plan_downloads(dt.date(2015, 1, 1), dt.date(2016, 1, 31))  # two files


def test_downloads_each_file_into_the_folder(tmp_path):
    client = FakeClient()

    paths = download_missing(client, DOWNLOADS, tmp_path)

    assert paths == [tmp_path / d.file_name for d in DOWNLOADS]
    assert all(path.exists() for path in paths)
    assert client.calls == [(GLOFAS_DATASET, d.request) for d in DOWNLOADS]


def test_skips_files_already_downloaded(tmp_path):
    (tmp_path / DOWNLOADS[0].file_name).write_bytes(b"done")
    client = FakeClient()

    download_missing(client, DOWNLOADS, tmp_path)

    assert client.calls == [(GLOFAS_DATASET, DOWNLOADS[1].request)]


def test_failed_download_leaves_no_file_behind(tmp_path):
    with pytest.raises(RuntimeError):
        download_missing(FakeClient(fail=True), DOWNLOADS, tmp_path)

    assert list(tmp_path.iterdir()) == []
