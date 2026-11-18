import os

import pytest
from fastapi.testclient import TestClient

os.environ["DB_DIALECT"] = "sqlite"
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["AUTH_MODE"] = "dev"

from app.db import Base, SessionLocal, engine, get_db  # noqa: E402
from app.main import create_app  # noqa: E402
from app.seed import seed_if_empty  # noqa: E402
from app.settings import get_settings  # noqa: E402

get_settings.cache_clear()


@pytest.fixture()
def db_session():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    seed_if_empty(session)
    yield session
    session.close()


@pytest.fixture()
def client(db_session):
    app = create_app()

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c