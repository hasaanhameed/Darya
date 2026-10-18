import datetime as dt

from sqlalchemy import ARRAY, DateTime, ForeignKey, Index, String, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class DailyObservation(Base):
    """One day of measured values for one node from one source. Values keep the source's native units."""

    __tablename__ = "daily_observations"
    __table_args__ = (
        UniqueConstraint("node_id", "observed_on", "source"),
        Index("ix_daily_observations_node_id_observed_on", "node_id", "observed_on"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    node_id: Mapped[str] = mapped_column(ForeignKey("nodes.id"))
    observed_on: Mapped[dt.date]  # the reporting day (a date, not a timestamp)
    source: Mapped[str]  # e.g. "wapda_hydel_synopsis"

    level_ft: Mapped[float | None]
    inflow_cfs: Mapped[float | None]
    outflow_turbine_cfs: Mapped[float | None]
    outflow_other_cfs: Mapped[float | None]
    outflow_total_cfs: Mapped[float | None]
    irrigation_indent_raw: Mapped[str | None]  # free text, exactly as written in the source

    # Quality notes, e.g. "suspect_inflow", "date_from_sheet". See docs/DATA.md for what each means.
    flags: Mapped[list[str]] = mapped_column(ARRAY(String), server_default=text("'{}'"))

    source_file: Mapped[str]
    sheet: Mapped[str]
    ingested_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
