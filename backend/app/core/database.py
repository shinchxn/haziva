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
            # Test connection
            with _engine.connect() as conn:
                pass
        except Exception as exc:
            if is_test or settings.ENVIRONMENT != "production":
                _engine = create_engine(
                    "sqlite:///haziva_dev.db",
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
