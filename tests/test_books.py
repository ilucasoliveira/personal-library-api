from datetime import date

from .conftest import bearer, register

NEW_BOOK = {"title": "Meu livro", "author": "Alguém", "gender": "Romance"}


def test_user_manages_own_book(client, auth):
    created = client.post("/create", json=NEW_BOOK, headers=auth)
    assert created.status_code == 201
    book = created.json()
    assert book["is_example"] is False

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
