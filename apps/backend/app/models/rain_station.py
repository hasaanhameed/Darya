from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RainStation(Base):
    """A PMD weather station with a rain gauge (ADR-023). Not a river node."""

    __tablename__ = "rain_stations"

    id: Mapped[str] = mapped_column(primary_key=True)  # stable slug, e.g. "islamabad_ap"
    name: Mapped[str]  # readable name, e.g. "Islamabad Airport"
    pmd_name: Mapped[str]  # the name as PMD writes it, spaces normalised, e.g. "ISLAMABAD A/P"
    lat: Mapped[float | None]  # approximate, see docs/DATA.md
    lon: Mapped[float | None]
    province: Mapped[str | None]
    basin: Mapped[str]  # "indus" or "outside"
