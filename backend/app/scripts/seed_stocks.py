from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.services.seed_service import seed_stocks_from_csv


def main() -> None:
    init_db()
    with SessionLocal() as db:
        processed = seed_stocks_from_csv(db)
    print(f"Seeded or updated {processed} stock records.")


if __name__ == "__main__":
    main()