"""Average one IMERG daily rain grid over each node's catchment and local area."""

import numpy as np
import pandas as pd
import xarray as xr

RAIN_VARIABLE = "precipitation"  # mm/day; IMERG marks missing cells with -9999.9


def average_over_catchments(dataset: xr.Dataset, weights: pd.DataFrame, source_file: str) -> pd.DataFrame:
    """One row per node per day: node_id, observed_on, catchment_rainfall_mm, local_rainfall_mm,
    catchment_coverage, local_coverage, source_file.

    `weights` comes from catchment_builder.imerg_cell_weights (node_id, area_type, lat, lon, area_km2).
    Each average is weighted by the land area of the catchment inside each IMERG cell. Missing cells
    are left out; coverage is the share of the area that had a value (1.0 = every cell).
    """
    grid = dataset[RAIN_VARIABLE].to_dataframe().reset_index()
    grid = grid.assign(
        observed_on=pd.to_datetime(grid["time"]).dt.date,
        # float64 first: IMERG stores lon as float32, where 72.05 is really 72.0500030517578
        lat=grid["lat"].astype("float64").round(2),
        lon=grid["lon"].astype("float64").round(2),
        rain_mm=grid[RAIN_VARIABLE].where(grid[RAIN_VARIABLE] >= 0),  # fill values (-9999.9) -> missing
    )

    # Every catchment cell on every day; cells the file doesn't cover stay in, with no rain value.
    days = pd.DataFrame({"observed_on": grid["observed_on"].unique()})
    cells = weights.merge(days, how="cross").merge(
        grid[["observed_on", "lat", "lon", "rain_mm"]], on=["observed_on", "lat", "lon"], how="left"
    )
    has_value = cells["rain_mm"].notna()
    cells = cells.assign(
        rain_times_area=(cells["rain_mm"] * cells["area_km2"]).where(has_value, 0.0),
        area_with_value_km2=cells["area_km2"].where(has_value, 0.0),
    )
    sums = cells.groupby(["node_id", "observed_on", "area_type"], as_index=False)[
        ["rain_times_area", "area_with_value_km2", "area_km2"]
    ].sum()
    with np.errstate(invalid="ignore", divide="ignore"):
        sums["rainfall_mm"] = sums["rain_times_area"] / sums["area_with_value_km2"].replace(0, np.nan)
    sums["coverage"] = sums["area_with_value_km2"] / sums["area_km2"]

    wide = sums.pivot(index=["node_id", "observed_on"], columns="area_type", values=["rainfall_mm", "coverage"])
    rows = pd.DataFrame({
        "catchment_rainfall_mm": wide[("rainfall_mm", "catchment")],
        "local_rainfall_mm": wide[("rainfall_mm", "local")],
        "catchment_coverage": wide[("coverage", "catchment")],
        "local_coverage": wide[("coverage", "local")],
    }).reset_index()
    return rows.assign(source_file=source_file)
