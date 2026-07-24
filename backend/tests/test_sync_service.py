from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from threading import Event, Thread

import pandas as pd
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models.stock import Stock
from app.models.stock_indicator import StockIndicator
from app.models.stock_price_history import StockPriceHistory
from app.models.sync_log import SyncLog
from app.models.sync_log_stock import SyncLogStock
from app.services.sync_service import (
    SYNC_MODE_FULL,
    _build_sync_warning,
    _download_history,
    _download_history_with_retry,
    _upsert_indicators,
    _upsert_price_history,
    run_sync,
)


def build_session() -> Session:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    return testing_session()


def build_file_session_factory(tmp_path: Path) -> sessionmaker[Session]:
    db_path = tmp_path / "sync-test.db"
    engine = create_engine(
        f"sqlite:///{db_path.as_posix()}",
        connect_args={"check_same_thread": False, "timeout": 30},
    )
    with engine.connect() as connection:
        connection.exec_driver_sql("PRAGMA journal_mode=WAL")
        connection.exec_driver_sql("PRAGMA busy_timeout=30000")
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)


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


def test_upsert_indicators_uses_persisted_history_for_incremental_updates() -> None:
    db = build_session()
    stock = seed_stock(db)
    historical_close_values = [100.0 + index for index in range(50)]

    _upsert_price_history(db, stock, build_history(historical_close_values))
    _upsert_indicators(db, stock, build_history(historical_close_values))
    db.commit()

    latest_trade_date = db.scalar(
        select(StockPriceHistory.trade_date)
        .where(StockPriceHistory.stock_id == stock.id)
        .order_by(StockPriceHistory.trade_date.desc())
    )
    assert latest_trade_date is not None

    incremental_close = 200.0
    incremental_history = pd.DataFrame(
        [
            {
                "Date": pd.Timestamp(latest_trade_date),
                "Open": incremental_close - 1,
                "High": incremental_close + 1,
                "Low": incremental_close - 2,
                "Close": incremental_close,
                "Adj Close": incremental_close,
                "Volume": 999999,
            }
        ]
    )

    _upsert_price_history(db, stock, incremental_history)
    _upsert_indicators(db, stock, incremental_history)
    db.commit()

    latest_indicator = db.scalar(
        select(StockIndicator)
        .where(StockIndicator.stock_id == stock.id)
        .order_by(StockIndicator.as_of_date.desc())
    )

    expected_ma = sum(historical_close_values[-44:-1] + [incremental_close]) / 44

    assert latest_indicator is not None
    assert latest_indicator.moving_average_44 is not None
    assert round(latest_indicator.moving_average_44, 6) == round(expected_ma, 6)
    assert latest_indicator.is_above_44_ma is True


def test_build_sync_warning_summarizes_failed_symbols() -> None:
    message = _build_sync_warning([f"SYM{index}" for index in range(12)])

    assert message is not None
    assert "12 stocks" in message
    assert "SYM0" in message
    assert "..." in message


def test_build_sync_warning_includes_unchanged_symbols() -> None:
    message = _build_sync_warning(["ABB"], ["TCS", "INFY"])

    assert message == (
        "No market data returned for 1 stocks: ABB | "
        "No new rows written for 2 stocks: TCS, INFY"
    )


def test_download_history_flattens_multiindex_columns(monkeypatch) -> None:
    history = pd.DataFrame(
        {
            ("Adj Close", "ABB.NS"): [101.0],
            ("Close", "ABB.NS"): [101.0],
            ("High", "ABB.NS"): [102.0],
            ("Low", "ABB.NS"): [99.0],
            ("Open", "ABB.NS"): [100.0],
            ("Volume", "ABB.NS"): [123456],
        },
        index=pd.DatetimeIndex([pd.Timestamp("2026-07-23T00:00:00Z")], name="Date"),
    )

    def fake_download(*args, **kwargs) -> pd.DataFrame:
        return history

    monkeypatch.setattr("app.services.sync_service.yf.download", fake_download)

    normalized = _download_history("ABB.NS")

    assert list(normalized.columns) == ["Date", "Adj Close", "Close", "High", "Low", "Open", "Volume"]
    assert pd.Timestamp(normalized.loc[0, "Date"]) == pd.Timestamp("2026-07-23T00:00:00Z")
    assert normalized.loc[0, "Close"] == 101.0


def test_download_history_with_retry_retries_empty_response(monkeypatch) -> None:
    history = build_history([100.0, 101.0])
    calls = {"count": 0}

    def fake_download(*args, **kwargs) -> pd.DataFrame:
        calls["count"] += 1
        if calls["count"] < 3:
            return pd.DataFrame()
        return history

    monkeypatch.setattr("app.services.sync_service._download_history", fake_download)

    normalized = _download_history_with_retry("ABB.NS", attempts=3, retry_delay_seconds=0)

    assert len(normalized) == 2
    assert calls["count"] == 3


def test_run_sync_allows_parallel_reads_after_start_log_commit(tmp_path: Path, monkeypatch) -> None:
    session_factory = build_file_session_factory(tmp_path)
    with session_factory() as db:
        seed_stock(db)

    sync_can_finish = Event()
    sync_started_download = Event()
    thread_errors: list[Exception] = []

    def fake_download(*args, **kwargs) -> pd.DataFrame:
        sync_started_download.set()
        if not sync_can_finish.wait(timeout=5):
            raise TimeoutError("sync test timed out")
        return build_history([100.0, 101.0, 102.0])

    def run_sync_in_thread() -> None:
        try:
            with session_factory() as db:
                run_sync(db, source="api")
        except Exception as exc:  # noqa: BLE001
            thread_errors.append(exc)

    monkeypatch.setattr("app.services.sync_service._download_history", fake_download)

    worker = Thread(target=run_sync_in_thread)
    worker.start()

    assert sync_started_download.wait(timeout=5)

    with session_factory() as read_db:
        stocks = read_db.scalars(select(Stock).where(Stock.is_active.is_(True))).all()
        logs = read_db.scalars(select(SyncLog).order_by(SyncLog.started_at.desc())).all()
        assert [stock.symbol for stock in stocks] == ["ABB"]
        assert logs[0].status == "running"

    sync_can_finish.set()
    worker.join(timeout=5)

    assert not worker.is_alive()
    assert thread_errors == []

    with session_factory() as db:
        latest_log = db.scalar(select(SyncLog).order_by(SyncLog.started_at.desc()))
        assert latest_log is not None
        assert latest_log.status == "success"


def test_run_sync_marks_existing_only_history_as_partial(tmp_path: Path, monkeypatch) -> None:
    session_factory = build_file_session_factory(tmp_path)
    with session_factory() as db:
        stock = seed_stock(db)
        _upsert_price_history(db, stock, build_history([100.0, 101.0, 102.0]))
        db.commit()

    def fake_download(*args, **kwargs) -> pd.DataFrame:
        return build_history([100.0, 101.0, 102.0])

    monkeypatch.setattr("app.services.sync_service._download_history", fake_download)

    with session_factory() as db:
        result = run_sync(db, source="api")

        latest_log = db.scalar(select(SyncLog).order_by(SyncLog.started_at.desc()))
        latest_item = db.scalar(select(SyncLogStock).order_by(SyncLogStock.id.desc()))

        assert result.status == "partial"
        assert result.stocks_processed == 1
        assert result.stocks_updated == 0
        assert result.failed_stocks == 1
        assert result.error_message == "No new rows written for 1 stocks: ABB"
        assert latest_log is not None
        assert latest_log.status == "partial"
        assert latest_log.stocks_updated == 0
        assert latest_log.failed_stocks == 1
        assert latest_item is not None
        assert latest_item.status == "partial"
        assert latest_item.rows_written == 0
        assert latest_item.message == "No new rows written"


def test_run_full_sync_replaces_existing_history(tmp_path: Path, monkeypatch) -> None:
    session_factory = build_file_session_factory(tmp_path)
    original_history = build_history([100.0, 101.0, 102.0])
    refreshed_history = build_history([110.0, 111.0, 112.0, 113.0])

    with session_factory() as db:
        stock = seed_stock(db)
        _upsert_price_history(db, stock, original_history)
        _upsert_indicators(db, stock, original_history)
        db.commit()

    def fake_download(*args, **kwargs) -> pd.DataFrame:
        return refreshed_history

    monkeypatch.setattr("app.services.sync_service._download_history", fake_download)

    with session_factory() as db:
        result = run_sync(db, source="api", mode=SYNC_MODE_FULL)

        history_rows = db.scalars(
            select(StockPriceHistory)
            .where(StockPriceHistory.stock_id == 1)
            .order_by(StockPriceHistory.trade_date.asc())
        ).all()
        indicator_rows = db.scalars(
            select(StockIndicator)
            .where(StockIndicator.stock_id == 1)
            .order_by(StockIndicator.as_of_date.asc())
        ).all()
        latest_log = db.scalar(select(SyncLog).order_by(SyncLog.started_at.desc()))
        latest_item = db.scalar(select(SyncLogStock).order_by(SyncLogStock.id.desc()))

        assert result.status == "success"
        assert result.stocks_processed == 1
        assert result.stocks_updated == 1
        assert result.failed_stocks == 0
        assert result.error_message is None
        assert [row.close_price for row in history_rows] == [110.0, 111.0, 112.0, 113.0]
        assert len(indicator_rows) == 4
        assert latest_log is not None
        assert latest_log.status == "success"
        assert latest_log.stocks_updated == 1
        assert latest_log.failed_stocks == 0
        assert latest_item is not None
        assert latest_item.status == "success"
        assert latest_item.rows_written == 4
        assert latest_item.message is None