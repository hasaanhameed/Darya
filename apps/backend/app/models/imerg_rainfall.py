import datetime as dt

from sqlalchemy import ARRAY, DateTime, ForeignKey, Index, String, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ImergRainfall(Base):
    """Daily IMERG satellite rainfall averaged over a node's catchment and local area (ADR-019, ADR-022)."""

    __tablename__ = "imerg_rainfall"
    __table_args__ = (
        UniqueConstraint("node_id", "observed_on", "run"),
        Index("ix_imerg_rainfall_node_id_observed_on", "node_id", "observed_on"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    node_id: Mapped[str] = mapped_column(ForeignKey("nodes.id"))
    observed_on: Mapped[dt.date]  # the UTC day (00-24 UTC, i.e. 05-05 PKT)
    catchment_rainfall_mm: Mapped[float | None]  # mean over all land draining to the node
    local_rainfall_mm: Mapped[float | None]  # mean over the land between this node and the next nodes upstream
    run: Mapped[str]  # IMERG run, e.g. "late"
    version_label: Mapped[str | None]  # from the file name, e.g. "V07B"

    # Quality notes, e.g. "low_coverage". See docs/DATA.md for what each means.
    flags: Mapped[list[str]] = mapped_column(ARRAY(String), server_default=text("'{}'"))

    source_file: Mapped[str]
    ingested_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
