import os
import tempfile

import pytest

# configuração antes de importar a app: banco SQLite temporário e modo demo ligado
_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_db_file.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_db_file.name}"
os.environ["DEMO_MODE"] = "true"
os.environ["ALLOW_SIGNUP"] = "true"
os.environ["DEMO_MAX_VISITOR_BOOKS"] = "3"
os.environ["MAX_BOOKS_PER_USER"] = "5"
os.environ["JWT_SECRET"] = "test-secret-with-enough-length-for-hs256"
os.environ["BCRYPT_ROUNDS"] = "4"

from fastapi.testclient import TestClient  # noqa: E402

from back_end_library.database import engine, SessionLocal  # noqa: E402
from back_end_library.main import app  # noqa: E402
from back_end_library.models import Base, User  # noqa: E402
from back_end_library.ratelimit import failed_logins, signups  # noqa: E402

PASSWORD = "senha-segura-123"


@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    failed_logins.clear()
    signups.clear()
    yield


@pytest.fixture
def client():
    return TestClient(app)


def register(client, email="ana@example.com", name="Ana", password=PASSWORD):
    response = client.post("/auth/register", json={"name": name, "email": email, "password": password})
    assert response.status_code == 201, response.text
    return response.json()


def bearer(token_response) -> dict:
    return {"Authorization": f"Bearer {token_response['access_token']}"}


@pytest.fixture
def auth(client):
    """Cabeçalho de uma conta comum recém-criada."""
    return bearer(register(client))


@pytest.fixture
def visitor(client, db):
    """Cria a conta de visitante (como o seed faz) e devolve o cabeçalho dela."""
    db.add(User(email="visitante@demo.invalid", name="Visitante", password_hash="!", is_visitor=True))
    db.commit()
    response = client.post("/auth/visitor")
    assert response.status_code == 200, response.text
    return bearer(response.json())


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()


def pytest_sessionfinish(session, exitstatus):
    engine.dispose()
    # no Windows o SQLite pode segurar o arquivo por um instante; nesse caso ele fica
    # na pasta temporária do sistema, que é limpa sozinha
    try:
        os.unlink(_db_file.name)
    except OSError:
        pass
