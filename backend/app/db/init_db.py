from pathlib import Path

from sqlalchemy import inspect, text

from app.db.base import Base
from app.db.session import engine
from app.models import ChartHighlightDate, Stock, StockComment, StockIndicator, StockPriceHistory, SyncLog  # noqa: F401


SQLITE_TABLE_MIGRATIONS: dict[str, tuple[tuple[str, str], ...]] = {
    "stocks": (
        ("last_sync_status", "ALTER TABLE stocks ADD COLUMN last_sync_status VARCHAR(30)"),
        ("last_sync_at", "ALTER TABLE stocks ADD COLUMN last_sync_at DATETIME"),
        ("last_sync_message", "ALTER TABLE stocks ADD COLUMN last_sync_message VARCHAR(500)"),
    ),
    "sync_logs": (
        ("failed_stocks", "ALTER TABLE sync_logs ADD COLUMN failed_stocks INTEGER DEFAULT 0"),
        ("mode", "ALTER TABLE sync_logs ADD COLUMN mode VARCHAR(30)"),
    ),
}


def _apply_sqlite_legacy_migrations() -> None:
    if engine.dialect.name != "sqlite":
        return

    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    with engine.begin() as connection:
        for table_name, migrations in SQLITE_TABLE_MIGRATIONS.items():
            if table_name not in existing_tables:
                continue

            existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
            for column_name, ddl in migrations:
                if column_name not in existing_columns:
                    connection.execute(text(ddl))

        # Create any newly introduced tables after older DBs have been patched.
        Base.metadata.create_all(bind=connection)


def init_db() -> None:
    db_path = Path(engine.url.database or "")
    if db_path:
        db_path.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    _apply_sqlite_legacy_migrations()