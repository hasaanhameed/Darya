import datetime as dt

from sqlalchemy import ARRAY, DateTime, ForeignKey, Index, String, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class GlofasDischarge(Base):
    """Modelled daily mean river discharge at a node's GloFAS grid cell (ADR-019, ADR-021)."""

    __tablename__ = "glofas_discharge"
    __table_args__ = (
        UniqueConstraint("node_id", "observed_on", "system_version"),
        Index("ix_glofas_discharge_node_id_observed_on", "node_id", "observed_on"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    node_id: Mapped[str] = mapped_column(ForeignKey("nodes.id"))
    observed_on: Mapped[dt.date]  # the UTC day the 24-hour mean covers
    discharge_m3s: Mapped[float | None]
    product_type: Mapped[str]  # "consolidated" (final ERA5) or "intermediate" (ERA5T)
    system_version: Mapped[str]  # e.g. "version_4_0"; versions are never mixed

    # Quality notes, e.g. "missing_value". See docs/DATA.md for what each means.
    flags: Mapped[list[str]] = mapped_column(ARRAY(String), server_default=text("'{}'"))

    source_file: Mapped[str]
    ingested_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
