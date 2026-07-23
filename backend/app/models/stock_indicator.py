from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Index, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class StockIndicator(Base):
    __tablename__ = "stock_indicators"

    __table_args__ = (
        UniqueConstraint("stock_id", "as_of_date", name="uq_stock_indicators_stock_id_as_of_date"),
        Index("ix_stock_indicators_stock_id", "stock_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False)
    as_of_date: Mapped[date] = mapped_column(Date, nullable=False)
    moving_average_44: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_above_44_ma: Mapped[bool] = mapped_column(Boolean, default=False)
    percent_above_44_ma: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    stock = relationship("Stock", back_populates="indicators")