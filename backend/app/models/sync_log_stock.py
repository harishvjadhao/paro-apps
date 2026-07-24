from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, utc_now


class SyncLogStock(Base):
    __tablename__ = "sync_log_stocks"

    __table_args__ = (
        Index("ix_sync_log_stocks_sync_log_id", "sync_log_id"),
        Index("ix_sync_log_stocks_stock_id", "stock_id"),
        Index("ix_sync_log_stocks_symbol_snapshot", "symbol_snapshot"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sync_log_id: Mapped[int] = mapped_column(ForeignKey("sync_logs.id", ondelete="CASCADE"), nullable=False)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False)
    symbol_snapshot: Mapped[str] = mapped_column(String(50), nullable=False)
    sync_mode: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    range_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    range_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    rows_written: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)