import pytest

from back_end_library import manage
from back_end_library.models import Book, User

from .conftest import PASSWORD, register


@pytest.fixture
def typed_password(monkeypatch):
    """Simula a senha digitada no terminal (duas vezes: senha e confirmação)."""
    monkeypatch.setattr(manage.getpass, "getpass", lambda prompt="": "nova-senha-123")


def test_create_user_claims_orphan_books(db, typed_password):
    db.add(Book(title="Antigo", author="A", gender="B"))
    db.commit()

    manage.create_user("Thur@Example.com", "Thur", claim_orphans=True, language="pt")

    db.expire_all()
    user = db.query(User).one()
    assert user.email == "thur@example.com"
    assert db.query(Book).one().user_id == user.id


def test_reset_password(client, typed_password):
    register(client)
    manage.reset_password("ANA@example.com")

    old = client.post("/auth/login", data={"username": "ana@example.com", "password": PASSWORD})
    new = client.post("/auth/login", data={"username": "ana@example.com", "password": "nova-senha-123"})
    assert old.status_code == 401
    assert new.status_code == 200
