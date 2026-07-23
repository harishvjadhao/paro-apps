from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.services.sync_service import run_sync


def main() -> None:
    init_db()
    with SessionLocal() as db:
        result = run_sync(db, source="cli")
    print(
        f"Sync status: {result.status}; processed={result.stocks_processed}; updated={result.stocks_updated}; "
        f"error={result.error_message}"
    )


if __name__ == "__main__":
    main()