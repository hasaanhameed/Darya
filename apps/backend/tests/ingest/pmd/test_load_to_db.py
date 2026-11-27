"""The loader replaces both PMD tables. These tests run inside the rolled-back `db_session`,
so the real stations and rainfall are never changed, and they use made-up station ids."""

import datetime as dt

import pandas as pd
import pytest
from sqlalchemy import func, select

from app.ingest.pmd.load_to_db import load_rows
from app.models import PmdRainfall, RainStation

pytestmark = [pytest.mark.anyio, pytest.mark.integration]

SOURCE_FILE = "DAILY RAIN - ALL STATIONS - 1981-2015.xls"


def stations() -> pd.DataFrame:
    """Shaped like rain_stations.csv."""
    return pd.DataFrame(
        [
            {"id": "test_station_x", "pmd_name": "TEST STATION X", "name": "Test Station X",
             "lat": 33.6, "lon": 73.1, "province": "ICT", "basin": "indus"},
            {"id": "test_station_y", "pmd_name": "TEST STATION Y", "name": "Test Station Y",
             "lat": 25.1, "lon": 62.3, "province": "Balochistan", "basin": "outside"},
        ]
    )


def clean_rows(rainfall_mm=591.9) -> pd.DataFrame:
    """Shaped like the output of cleaning.clean_rows."""
    return pd.DataFrame(
        [
            {"station_id": "test_station_x", "observed_on": dt.date(2001, 7, 24), "rainfall_mm": rainfall_mm,
             "rainfall_raw": str(rainfall_mm), "flags": ["extreme_rainfall"], "source_file": SOURCE_FILE, "sheet_row": 10},
            {"station_id": "test_station_y", "observed_on": dt.date(2001, 7, 24), "rainfall_mm": float("nan"),
             "rainfall_raw": "----", "flags": ["missing_marker"], "source_file": SOURCE_FILE, "sheet_row": 20},
        ]
    )


async def count(session, model) -> int:
    return await session.scalar(select(func.count()).select_from(model))


async def test_loads_stations_and_rainfall(db_session):
    inserted = await load_rows(db_session, stations(), clean_rows())

    assert inserted == 2
    assert await count(db_session, RainStation) == 2
    islamabad = await db_session.scalar(select(PmdRainfall).where(PmdRainfall.station_id == "test_station_x"))
    assert islamabad.rainfall_mm == pytest.approx(591.9)
    assert islamabad.flags == ["extreme_rainfall"]
    assert islamabad.sheet_row == 10


async def test_missing_values_are_stored_as_null(db_session):
    await load_rows(db_session, stations(), clean_rows())

    row = await db_session.scalar(select(PmdRainfall).where(PmdRainfall.station_id == "test_station_y"))
    assert row.rainfall_mm is None
    assert row.rainfall_raw == "----"


async def test_running_again_replaces_instead_of_adding(db_session):
    await load_rows(db_session, stations(), clean_rows(rainfall_mm=1.0))
    await load_rows(db_session, stations(), clean_rows(rainfall_mm=2.0))

    assert await count(db_session, PmdRainfall) == 2
    assert await count(db_session, RainStation) == 2
    values = await db_session.scalars(select(PmdRainfall.rainfall_mm).where(PmdRainfall.station_id == "test_station_x"))
    assert values.all() == [2.0]


async def test_rows_and_stations_no_longer_in_the_input_are_removed(db_session):
    await load_rows(db_session, stations(), clean_rows())
    await load_rows(db_session, stations().iloc[:1], clean_rows().iloc[:1])

    assert await count(db_session, PmdRainfall) == 1
    assert await count(db_session, RainStation) == 1
