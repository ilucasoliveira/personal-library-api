from datetime import date

from .conftest import bearer, register

NEW_BOOK = {"title": "Meu livro", "author": "Alguém", "gender": "Romance"}


def test_user_manages_own_book(client, auth):
    created = client.post("/create", json=NEW_BOOK, headers=auth)
    assert created.status_code == 201
    book = created.json()
    assert book["is_example"] is False
    assert book["add_date"] == date.today().isoformat()

    updated = client.put(f"/update/{book['id']}", json={"reading_status": "read", "grade": 5}, headers=auth)
    assert updated.status_code == 200
    assert updated.json()["finished_date"] == date.today().isoformat()

    assert client.delete(f"/delete/{book['id']}", headers=auth).status_code == 204
    assert client.get("/books", headers=auth).json() == []


def test_shelves_are_isolated(client):
    ana = bearer(register(client, email="ana@example.com"))
    bia = bearer(register(client, email="bia@example.com", name="Bia"))

    book_id = client.post("/create", json=NEW_BOOK, headers=ana).json()["id"]

    assert client.get("/books", headers=bia).json() == []
    # para a outra pessoa, o livro simplesmente não existe
    assert client.get(f"/books/{book_id}", headers=bia).status_code == 404
    assert client.put(f"/update/{book_id}", json={"grade": 1}, headers=bia).status_code == 404
    assert client.delete(f"/delete/{book_id}", headers=bia).status_code == 404

    assert client.get(f"/books/{book_id}", headers=ana).json()["grade"] is None


def test_user_cannot_create_example(client, auth):
    response = client.post("/create", json={**NEW_BOOK, "is_example": True}, headers=auth)
    assert response.json()["is_example"] is False


def test_book_limit_per_user(client, auth):
    for i in range(5):
        assert client.post("/create", json={**NEW_BOOK, "title": f"Livro {i}"}, headers=auth).status_code == 201
    assert client.post("/create", json=NEW_BOOK, headers=auth).status_code == 409


def test_orphan_books_are_invisible(client, auth, db):
    from back_end_library.models import Book

    db.add(Book(title="Sem dono", author="A", gender="B"))
    db.commit()
    assert client.get("/books", headers=auth).json() == []


def test_reading_status_is_validated(client, auth):
    assert client.post("/create", json={**NEW_BOOK, "reading_status": "banana"}, headers=auth).status_code == 422
    book = client.post("/create", json=NEW_BOOK, headers=auth).json()
    assert book["reading_status"] == "toRead"
    assert client.put(f"/update/{book['id']}", json={"reading_status": "banana"}, headers=auth).status_code == 422
    assert client.put(f"/update/{book['id']}", json={"reading_status": "reading"}, headers=auth).json()["reading_status"] == "reading"


def test_rest_routes(client, auth):
    created = client.post("/books", json=NEW_BOOK, headers=auth)
    assert created.status_code == 201
    book_id = created.json()["id"]

    assert client.put(f"/books/{book_id}", json={"grade": 4}, headers=auth).json()["grade"] == 4
    assert client.patch(f"/books/{book_id}", json={"favorite": True}, headers=auth).json()["favorite"] is True
    assert client.delete(f"/books/{book_id}", headers=auth).status_code == 204
    assert client.get(f"/books/{book_id}", headers=auth).status_code == 404


def test_grade_in_quarter_steps(client, auth):
    book = client.post("/books", json=NEW_BOOK, headers=auth).json()
    for grade in (0.25, 2.5, 3.75, 5):
        response = client.patch(f"/books/{book['id']}", json={"grade": grade}, headers=auth)
        assert response.status_code == 200, grade
        assert response.json()["grade"] == grade
    # fora do passo de 0.25 ou fora de 0.25 a 5: recusa e a nota anterior fica
    for grade in (0, 0.3, 3.8, 5.25, -1):
        assert client.patch(f"/books/{book['id']}", json={"grade": grade}, headers=auth).status_code == 422, grade
    assert client.get(f"/books/{book['id']}", headers=auth).json()["grade"] == 5


def test_null_clears_optional_fields(client, auth):
    book = client.post("/books", json={**NEW_BOOK, "synopsis": "Uma história.", "cover_url": "https://x.com/c.jpg"}, headers=auth).json()
    filled = client.patch(f"/books/{book['id']}", json={"grade": 5, "comment": "Bom."}, headers=auth).json()
    assert (filled["grade"], filled["comment"]) == (5, "Bom.")

    cleared = client.patch(
        f"/books/{book['id']}", json={"grade": None, "comment": None, "synopsis": None, "cover_url": "  "}, headers=auth
    ).json()
    assert (cleared["grade"], cleared["comment"], cleared["synopsis"], cleared["cover_url"]) == (None, None, None, None)
    # campo que não veio no corpo não muda
    assert cleared["title"] == NEW_BOOK["title"]

    for field in ("title", "author", "gender", "reading_status", "favorite"):
        response = client.patch(f"/books/{book['id']}", json={field: None}, headers=auth)
        assert response.status_code == 422, field


def test_errors_have_codes(client, auth):
    assert client.get("/books/999999", headers=auth).json()["code"] == "book_not_found"
    assert client.get("/books").json()["code"] == "invalid_session"
    assert client.get("/nao-existe").json()["code"] == "not_found"
    body = client.post("/books", json={"title": ""}, headers=auth).json()
    assert body["code"] == "validation_error" and isinstance(body["detail"], list)
