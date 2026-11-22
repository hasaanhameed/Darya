"""Read daily discharge at each node's grid cell from a GloFAS NetCDF file into a DataFrame."""

import pandas as pd
import xarray as xr

DISCHARGE_VARIABLE = "avg_dis"  # "Time-mean discharge from rivers or streams" over 24 hours, m³/s
TIME_NAMES = ("valid_time", "time")  # EWDS NetCDF files use valid_time; older files use time
CELL_TOLERANCE_DEG = 0.03  # a matched cell must be in the file (grid spacing is 0.05°)


def read_discharge(dataset: xr.Dataset, cells: pd.DataFrame, product_type: str, source_file: str) -> pd.DataFrame:
    """One row per node per day: node_id, observed_on, discharge_m3s, product_type, source_file.

    `cells` holds node_id, cell_lat, cell_lon (see grid_cell_matcher).
    GloFAS stamps each value at 00 UTC at the END of its 24 hours, so a value stamped
    29 Aug 00:00 is the mean for 28 Aug, and is stored under 28 Aug. (Asking EWDS for
    day 28 Aug returns the value stamped 29 Aug 00:00, checked on a real file.)
    """
    time_name = next(name for name in TIME_NAMES if name in dataset.coords)
    points = dataset[DISCHARGE_VARIABLE].sel(
        latitude=xr.DataArray(cells["cell_lat"].to_numpy(), dims="node"),
        longitude=xr.DataArray(cells["cell_lon"].to_numpy(), dims="node"),
        method="nearest",
        tolerance=CELL_TOLERANCE_DEG,
    )
    points = points.assign_coords(node=cells["node_id"].to_numpy())

    rows = points.to_dataframe(name="discharge_m3s").reset_index()
    rows["observed_on"] = (pd.to_datetime(rows[time_name]) - pd.Timedelta(days=1)).dt.date
    rows = rows.rename(columns={"node": "node_id"}).assign(product_type=product_type, source_file=source_file)
    return rows[["node_id", "observed_on", "discharge_m3s", "product_type", "source_file"]]
