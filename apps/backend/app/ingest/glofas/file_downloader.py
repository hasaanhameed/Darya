"""Download the planned GloFAS files from Copernicus EWDS, skipping files we already have."""

from pathlib import Path

import cdsapi

from app.ingest.glofas.request_builder import GLOFAS_DATASET, Download

EWDS_URL = "https://ewds.climate.copernicus.eu/api"


def make_client(api_key: str) -> cdsapi.Client:
    return cdsapi.Client(url=EWDS_URL, key=api_key)


def download_missing(client: cdsapi.Client, downloads: list[Download], folder: Path) -> list[Path]:
    """Download every planned file not yet in `folder`. Returns the paths of all planned files.

    Each file is written under a temporary name and renamed when complete,
    so an interrupted download never looks like a finished file.
    """
    folder.mkdir(parents=True, exist_ok=True)
    paths = []
    for download in downloads:
        target = folder / download.file_name
        if not target.exists():
            partial = target.with_name(target.name + ".part")
            try:
                client.retrieve(GLOFAS_DATASET, download.request, str(partial))
            except Exception:
                partial.unlink(missing_ok=True)
                raise
            partial.replace(target)
        paths.append(target)
    return paths
