import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from backend.app.core.config import settings

Base = declarative_base()

_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        is_test = "pytest" in sys.modules or getattr(settings, "TESTING", False)
        try:
            _engine = create_engine(
                settings.DATABASE_URL,
                pool_pre_ping=True,
                future=True,
            )
            # Test connection import capability
            _engine.connect().close()
        except Exception as exc:
            # SQLite is strictly a test/development fallback, NEVER a production fallback.
            # In production, a PostgreSQL/PostGIS connection failure MUST raise an error.
            if is_test or (settings.ENVIRONMENT != "production" and settings.DATABASE_URL.startswith("sqlite")):
                _engine = create_engine(
                    "sqlite:///:memory:",
                    connect_args={"check_same_thread": False},
                    future=True,
                )
            else:
                raise RuntimeError(
                    f"Failed to connect to primary PostgreSQL/PostGIS database at '{settings.DATABASE_URL}'. "
                    "Production environment forbids falling back to an incompatible SQLite database."
                ) from exc
    return _engine



def get_sessionmaker():
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)
    return _SessionLocal


def get_db():
    SessionFactory = get_sessionmaker()
    db = SessionFactory()
    try:
        yield db
    finally:
        db.close()
