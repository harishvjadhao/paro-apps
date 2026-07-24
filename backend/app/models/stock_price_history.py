from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Index, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, utc_now


class StockPriceHistory(Base):
    __tablename__ = "stock_price_history"

    __table_args__ = (
        UniqueConstraint("stock_id", "trade_date", name="uq_stock_price_history_stock_id_trade_date"),
        Index("ix_stock_price_history_stock_id", "stock_id"),
        Index("ix_stock_price_history_trade_date", "trade_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    open_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    high_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    low_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    close_price: Mapped[float] = mapped_column(Float, nullable=False)
    adj_close_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    volume: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    stock = relationship("Stock", back_populates="price_history")