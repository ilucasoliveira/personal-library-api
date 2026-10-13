from back_end_library.models import User

from .conftest import PASSWORD, bearer, register


def login(client, email="ana@example.com", password=PASSWORD):
    return client.post("/auth/login", data={"username": email, "password": password})


def test_ping_reports_flags(client):
    response = client.get("/ping")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "demo": True, "signup": True}


def test_books_require_login(client):
    assert client.get("/books").status_code == 401
    assert client.get("/books", headers={"Authorization": "Bearer nonsense"}).status_code == 401


def test_register_returns_token_and_user(client):
    body = register(client, email="  Ana@Example.COM ")
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == "ana@example.com"
    assert body["user"]["theme"] == "twilight"
    assert body["user"]["language"] == "pt"
    assert "password_hash" not in body["user"]
    assert client.get("/me", headers=bearer(body)).json()["name"] == "Ana"


def test_password_is_hashed(client, db):
    register(client)
    user = db.query(User).one()
    assert user.password_hash != PASSWORD
    assert user.password_hash.startswith("$2")


def test_duplicate_email_is_rejected(client):
    register(client)
    response = client.post("/auth/register", json={"name": "Outra", "email": "ANA@example.com", "password": PASSWORD})
    assert response.status_code == 409


def test_register_validates_input(client):
    short = client.post("/auth/register", json={"name": "Ana", "email": "a@example.com", "password": "123"})
    bad_email = client.post("/auth/register", json={"name": "Ana", "email": "not-an-email", "password": PASSWORD})
    blank_name = client.post("/auth/register", json={"name": "   ", "email": "b@example.com", "password": PASSWORD})
    assert short.status_code == bad_email.status_code == blank_name.status_code == 422


def test_login_with_right_and_wrong_password(client):
    register(client)
    ok = login(client, email="ANA@example.com")
    assert ok.status_code == 200
    assert client.get("/me", headers=bearer(ok.json())).status_code == 200
    assert login(client, password="errada-123").status_code == 401
    assert login(client, email="ninguem@example.com").status_code == 401


def test_login_is_rate_limited_after_failures(client):
    register(client)
    for _ in range(5):
        assert login(client, password="errada-123").status_code == 401
    # depois de 5 erros, até a senha certa espera
    assert login(client).status_code == 429


def test_signup_can_be_disabled(client, monkeypatch):
    monkeypatch.setattr("back_end_library.routers.auth.ALLOW_SIGNUP", False)
    response = client.post("/auth/register", json={"name": "Ana", "email": "a@example.com", "password": PASSWORD})
    assert response.status_code == 403


def test_signups_are_rate_limited_per_ip(client):
    for i in range(5):
        register(client, email=f"user{i}@example.com")
    response = client.post("/auth/register", json={"name": "X", "email": "x@example.com", "password": PASSWORD})
    assert response.status_code == 429


def test_visitor_cannot_log_in_with_password(client, visitor):
    assert login(client, email="visitante@demo.invalid", password="!").status_code == 401


def test_visitor_endpoint_only_in_demo(client, monkeypatch):
    monkeypatch.setattr("back_end_library.routers.auth.DEMO_MODE", False)
    assert client.post("/auth/visitor").status_code == 404


def test_visitor_endpoint_without_seed(client):
    assert client.post("/auth/visitor").status_code == 503
