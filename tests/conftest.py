import base64
import os
import tempfile

import pytest

# configuração antes de importar a app: banco SQLite temporário e modo demo ligado
_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_db_file.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_db_file.name}"
os.environ["APP_USERNAME"] = "visitante"
os.environ["APP_PASSWORD"] = "biblioteca2026"
os.environ["DEMO_MODE"] = "true"
os.environ["DEMO_MAX_VISITOR_BOOKS"] = "3"

from fastapi.testclient import TestClient  # noqa: E402

from back_end_library.database import engine, SessionLocal  # noqa: E402
from back_end_library.main import app  # noqa: E402
from back_end_library.models import Base  # noqa: E402

AUTH = {"Authorization": "Basic " + base64.b64encode(b"visitante:biblioteca2026").decode()}


@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()


def pytest_sessionfinish(session, exitstatus):
    engine.dispose()
    os.unlink(_db_file.name)
