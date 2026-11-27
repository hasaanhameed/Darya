import datetime as dt

from sqlalchemy import ARRAY, DateTime, ForeignKey, Index, String, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PmdRainfall(Base):
    """One day of gauge rainfall at one PMD station (ADR-023). Values are exactly as written in the file."""

    __tablename__ = "pmd_rainfall"
    __table_args__ = (
        UniqueConstraint("station_id", "observed_on"),
        Index("ix_pmd_rainfall_station_id_observed_on", "station_id", "observed_on"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    station_id: Mapped[str] = mapped_column(ForeignKey("rain_stations.id"))
    observed_on: Mapped[dt.date]  # the PMD rainfall day (a date, not a timestamp)
    rainfall_mm: Mapped[float | None]  # empty when the cell held a marker or unreadable text
    rainfall_raw: Mapped[str]  # the cell exactly as written, e.g. "12.5", "----", "*"

    # Quality notes, e.g. "suspect_negative", "duplicate_conflict". See docs/DATA.md for what each means.
    flags: Mapped[list[str]] = mapped_column(ARRAY(String), server_default=text("'{}'"))

    source_file: Mapped[str]
    sheet_row: Mapped[int]  # Excel row number in Sheet1, to trace a value back to the file
    ingested_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
