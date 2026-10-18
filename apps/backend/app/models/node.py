from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Node(Base):
    """A point on the river network: a dam, barrage, headworks or gauge."""

    __tablename__ = "nodes"

    id: Mapped[str] = mapped_column(primary_key=True)  # stable slug, e.g. "tarbela"
    name: Mapped[str]
    river: Mapped[str]
    lat: Mapped[float | None]  # approximate, see docs/DATA.md
    lon: Mapped[float | None]
