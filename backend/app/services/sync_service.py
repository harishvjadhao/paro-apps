from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import UTC, date, datetime

import pandas as pd
import yfinance as yf
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.stock import Stock
from app.models.stock_indicator import StockIndicator
from app.models.stock_price_history import StockPriceHistory
from app.models.sync_log import SyncLog
from app.models.sync_log_stock import SyncLogStock
from app.services.sample_data_service import build_sample_history


SYNC_STATUS_IDLE = "idle"
SYNC_STATUS_RUNNING = "running"
SYNC_STATUS_SUCCESS = "success"
SYNC_STATUS_PARTIAL = "partial"
SYNC_STATUS_FAILED = "failed"

SYNC_MODE_FULL = "full"
SYNC_MODE_INCREMENTAL = "incremental"
SYNC_MODE_SINGLE_STOCK = "single_stock"

DOWNLOAD_RETRY_ATTEMPTS = 3
DOWNLOAD_RETRY_DELAY_SECONDS = 1.0


@dataclass
class SyncResult:
    status: str
    stocks_processed: int
    stocks_updated: int
    failed_stocks: int = 0
    error_message: str | None = None
    last_successful_sync_at: datetime | None = None
    last_sync_started_at: datetime | None = None
    mode: str | None = None
    sync_log_id: int | None = None


@dataclass
class SyncStockResult:
    stock_id: int
    symbol: str
    sync_mode: str
    status: str
    message: str | None
    range_start: date | None
    range_end: date | None
    started_at: datetime
    finished_at: datetime
    rows_written: int


def run_sync(db: Session, source: str = "manual", mode: str = SYNC_MODE_INCREMENTAL, symbol: str | None = None) -> SyncResult:
    settings = get_settings()
    started_at = datetime.now(UTC)
    sync_log = SyncLog(started_at=started_at, status=SYNC_STATUS_RUNNING, source=source, mode=mode)
    db.add(sync_log)
    db.commit()
    db.refresh(sync_log)
    sync_log_id = sync_log.id

    stocks_processed = 0
    stocks_updated = 0
    failed_symbols: list[str] = []
    unchanged_symbols: list[str] = []
    stock_results: list[SyncStockResult] = []

    try:
        stocks = _resolve_target_stocks(db, symbol)
        force_sample_mode = settings.data_source_mode.lower() == "mock" and source != "api"

        if mode == SYNC_MODE_FULL:
            _reset_full_sync_state(db, stocks)

        for stock in stocks:
            stock_started_at = datetime.now(UTC)
            range_start, range_end = _resolve_sync_window(db, stock, mode)
            history = (
                build_sample_history(stock)
                if force_sample_mode
                else _download_history_with_retry(stock.yahoo_ticker, mode=mode, start_date=range_start)
            )
            if history.empty:
                if source != "api":
                    history = build_sample_history(stock)

                if history.empty:
                    failed_symbols.append(stock.symbol)
                    stock_finished_at = datetime.now(UTC)
                    stock_results.append(
                        SyncStockResult(
                            stock_id=stock.id,
                            symbol=stock.symbol,
                            sync_mode=mode,
                            status=SYNC_STATUS_FAILED,
                            message="No market data returned",
                            range_start=range_start,
                            range_end=range_end,
                            started_at=stock_started_at,
                            finished_at=stock_finished_at,
                            rows_written=0,
                        )
                    )
                    _update_stock_sync_state(stock, SYNC_STATUS_FAILED, stock_finished_at, "No market data returned")
                    stocks_processed += 1
                    continue

            rows_written = _upsert_price_history(db, stock, history)
            _upsert_indicators(db, stock, history)
            stock_finished_at = datetime.now(UTC)
            stock_status = SYNC_STATUS_SUCCESS if rows_written > 0 else SYNC_STATUS_PARTIAL
            stock_message = None if stock_status == SYNC_STATUS_SUCCESS else "No new rows written"
            stock_results.append(
                SyncStockResult(
                    stock_id=stock.id,
                    symbol=stock.symbol,
                    sync_mode=mode,
                    status=stock_status,
                    message=stock_message,
                    range_start=range_start,
                    range_end=range_end,
                    started_at=stock_started_at,
                    finished_at=stock_finished_at,
                    rows_written=rows_written,
                )
            )
            _update_stock_sync_state(stock, stock_status, stock_finished_at, stock_message)
            stocks_processed += 1
            if rows_written > 0:
                stocks_updated += 1
            if stock_status == SYNC_STATUS_PARTIAL:
                unchanged_symbols.append(stock.symbol)

        _store_stock_results(db, sync_log_id, stock_results)

        db.commit()

        finished_at = datetime.now(UTC)
        error_message = _build_sync_warning(failed_symbols, unchanged_symbols)
        status = SYNC_STATUS_PARTIAL if failed_symbols or unchanged_symbols else SYNC_STATUS_SUCCESS
        sync_log = db.get(SyncLog, sync_log_id)
        sync_log.finished_at = finished_at
        sync_log.status = status
        sync_log.stocks_processed = stocks_processed
        sync_log.stocks_updated = stocks_updated
        sync_log.failed_stocks = len(failed_symbols) + len(unchanged_symbols)
        sync_log.error_message = error_message
        db.commit()

        return SyncResult(
            status=status,
            stocks_processed=stocks_processed,
            stocks_updated=stocks_updated,
            failed_stocks=len(failed_symbols) + len(unchanged_symbols),
            error_message=error_message,
            last_successful_sync_at=finished_at,
            last_sync_started_at=started_at,
            mode=mode,
            sync_log_id=sync_log_id,
        )
    except Exception as exc:  # noqa: BLE001
        finished_at = datetime.now(UTC)
        db.rollback()
        sync_log = db.get(SyncLog, sync_log_id)
        sync_log.finished_at = finished_at
        sync_log.status = SYNC_STATUS_FAILED
        sync_log.stocks_processed = stocks_processed
        sync_log.stocks_updated = stocks_updated
        sync_log.failed_stocks = max(len(failed_symbols), 1)
        sync_log.error_message = str(exc)
        db.commit()
        return SyncResult(
            status=SYNC_STATUS_FAILED,
            stocks_processed=stocks_processed,
            stocks_updated=stocks_updated,
            failed_stocks=max(len(failed_symbols), 1),
            error_message=str(exc),
            last_sync_started_at=started_at,
            mode=mode,
            sync_log_id=sync_log_id,
        )


def get_latest_sync_status(db: Session) -> SyncResult:
    latest = db.scalar(select(SyncLog).order_by(SyncLog.started_at.desc()))
    if latest is None:
        return SyncResult(status=SYNC_STATUS_IDLE, stocks_processed=0, stocks_updated=0)

    return SyncResult(
        status=latest.status,
        stocks_processed=latest.stocks_processed,
        stocks_updated=latest.stocks_updated,
        failed_stocks=latest.failed_stocks,
        error_message=latest.error_message,
        last_successful_sync_at=latest.finished_at if latest.status == SYNC_STATUS_SUCCESS else None,
        last_sync_started_at=latest.started_at,
        mode=latest.mode,
        sync_log_id=latest.id,
    )


def get_sync_log_detail(db: Session, sync_log_id: int) -> dict | None:
    sync_log = db.get(SyncLog, sync_log_id)
    if sync_log is None:
        return None

    items = db.scalars(select(SyncLogStock).where(SyncLogStock.sync_log_id == sync_log_id).order_by(SyncLogStock.symbol_snapshot.asc())).all()
    return {
        "id": sync_log.id,
        "startedAt": sync_log.started_at,
        "finishedAt": sync_log.finished_at,
        "status": sync_log.status,
        "stocksProcessed": sync_log.stocks_processed,
        "stocksUpdated": sync_log.stocks_updated,
        "failedStocks": sync_log.failed_stocks,
        "errorMessage": sync_log.error_message,
        "source": sync_log.source,
        "mode": sync_log.mode,
        "items": [
            {
                "id": item.id,
                "stockId": item.stock_id,
                "symbol": item.symbol_snapshot,
                "syncMode": item.sync_mode,
                "status": item.status,
                "message": item.message,
                "rangeStart": item.range_start,
                "rangeEnd": item.range_end,
                "startedAt": item.started_at,
                "finishedAt": item.finished_at,
                "rowsWritten": item.rows_written,
            }
            for item in items
        ],
    }


def _download_history(yahoo_ticker: str, mode: str = SYNC_MODE_INCREMENTAL, start_date: date | None = None) -> pd.DataFrame:
    history_kwargs = {
        "interval": "1d",
        "auto_adjust": False,
        "progress": False,
    }
    if mode == SYNC_MODE_FULL:
        history_kwargs["period"] = "1y"
    elif start_date is not None:
        history_kwargs["start"] = start_date.isoformat()
    else:
        history_kwargs["period"] = "5d"

    history = yf.download(yahoo_ticker, **history_kwargs)
    if history.empty:
        return history

    history = history.reset_index()
    history.columns = [_normalize_history_column_name(column) for column in history.columns]
    return history


def _download_history_with_retry(
    yahoo_ticker: str,
    mode: str = SYNC_MODE_INCREMENTAL,
    start_date: date | None = None,
    attempts: int = DOWNLOAD_RETRY_ATTEMPTS,
    retry_delay_seconds: float = DOWNLOAD_RETRY_DELAY_SECONDS,
) -> pd.DataFrame:
    history = pd.DataFrame()

    for attempt in range(1, attempts + 1):
        history = _download_history(yahoo_ticker, mode=mode, start_date=start_date)
        if not history.empty:
            return history
        if attempt < attempts:
            time.sleep(retry_delay_seconds)

    return history


def _normalize_history_column_name(column: object) -> str:
    if isinstance(column, tuple):
        primary_name = str(column[0])
        if primary_name == "Date":
            return primary_name
        return primary_name

    return str(column)


def _resolve_target_stocks(db: Session, symbol: str | None) -> list[Stock]:
    query = select(Stock).where(Stock.is_active.is_(True))
    if symbol is not None:
        query = query.where(Stock.symbol == symbol)

    return db.scalars(query.order_by(Stock.symbol.asc())).all()


def _resolve_sync_window(db: Session, stock: Stock, mode: str) -> tuple[date | None, date]:
    latest_trade_date = db.scalar(
        select(StockPriceHistory.trade_date)
        .where(StockPriceHistory.stock_id == stock.id)
        .order_by(StockPriceHistory.trade_date.desc())
        .limit(1)
    )
    today = datetime.now(UTC).date()
    if mode == SYNC_MODE_FULL:
        return None, today

    if latest_trade_date is None:
        return today, today

    return latest_trade_date, today


def _store_stock_results(db: Session, sync_log_id: int, stock_results: list[SyncStockResult]) -> None:
    for item in stock_results:
        db.add(
            SyncLogStock(
                sync_log_id=sync_log_id,
                stock_id=item.stock_id,
                symbol_snapshot=item.symbol,
                sync_mode=item.sync_mode,
                status=item.status,
                message=item.message,
                range_start=item.range_start,
                range_end=item.range_end,
                started_at=item.started_at,
                finished_at=item.finished_at,
                rows_written=item.rows_written,
            )
        )


def _update_stock_sync_state(stock: Stock, status: str, synced_at: datetime, message: str | None) -> None:
    stock.last_sync_status = status
    stock.last_sync_at = synced_at
    stock.last_sync_message = message


def _reset_full_sync_state(db: Session, stocks: list[Stock]) -> None:
    stock_ids = [stock.id for stock in stocks]
    if not stock_ids:
        return

    db.execute(delete(StockIndicator).where(StockIndicator.stock_id.in_(stock_ids)))
    db.execute(delete(StockPriceHistory).where(StockPriceHistory.stock_id.in_(stock_ids)))
    db.flush()


def _upsert_price_history(db: Session, stock: Stock, history: pd.DataFrame) -> int:
    written = 0

    for _, row in history.iterrows():
        trade_date = pd.Timestamp(row["Date"]).date()
        existing = db.scalar(
            select(StockPriceHistory).where(
                StockPriceHistory.stock_id == stock.id,
                StockPriceHistory.trade_date == trade_date,
            )
        )

        open_price = _to_float(row.get("Open"))
        high_price = _to_float(row.get("High"))
        low_price = _to_float(row.get("Low"))
        close_price = _to_float(row.get("Close"))
        adj_close_price = _to_float(row.get("Adj Close"))
        volume = _to_int(row.get("Volume"))

        if close_price is None:
            continue

        if existing is None:
            db.add(
                StockPriceHistory(
                    stock_id=stock.id,
                    trade_date=trade_date,
                    open_price=open_price,
                    high_price=high_price,
                    low_price=low_price,
                    close_price=close_price,
                    adj_close_price=adj_close_price,
                    volume=volume,
                )
            )
            written += 1
        else:
            existing.open_price = open_price
            existing.high_price = high_price
            existing.low_price = low_price
            existing.close_price = close_price
            existing.adj_close_price = adj_close_price
            existing.volume = volume

    db.flush()
    return written


def _upsert_indicators(db: Session, stock: Stock, history: pd.DataFrame) -> None:
    persisted_rows = db.execute(
        select(
            StockPriceHistory.trade_date,
            StockPriceHistory.close_price,
        )
        .where(StockPriceHistory.stock_id == stock.id)
        .order_by(StockPriceHistory.trade_date.asc())
    ).all()
    persisted_history = pd.DataFrame(
        [
            {
                "Date": pd.Timestamp(trade_date),
                "Close": close_price,
            }
            for trade_date, close_price in persisted_rows
        ]
    )

    incremental_history = history[["Date", "Close"]].copy()
    incremental_history["Date"] = incremental_history["Date"].apply(
        lambda value: pd.Timestamp(value).tz_localize(None) if pd.Timestamp(value).tzinfo else pd.Timestamp(value)
    )

    frames = [frame for frame in (persisted_history, incremental_history) if not frame.empty]
    if not frames:
        return

    working = pd.concat(frames, ignore_index=True)
    working["Close"] = pd.to_numeric(working["Close"], errors="coerce")
    working = working.dropna(subset=["Close"])
    working = working.sort_values("Date").drop_duplicates(subset=["Date"], keep="last")
    if working.empty:
        return

    working["moving_average_44"] = working["Close"].rolling(window=44).mean()
    for _, row in working.iterrows():
        indicator_date = pd.Timestamp(row["Date"]).date()
        close_price = float(row["Close"])
        moving_average_44 = _to_float(row.get("moving_average_44"))
        is_above_44_ma = bool(moving_average_44 is not None and close_price > moving_average_44)
        percent_above_44_ma = None
        if moving_average_44 and moving_average_44 != 0:
            percent_above_44_ma = ((close_price - moving_average_44) / moving_average_44) * 100

        indicator = db.scalar(
            select(StockIndicator).where(
                StockIndicator.stock_id == stock.id,
                StockIndicator.as_of_date == indicator_date,
            )
        )

        if indicator is None:
            db.add(
                StockIndicator(
                    stock_id=stock.id,
                    as_of_date=indicator_date,
                    moving_average_44=moving_average_44,
                    is_above_44_ma=is_above_44_ma,
                    percent_above_44_ma=percent_above_44_ma,
                )
            )
        else:
            indicator.moving_average_44 = moving_average_44
            indicator.is_above_44_ma = is_above_44_ma
            indicator.percent_above_44_ma = percent_above_44_ma

    db.flush()


def _to_float(value) -> float | None:
    if value is None or pd.isna(value):
        return None
    return float(value)


def _to_int(value) -> int | None:
    if value is None or pd.isna(value):
        return None
    return int(value)


def _build_sync_warning(failed_symbols: list[str], unchanged_symbols: list[str] | None = None) -> str | None:
    unchanged_symbols = unchanged_symbols or []
    messages: list[str] = []

    if failed_symbols:
        preview = ", ".join(failed_symbols[:10])
        if len(failed_symbols) > 10:
            preview = f"{preview}, ..."
        messages.append(f"No market data returned for {len(failed_symbols)} stocks: {preview}")

    if unchanged_symbols:
        preview = ", ".join(unchanged_symbols[:10])
        if len(unchanged_symbols) > 10:
            preview = f"{preview}, ..."
        messages.append(f"No new rows written for {len(unchanged_symbols)} stocks: {preview}")

    if not messages:
        return None

    return " | ".join(messages)
