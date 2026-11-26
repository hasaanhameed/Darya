"""Turn averaged IMERG rows into table rows: one per node per day, with version label and quality flags."""

import datetime as dt

import pandas as pd

OUTPUT_COLUMNS = [
    "node_id", "observed_on", "catchment_rainfall_mm", "local_rainfall_mm", "run", "version_label", "flags",
    "source_file",
]
IMERG_RUN = "late"  # the daily Late run (ADR-022)
VERSION_PATTERN = r"\.(V\d+[A-Z]*)[._]"  # ...E235959.V07B.nc4 or ...V07B_precipitation_subsetted.nc4 -> V07B
MIN_COVERAGE = 0.9  # flag a day when under 90% of an area had a rain value


def clean_rainfall(raw: pd.DataFrame, start: dt.date, end: dt.date) -> pd.DataFrame:
    """Keep days start..end, one row per node per day, and flag values without changing them.

    Flags: `low_coverage` (under 90% of the catchment or local area had data),
    `missing_value` (no rain value at all for one of the areas).
    """
    rows = raw[(raw["observed_on"] >= start) & (raw["observed_on"] <= end)]
    rows = rows.assign(version_label=rows["source_file"].str.extract(VERSION_PATTERN, expand=False))
    rows = (
        rows.sort_values(["node_id", "observed_on", "version_label"])
        .drop_duplicates(["node_id", "observed_on"], keep="last")  # a re-released day: keep the newest version
    )

    checks = pd.DataFrame(
        {
            "low_coverage": rows[["catchment_coverage", "local_coverage"]].min(axis=1) < MIN_COVERAGE,
            "missing_value": rows[["catchment_rainfall_mm", "local_rainfall_mm"]].isna().any(axis=1),
        },
        index=rows.index,
    )
    flags = checks.apply(lambda row: [name for name in checks.columns if row[name]], axis=1, result_type="reduce")

    rows = rows.assign(run=IMERG_RUN, flags=flags)
    return rows[OUTPUT_COLUMNS].reset_index(drop=True)
