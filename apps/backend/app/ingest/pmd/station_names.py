"""Match PMD station names, as written in the workbook, to our rain station catalog (ADR-023)."""

from pathlib import Path

import pandas as pd

STATION_CATALOG_FILE = Path(__file__).with_name("rain_stations.csv")

# Names that are the same gauge written another way (after spaces are normalised) → catalog name.
# "LAHORE, UPPER MALL" continues "LAHORE UPPER MALL" from Aug 2015, with no overlapping months.
NAME_ALIASES = {
    "LAHORE, UPPER MALL": "LAHORE UPPER MALL",
}


def read_station_catalog(path: Path = STATION_CATALOG_FILE) -> pd.DataFrame:
    """The committed station catalog: id, pmd_name, name, lat, lon, province, basin."""
    return pd.read_csv(path, dtype={"id": str, "pmd_name": str})


def normalise_names(names: pd.Series) -> pd.Series:
    """Upper-case, trim and collapse repeated spaces, then apply the aliases."""
    normalised = names.str.upper().str.split().str.join(" ")
    return normalised.replace(NAME_ALIASES)


def add_station_ids(rows: pd.DataFrame, catalog: pd.DataFrame) -> pd.DataFrame:
    """Add a `station_id` column matched from the `station` column. Unknown names raise ValueError."""
    id_by_name = catalog.set_index("pmd_name")["id"]
    station_ids = normalise_names(rows["station"]).map(id_by_name)

    unknown = sorted(rows.loc[station_ids.isna(), "station"].unique())
    if unknown:
        raise ValueError(f"Station names not in rain_stations.csv: {unknown}")
    return rows.assign(station_id=station_ids)
