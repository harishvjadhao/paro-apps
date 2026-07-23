import csv
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.stock import Stock
from app.services.ticker_mapping import load_ticker_overrides, map_symbol_to_yahoo_ticker


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_STOCK_CSV_PATH = REPO_ROOT / "ind_nifty200list.csv"


def seed_stocks_from_csv(db: Session, csv_path: Path | None = None) -> int:
    stock_csv_path = csv_path or DEFAULT_STOCK_CSV_PATH
    if not stock_csv_path.exists():
        raise FileNotFoundError(f"Stock CSV not found: {stock_csv_path}")

    overrides = load_ticker_overrides()
    processed = 0

    with stock_csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            symbol = (row.get("Symbol") or "").strip()
            if not symbol:
                continue

            company_name = (row.get("Company Name") or "").strip()
            industry = (row.get("Industry") or "").strip()
            series = (row.get("Series") or "").strip() or None
            isin_code = (row.get("ISIN Code") or "").strip() or None
            yahoo_ticker = map_symbol_to_yahoo_ticker(symbol, overrides)

            existing = db.scalar(select(Stock).where(Stock.symbol == symbol))
            if existing is None:
                stock = Stock(
                    symbol=symbol,
                    company_name=company_name,
                    industry=industry,
                    series=series,
                    isin_code=isin_code,
                    yahoo_ticker=yahoo_ticker,
                    is_active=True,
                )
                db.add(stock)
            else:
                existing.company_name = company_name
                existing.industry = industry
                existing.series = series
                existing.isin_code = isin_code
                existing.yahoo_ticker = yahoo_ticker
                existing.is_active = True

            processed += 1

    db.commit()
    return processed