from .conftest import PASSWORD, bearer, register


def test_update_settings(client, auth):
    response = client.put("/me", json={"theme": "sepia", "accent": "#2a9d8f", "language": "en", "name": " Ana Clara "}, headers=auth)
    assert response.status_code == 200
    body = response.json()
    assert (body["theme"], body["accent"], body["language"], body["name"]) == ("sepia", "#2a9d8f", "en", "Ana Clara")

    # só o que vem no corpo muda; accent null volta para a cor do tema
    body = client.put("/me", json={"accent": None}, headers=auth).json()
    assert body["accent"] is None
    assert body["theme"] == "sepia"


def test_settings_are_validated(client, auth):
    assert client.put("/me", json={"theme": "neon"}, headers=auth).status_code == 422
    assert client.put("/me", json={"accent": "red"}, headers=auth).status_code == 422
    assert client.put("/me", json={"language": "es"}, headers=auth).status_code == 422
    assert client.put("/me", json={"name": "   "}, headers=auth).status_code == 422


def test_change_password(client, auth):
    wrong = client.put("/me/password", json={"current_password": "errada-123", "new_password": "nova-senha-123"}, headers=auth)
    assert wrong.status_code == 400

    ok = client.put("/me/password", json={"current_password": PASSWORD, "new_password": "nova-senha-123"}, headers=auth)
    assert ok.status_code == 200
    login = client.post("/auth/login", data={"username": "ana@example.com", "password": "nova-senha-123"})
    assert login.status_code == 200


def test_password_change_ends_other_sessions(client):
    first = bearer(register(client))
    second = bearer(client.post("/auth/login", data={"username": "ana@example.com", "password": PASSWORD}).json())

    changed = client.put("/me/password", json={"current_password": PASSWORD, "new_password": "nova-senha-123"}, headers=first)
    assert changed.status_code == 200

    # os dois tokens antigos caem; o token devolvido pela troca continua valendo
    assert client.get("/me", headers=first).status_code == 401
    assert client.get("/me", headers=second).status_code == 401
    assert client.get("/me", headers=bearer(changed.json())).status_code == 200


def test_delete_account_removes_books(client, db):
    from back_end_library.models import Book, User

    ana = bearer(register(client))
    client.post("/create", json={"title": "T", "author": "A", "gender": "G"}, headers=ana)

    assert client.request("DELETE", "/me", json={"password": "errada-123"}, headers=ana).status_code == 400
    assert client.request("DELETE", "/me", json={"password": PASSWORD}, headers=ana).status_code == 204

    assert db.query(User).count() == 0
    assert db.query(Book).count() == 0
    # o token antigo deixa de valer
    assert client.get("/me", headers=ana).status_code == 401


def test_photo_upload_validates_type(client, auth):
    response = client.post("/me/photo", files={"file": ("a.txt", b"hello", "text/plain")}, headers=auth)
    assert response.status_code == 415


def test_photo_upload_validates_size(client, auth):
    big = b"0" * (2 * 1024 * 1024 + 1)
    response = client.post("/me/photo", files={"file": ("a.png", big, "image/png")}, headers=auth)
    assert response.status_code == 413


def test_photo_upload_replaces_old_photo(client, auth, monkeypatch):
    from back_end_library.routers import me

    base = "https://proj.supabase.co"
    monkeypatch.setattr(me, "SUPABASE_URL", base)
    monkeypatch.setattr(me, "SUPABASE_SERVICE_KEY", "service-key")
    calls = []

    class FakeAsyncClient:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, url, **kwargs):
            calls.append(("upload", url))
            return me.httpx.Response(200)

    monkeypatch.setattr(me.httpx, "AsyncClient", FakeAsyncClient)
    monkeypatch.setattr(me.httpx, "delete", lambda url, **k: calls.append(("delete", url)))

    first = client.post("/me/photo", files={"file": ("a.png", b"png", "image/png")}, headers=auth).json()["photo_url"]
    assert first.startswith(f"{base}/storage/v1/object/public/profile-photos/user-")
    client.post("/me/photo", files={"file": ("b.jpg", b"jpg", "image/jpeg")}, headers=auth)

    deleted = [url for kind, url in calls if kind == "delete"]
    assert deleted == [first.replace("/object/public/", "/object/")]


def fake_storage(monkeypatch, upload):
    """Troca o cliente HTTP do Storage por um falso; upload(url) devolve a resposta ou levanta erro."""
    from back_end_library.routers import me

    monkeypatch.setattr(me, "SUPABASE_URL", "https://proj.supabase.co")
    monkeypatch.setattr(me, "SUPABASE_SERVICE_KEY", "service-key")
    deleted = []

    class FakeAsyncClient:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, url, **kwargs):
            return upload(url)

    monkeypatch.setattr(me.httpx, "AsyncClient", FakeAsyncClient)
    monkeypatch.setattr(me.httpx, "delete", lambda url, **k: deleted.append(url))
    return me, deleted


def test_photo_upload_failure_is_logged(client, auth, monkeypatch, caplog):
    me, _ = fake_storage(monkeypatch, lambda url: me.httpx.Response(404, text='{"message":"Bucket not found"}'))
    response = client.post("/me/photo", files={"file": ("a.jpg", b"jpg", "image/jpeg")}, headers=auth)
    assert response.status_code == 502
    assert response.json()["code"] == "photo_upload_failed"
    assert "Bucket not found" in caplog.text
    assert client.get("/me", headers=auth).json()["photo_url"] is None


def test_photo_upload_storage_offline(client, auth, monkeypatch, caplog):
    def offline(url):
        raise me.httpx.ConnectError("nome não encontrado")

    me, _ = fake_storage(monkeypatch, offline)
    response = client.post("/me/photo", files={"file": ("a.jpg", b"jpg", "image/jpeg")}, headers=auth)
    assert response.status_code == 502
    assert "nome não encontrado" in caplog.text


def test_delete_photo(client, auth, monkeypatch):
    me, deleted = fake_storage(monkeypatch, lambda url: me.httpx.Response(200))
    photo = client.post("/me/photo", files={"file": ("a.jpg", b"jpg", "image/jpeg")}, headers=auth).json()["photo_url"]
    response = client.delete("/me/photo", headers=auth)
    assert response.status_code == 200
    assert response.json()["photo_url"] is None
    assert deleted == [photo.replace("/object/public/", "/object/")]


def test_visitor_cannot_delete_photo(client, visitor):
    assert client.delete("/me/photo", headers=visitor).status_code == 403


def test_storage_headers_follow_the_key_type(monkeypatch):
    from back_end_library.routers import me

    # chave nova: não é JWT, vai só no apikey
    monkeypatch.setattr(me, "SUPABASE_SERVICE_KEY", "sb_secret_abc123")
    assert me.storage_headers() == {"apikey": "sb_secret_abc123"}
    # chave antiga (service_role): é JWT, vai também no Authorization
    monkeypatch.setattr(me, "SUPABASE_SERVICE_KEY", "eyJhbGciOiJIUzI1NiJ9.x.y")
    assert me.storage_headers({"Content-Type": "image/jpeg"}) == {
        "apikey": "eyJhbGciOiJIUzI1NiJ9.x.y",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.x.y",
        "Content-Type": "image/jpeg",
    }


def test_upload_with_new_secret_key_sends_no_bearer(client, auth, monkeypatch):
    sent = []
    me, _ = fake_storage(monkeypatch, lambda url: me.httpx.Response(200))
    monkeypatch.setattr(me, "SUPABASE_SERVICE_KEY", "sb_secret_abc123")
    upload = me.httpx.AsyncClient.post

    async def recording_post(self, url, **kwargs):
        sent.append(kwargs["headers"])
        return await upload(self, url, **kwargs)

    monkeypatch.setattr(me.httpx.AsyncClient, "post", recording_post)
    response = client.post("/me/photo", files={"file": ("a.jpg", b"jpg", "image/jpeg")}, headers=auth)
    assert response.status_code == 200
    assert sent == [{"apikey": "sb_secret_abc123", "Content-Type": "image/jpeg"}]


def test_me_shows_when_the_account_was_created(client, auth):
    body = client.get("/me", headers=auth).json()
    assert body["created_at"]
