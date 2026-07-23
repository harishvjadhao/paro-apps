from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

import pandas as pd
import yfinance as yf
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.stock import Stock
from app.models.stock_indicator import StockIndicator
from app.models.stock_price_history import StockPriceHistory
from app.models.sync_log import SyncLog
from app.services.sample_data_service import build_sample_history


SYNC_STATUS_IDLE = "idle"
SYNC_STATUS_RUNNING = "running"
SYNC_STATUS_SUCCESS = "success"
SYNC_STATUS_PARTIAL = "partial"
SYNC_STATUS_FAILED = "failed"


@dataclass
class SyncResult:
    status: str
    stocks_processed: int
    stocks_updated: int
    error_message: str | None = None
    last_successful_sync_at: datetime | None = None
    last_sync_started_at: datetime | None = None


def run_sync(db: Session, source: str = "manual") -> SyncResult:
    settings = get_settings()
    started_at = datetime.now(UTC)
    sync_log = SyncLog(started_at=started_at, status=SYNC_STATUS_RUNNING, source=source)
    db.add(sync_log)
    db.commit()
    db.refresh(sync_log)

    stocks_processed = 0
    stocks_updated = 0
    failed_symbols: list[str] = []

    try:
        stocks = db.scalars(select(Stock).where(Stock.is_active.is_(True)).order_by(Stock.symbol.asc())).all()
        force_sample_mode = settings.data_source_mode.lower() == "mock" and source != "api"

        for stock in stocks:
            history = build_sample_history(stock) if force_sample_mode else _download_history(stock.yahoo_ticker)
            if history.empty:
                if source != "api":
                    history = build_sample_history(stock)

                if history.empty:
                    failed_symbols.append(stock.symbol)
                    stocks_processed += 1
                    continue

            rows_written = _upsert_price_history(db, stock, history)
            _upsert_indicators(db, stock, history)
            stocks_processed += 1
            if rows_written > 0:
                stocks_updated += 1

        finished_at = datetime.now(UTC)
        error_message = _build_sync_warning(failed_symbols)
        status = SYNC_STATUS_PARTIAL if failed_symbols else SYNC_STATUS_SUCCESS
        sync_log.finished_at = finished_at
        sync_log.status = status
        sync_log.stocks_processed = stocks_processed
        sync_log.stocks_updated = stocks_updated
        sync_log.error_message = error_message
        db.commit()

        return SyncResult(
            status=status,
            stocks_processed=stocks_processed,
            stocks_updated=stocks_updated,
            error_message=error_message,
            last_successful_sync_at=finished_at,
            last_sync_started_at=started_at,
        )
    except Exception as exc:  # noqa: BLE001
        finished_at = datetime.now(UTC)
        sync_log.finished_at = finished_at
        sync_log.status = SYNC_STATUS_FAILED
        sync_log.stocks_processed = stocks_processed
        sync_log.stocks_updated = stocks_updated
        sync_log.error_message = str(exc)
        db.commit()
        return SyncResult(
            status=SYNC_STATUS_FAILED,
            stocks_processed=stocks_processed,
            stocks_updated=stocks_updated,
            error_message=str(exc),
            last_sync_started_at=started_at,
        )


def get_latest_sync_status(db: Session) -> SyncResult:
    latest = db.scalar(select(SyncLog).order_by(SyncLog.started_at.desc()))
    if latest is None:
        return SyncResult(status=SYNC_STATUS_IDLE, stocks_processed=0, stocks_updated=0)

    return SyncResult(
        status=latest.status,
        stocks_processed=latest.stocks_processed,
        stocks_updated=latest.stocks_updated,
        error_message=latest.error_message,
        last_successful_sync_at=latest.finished_at if latest.status == SYNC_STATUS_SUCCESS else None,
        last_sync_started_at=latest.started_at,
    )


def _download_history(yahoo_ticker: str) -> pd.DataFrame:
    history = yf.download(yahoo_ticker, period="1y", interval="1d", auto_adjust=False, progress=False)
    if history.empty:
        return history

    history = history.reset_index()
    history.columns = [str(column) for column in history.columns]
    return history


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
    working = history.copy()
    working["Close"] = pd.to_numeric(working["Close"], errors="coerce")
    working = working.dropna(subset=["Close"])
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


def _build_sync_warning(failed_symbols: list[str]) -> str | None:
    if not failed_symbols:
        return None

    preview = ", ".join(failed_symbols[:10])
    if len(failed_symbols) > 10:
        preview = f"{preview}, ..."

    return f"No market data returned for {len(failed_symbols)} stocks: {preview}"
