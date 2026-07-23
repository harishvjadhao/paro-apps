from __future__ import annotations

from datetime import UTC, datetime, timedelta
from random import Random

import pandas as pd

from app.models.stock import Stock


def build_sample_history(stock: Stock, periods: int = 66) -> pd.DataFrame:
    seed = sum(ord(character) for character in stock.symbol)
    random = Random(seed)
    anchor = 80 + (seed % 220)
    rows: list[dict[str, object]] = []
    current = datetime.now(UTC).date() - timedelta(days=periods * 2)
    close_price = float(anchor)

    while len(rows) < periods:
        if current.weekday() >= 5:
            current += timedelta(days=1)
            continue

        drift = ((seed % 7) - 3) * 0.08
        change = random.uniform(-2.4, 2.8) + drift
        open_price = max(5.0, close_price + random.uniform(-1.5, 1.5))
        close_price = max(5.0, open_price + change)
        high_price = max(open_price, close_price) + random.uniform(0.3, 2.2)
        low_price = max(1.0, min(open_price, close_price) - random.uniform(0.3, 2.0))
        volume = int(250000 + (seed % 1000) * 100 + random.uniform(0, 900000))

        rows.append(
            {
                "Date": pd.Timestamp(current),
                "Open": round(open_price, 2),
                "High": round(high_price, 2),
                "Low": round(low_price, 2),
                "Close": round(close_price, 2),
                "Adj Close": round(close_price, 2),
                "Volume": volume,
            }
        )
        current += timedelta(days=1)

    return pd.DataFrame(rows)