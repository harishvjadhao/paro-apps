from datetime import UTC, datetime

from sqlalchemy import Date, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, utc_now


class ChartHighlightDate(Base):
    __tablename__ = "chart_highlight_dates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    highlight_date: Mapped[datetime.date] = mapped_column(Date, unique=True, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)