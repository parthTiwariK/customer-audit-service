from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.settings import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()
_url = settings.db_url
_is_sqlite = _url.startswith("sqlite")
_is_sqlite_memory = _is_sqlite and ":memory:" in _url
_connect_args: dict = {"check_same_thread": False} if _is_sqlite else {}
if _url.startswith("mysql") and settings.db_ssl_ca:
    _connect_args["ssl"] = {"ca": settings.db_ssl_ca}

_engine_kwargs: dict = {
    "pool_pre_ping": True,
    "connect_args": _connect_args,
}
if _url.startswith("mysql"):
    _engine_kwargs["pool_recycle"] = 280
if _is_sqlite_memory:
    _engine_kwargs["poolclass"] = StaticPool
engine = create_engine(_url, **_engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()