from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models.stock import Stock
from app.models.stock_indicator import StockIndicator
from app.models.stock_price_history import StockPriceHistory
from app.services.sync_service import _build_sync_warning, _upsert_indicators, _upsert_price_history


def build_session() -> Session:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    return testing_session()


def seed_stock(db: Session) -> Stock:
    stock = Stock(
        symbol="ABB",
        company_name="ABB India",
        industry="Capital Goods",
        series="EQ",
        isin_code="INE117A01022",
        yahoo_ticker="ABB.NS",
        is_active=True,
    )
    db.add(stock)
    db.commit()
    db.refresh(stock)
    return stock


def build_history(close_values: list[float]) -> pd.DataFrame:
    start_date = datetime(2026, 5, 1, tzinfo=UTC)
    rows = []
    for index, close_value in enumerate(close_values):
        trade_date = start_date + pd.Timedelta(days=index)
        rows.append(
            {
                "Date": pd.Timestamp(trade_date),
                "Open": close_value - 1,
                "High": close_value + 1,
                "Low": close_value - 2,
                "Close": close_value,
                "Adj Close": close_value,
                "Volume": 100000 + index,
            }
        )
    return pd.DataFrame(rows)


def test_upsert_price_history_inserts_and_updates_rows() -> None:
    db = build_session()
    stock = seed_stock(db)
    history = build_history([100.0, 101.0, 102.0])

    inserted = _upsert_price_history(db, stock, history)
    db.commit()

    assert inserted == 3

    updated_history = build_history([100.0, 101.0, 111.0])
    inserted_again = _upsert_price_history(db, stock, updated_history)
    db.commit()

    latest = db.scalar(
        select(StockPriceHistory)
        .where(StockPriceHistory.stock_id == stock.id)
        .order_by(StockPriceHistory.trade_date.desc())
    )

    assert inserted_again == 0
    assert latest is not None
    assert latest.close_price == 111.0


def test_upsert_indicators_computes_44_day_metrics_for_each_trading_day() -> None:
    db = build_session()
    stock = seed_stock(db)
    close_values = [100.0 + (index * 0.5) for index in range(50)]
    history = build_history(close_values)

    _upsert_indicators(db, stock, history)
    db.commit()

    indicators = db.scalars(
        select(StockIndicator)
        .where(StockIndicator.stock_id == stock.id)
        .order_by(StockIndicator.as_of_date.asc())
    ).all()
    expected_ma = sum(close_values[-44:]) / 44

    assert len(indicators) == 50
    assert indicators[0].moving_average_44 is None
    assert indicators[42].moving_average_44 is None
    assert indicators[43].moving_average_44 is not None
    assert round(indicators[-1].moving_average_44 or 0, 6) == round(expected_ma, 6)
    assert indicators[-1].is_above_44_ma is True
    assert indicators[-1].percent_above_44_ma is not None
    assert indicators[-1].percent_above_44_ma > 0


def test_build_sync_warning_summarizes_failed_symbols() -> None:
    message = _build_sync_warning([f"SYM{index}" for index in range(12)])

    assert message is not None
    assert "12 stocks" in message
    assert "SYM0" in message
    assert "..." in message