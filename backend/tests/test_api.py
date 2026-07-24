from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.db.init_db import _apply_sqlite_legacy_migrations
from app.main import create_app
from app.models.chart_highlight_date import ChartHighlightDate
from app.models.stock import Stock
from app.models.stock_comment import StockComment
from app.models.stock_indicator import StockIndicator
from app.models.stock_price_history import StockPriceHistory
from app.models.sync_log import SyncLog
from app.models.sync_log_stock import SyncLogStock


def build_test_client(tmp_path: Path) -> tuple[TestClient, sessionmaker[Session]]:
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path.as_posix()}", connect_args={"check_same_thread": False})
    testing_session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    Base.metadata.create_all(bind=engine)

    app = create_app()

    def override_get_db():
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    from app.db.session import get_db

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app), testing_session_local


def test_sqlite_legacy_schema_is_upgraded_for_new_sync_columns(tmp_path: Path) -> None:
    db_path = tmp_path / "legacy.db"
    legacy_engine = create_engine(f"sqlite:///{db_path.as_posix()}", connect_args={"check_same_thread": False})

    with legacy_engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE stocks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol VARCHAR(50) NOT NULL,
                    company_name VARCHAR(255) NOT NULL,
                    industry VARCHAR(255) NOT NULL,
                    series VARCHAR(20),
                    isin_code VARCHAR(50),
                    yahoo_ticker VARCHAR(100) NOT NULL,
                    is_active BOOLEAN,
                    is_favorite BOOLEAN,
                    in_watchlist BOOLEAN,
                    manual_rank INTEGER,
                    created_at DATETIME,
                    updated_at DATETIME
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE sync_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    started_at DATETIME NOT NULL,
                    finished_at DATETIME,
                    status VARCHAR(50) NOT NULL,
                    stocks_processed INTEGER,
                    stocks_updated INTEGER,
                    error_message TEXT,
                    source VARCHAR(100),
                    created_at DATETIME
                )
                """
            )
        )

    from app.db import init_db as init_db_module

    original_engine = init_db_module.engine
    try:
        init_db_module.engine = legacy_engine
        _apply_sqlite_legacy_migrations()
    finally:
        init_db_module.engine = original_engine

    with legacy_engine.connect() as connection:
        stock_columns = {
            row[1]
            for row in connection.execute(text("PRAGMA table_info('stocks')")).fetchall()
        }
        sync_log_columns = {
            row[1]
            for row in connection.execute(text("PRAGMA table_info('sync_logs')")).fetchall()
        }
        sync_log_stock_tables = {
            row[0]
            for row in connection.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        }

    assert "last_sync_status" in stock_columns
    assert "last_sync_at" in stock_columns
    assert "last_sync_message" in stock_columns
    assert "failed_stocks" in sync_log_columns
    assert "mode" in sync_log_columns
    assert "sync_log_stocks" in sync_log_stock_tables


def seed_test_data(session_factory: sessionmaker[Session]) -> None:
    with session_factory() as db:
        stock = Stock(
            symbol="ABB",
            company_name="ABB India",
            industry="Capital Goods",
            series="EQ",
            isin_code="INE117A01022",
            yahoo_ticker="ABB.NS",
            is_active=True,
            is_favorite=False,
            in_watchlist=False,
            manual_rank=2,
        )
        db.add(stock)
        db.flush()

        db.add_all(
            [
                StockPriceHistory(
                    stock_id=stock.id,
                    trade_date=datetime(2026, 4, 1, tzinfo=UTC).date(),
                    open_price=270.0,
                    high_price=276.0,
                    low_price=268.0,
                    close_price=274.0,
                    adj_close_price=274.0,
                    volume=95000,
                ),
                StockPriceHistory(
                    stock_id=stock.id,
                    trade_date=datetime(2026, 6, 2, tzinfo=UTC).date(),
                    open_price=288.0,
                    high_price=294.0,
                    low_price=286.0,
                    close_price=291.0,
                    adj_close_price=291.0,
                    volume=110000,
                ),
                StockPriceHistory(
                    stock_id=stock.id,
                    trade_date=datetime(2026, 7, 22, tzinfo=UTC).date(),
                    open_price=295.0,
                    high_price=300.0,
                    low_price=292.0,
                    close_price=297.56,
                    adj_close_price=297.56,
                    volume=125000,
                ),
            ]
        )
        db.add(
            StockIndicator(
                stock_id=stock.id,
                as_of_date=datetime(2026, 7, 22, tzinfo=UTC).date(),
                moving_average_44=295.31,
                is_above_44_ma=True,
                percent_above_44_ma=0.76,
            )
        )
        db.add(
            SyncLog(
                started_at=datetime(2026, 7, 22, 9, 0, tzinfo=UTC),
                finished_at=datetime(2026, 7, 22, 9, 1, tzinfo=UTC),
                status="success",
                stocks_processed=200,
                stocks_updated=200,
                failed_stocks=1,
                source="bootstrap",
                mode="full",
            )
        )
        db.flush()
        latest_log = db.query(SyncLog).order_by(SyncLog.id.desc()).first()
        db.add(
            SyncLogStock(
                sync_log_id=latest_log.id,
                stock_id=stock.id,
                symbol_snapshot=stock.symbol,
                sync_mode="full",
                status="failed",
                message="No market data returned",
                range_start=datetime(2026, 7, 1, tzinfo=UTC).date(),
                range_end=datetime(2026, 7, 22, tzinfo=UTC).date(),
                started_at=datetime(2026, 7, 22, 9, 0, tzinfo=UTC),
                finished_at=datetime(2026, 7, 22, 9, 0, 30, tzinfo=UTC),
                rows_written=0,
            )
        )
        db.commit()


def test_list_stocks_returns_market_fields(tmp_path: Path) -> None:
    client, session_factory = build_test_client(tmp_path)
    seed_test_data(session_factory)

    response = client.get("/api/stocks")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["total"] == 1
    assert payload["data"]["items"][0]["symbol"] == "ABB"
    assert payload["data"]["items"][0]["closePrice"] == 297.56
    assert payload["data"]["items"][0]["isAbove44MA"] is True


def test_stock_mutation_endpoints_update_flags(tmp_path: Path) -> None:
    client, session_factory = build_test_client(tmp_path)
    seed_test_data(session_factory)

    favorite_response = client.post("/api/stocks/ABB/favorite", json={"value": True})
    watchlist_response = client.post("/api/stocks/ABB/watchlist", json={"value": True})

    assert favorite_response.status_code == 200
    assert favorite_response.json()["data"]["isFavorite"] is True
    assert watchlist_response.status_code == 200
    assert watchlist_response.json()["data"]["inWatchlist"] is True


def test_reorder_and_sync_status_endpoints(tmp_path: Path) -> None:
    client, session_factory = build_test_client(tmp_path)
    seed_test_data(session_factory)

    reorder_response = client.post("/api/stocks/reorder", json={"items": [{"symbol": "ABB", "manualRank": 1}]})
    status_response = client.get("/api/sync/status")
    logs_response = client.get("/api/sync/logs")
    detail_response = client.get("/api/sync/logs/1")

    assert reorder_response.status_code == 200
    assert reorder_response.json()["data"]["items"][0]["manualRank"] == 1
    assert status_response.status_code == 200
    assert status_response.json()["data"]["status"] == "success"
    assert status_response.json()["data"]["mode"] == "full"
    assert status_response.json()["data"]["failedStocks"] == 1
    assert logs_response.status_code == 200
    assert logs_response.json()["data"]["items"][0]["source"] == "bootstrap"
    assert logs_response.json()["data"]["items"][0]["mode"] == "full"
    assert detail_response.status_code == 200
    assert detail_response.json()["data"]["items"][0]["symbol"] == "ABB"
    assert detail_response.json()["data"]["items"][0]["status"] == "failed"


def test_stock_comment_endpoints_create_update_and_delete_entries(tmp_path: Path) -> None:
    client, session_factory = build_test_client(tmp_path)
    seed_test_data(session_factory)

    create_response = client.post("/api/stocks/ABB/comments", json={"comment": "Initial thesis"})

    assert create_response.status_code == 200
    comment_payload = create_response.json()["data"]
    assert comment_payload["comment"] == "Initial thesis"
    assert comment_payload["id"] > 0

    list_response = client.get("/api/stocks/ABB/comments")

    assert list_response.status_code == 200
    assert list_response.json()["data"]["items"][0]["comment"] == "Initial thesis"

    update_response = client.put(
        f"/api/stocks/ABB/comments/{comment_payload['id']}",
        json={"comment": "Updated thesis"},
    )

    assert update_response.status_code == 200
    assert update_response.json()["data"]["comment"] == "Updated thesis"

    delete_response = client.delete(f"/api/stocks/ABB/comments/{comment_payload['id']}")

    assert delete_response.status_code == 200
    assert delete_response.json()["data"]["deleted"] is True

    list_after_delete_response = client.get("/api/stocks/ABB/comments")

    assert list_after_delete_response.status_code == 200
    assert list_after_delete_response.json()["data"]["items"] == []

    with session_factory() as db:
        stored_comment = db.get(StockComment, comment_payload["id"])
        assert stored_comment is None


def test_chart_highlight_date_endpoints_create_list_and_delete_entries(tmp_path: Path) -> None:
    client, session_factory = build_test_client(tmp_path)
    seed_test_data(session_factory)

    create_response = client.post("/api/settings/chart-highlights", json={"highlightDate": "2026-06-02"})

    assert create_response.status_code == 200
    highlight_payload = create_response.json()["data"]
    assert highlight_payload["highlightDate"] == "2026-06-02"
    assert highlight_payload["id"] > 0

    list_response = client.get("/api/settings/chart-highlights")

    assert list_response.status_code == 200
    assert list_response.json()["data"]["items"][0]["highlightDate"] == "2026-06-02"

    duplicate_response = client.post("/api/settings/chart-highlights", json={"highlightDate": "2026-06-02"})

    assert duplicate_response.status_code == 400

    delete_response = client.delete(f"/api/settings/chart-highlights/{highlight_payload['id']}")

    assert delete_response.status_code == 200
    assert delete_response.json()["data"]["deleted"] is True

    with session_factory() as db:
        stored_item = db.get(ChartHighlightDate, highlight_payload["id"])
        assert stored_item is None


def test_stock_timeline_endpoint_returns_latest_100_candles_with_indicator_values(tmp_path: Path) -> None:
    client, session_factory = build_test_client(tmp_path)
    seed_test_data(session_factory)

    response = client.get("/api/stocks/ABB/timeline")

    assert response.status_code == 200
    payload = response.json()["data"]["items"]
    assert len(payload) == 3
    assert payload[0]["tradeDate"] == "2026-04-01"
    assert payload[-1]["tradeDate"] == "2026-07-22"
    assert payload[-1]["openPrice"] == 295.0
    assert payload[-1]["highPrice"] == 300.0
    assert payload[-1]["lowPrice"] == 292.0
    assert payload[-1]["closePrice"] == 297.56
    assert payload[-1]["movingAverage44"] == 295.31