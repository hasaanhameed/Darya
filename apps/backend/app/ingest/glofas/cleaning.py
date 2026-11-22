"""Turn raw GloFAS rows into table rows: one per node per day, with quality flags."""

import datetime as dt

import pandas as pd

from app.ingest.glofas.request_builder import SYSTEM_VERSION

OUTPUT_COLUMNS = [
    "node_id", "observed_on", "discharge_m3s", "product_type", "system_version", "flags", "source_file",
]
PRODUCT_PRIORITY = {"consolidated": 0, "intermediate": 1}  # consolidated (final ERA5) wins over intermediate


def clean_discharge(raw: pd.DataFrame, start: dt.date, end: dt.date) -> pd.DataFrame:
    """Keep days start..end, one row per node per day, and flag values without changing them.

    Flags: `missing_value` (no value in the file), `negative_value` (below zero, not physical).
    """
    rows = raw[(raw["observed_on"] >= start) & (raw["observed_on"] <= end)]
    rows = (
        rows.assign(priority=rows["product_type"].map(PRODUCT_PRIORITY))
        .sort_values(["node_id", "observed_on", "priority"])
        .drop_duplicates(["node_id", "observed_on"], keep="first")
    )

    checks = pd.DataFrame(
        {"missing_value": rows["discharge_m3s"].isna(), "negative_value": rows["discharge_m3s"] < 0},
        index=rows.index,
    )
    flags = checks.apply(lambda row: [name for name in checks.columns if row[name]], axis=1, result_type="reduce")

    rows = rows.assign(system_version=SYSTEM_VERSION, flags=flags)
    return rows[OUTPUT_COLUMNS].reset_index(drop=True)
