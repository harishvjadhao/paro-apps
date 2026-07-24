from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings


settings = get_settings()

engine = create_engine(
    settings.sqlite_url,
    connect_args={"check_same_thread": False, "timeout": 30},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)


@event.listens_for(engine, "connect")
def configure_sqlite(connection, _record) -> None:
    cursor = connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=30000")
    cursor.close()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()