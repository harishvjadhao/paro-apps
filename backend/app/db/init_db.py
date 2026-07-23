from pathlib import Path

from app.db.base import Base
from app.db.session import engine
from app.models import ChartHighlightDate, Stock, StockComment, StockIndicator, StockPriceHistory, SyncLog  # noqa: F401


def init_db() -> None:
    db_path = Path(engine.url.database or "")
    if db_path:
        db_path.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)