from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Stock(Base):
    __tablename__ = "stocks"

    __table_args__ = (
        UniqueConstraint("symbol", name="uq_stocks_symbol"),
        UniqueConstraint("yahoo_ticker", name="uq_stocks_yahoo_ticker"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(50), index=True)
    company_name: Mapped[str] = mapped_column(String(255))
    industry: Mapped[str] = mapped_column(String(255), index=True)
    series: Mapped[str | None] = mapped_column(String(20), nullable=True)
    isin_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    yahoo_ticker: Mapped[str] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    in_watchlist: Mapped[bool] = mapped_column(Boolean, default=False)
    manual_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    price_history = relationship("StockPriceHistory", back_populates="stock", cascade="all, delete-orphan")
    indicators = relationship("StockIndicator", back_populates="stock", cascade="all, delete-orphan")
    comments = relationship("StockComment", back_populates="stock", cascade="all, delete-orphan")