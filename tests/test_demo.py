from datetime import date, timedelta

from back_end_library.models import Book

from .conftest import AUTH

NEW_BOOK = {"title": "Meu livro", "author": "Alguém", "gender": "Romance"}


def add_example(db, title="Exemplo"):
    book = Book(title=title, author="Autor", gender="Romance", is_example=True)
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


def test_requires_credentials(client):
    assert client.get("/books").status_code == 401


def test_ping_touches_database(client):
    response = client.get("/ping")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "demo": True}


def test_example_book_cannot_be_updated(client, db):
    book = add_example(db)
    response = client.put(f"/update/{book.id}", json={"favorite": True}, headers=AUTH)
    assert response.status_code == 403


def test_example_book_cannot_be_deleted(client, db):
    book = add_example(db)
    assert client.delete(f"/delete/{book.id}", headers=AUTH).status_code == 403
    assert client.get(f"/books/{book.id}", headers=AUTH).status_code == 200


def test_visitor_can_manage_own_book(client):
    created = client.post("/create", json=NEW_BOOK, headers=AUTH)
    assert created.status_code == 201
    body = created.json()
    assert body["is_example"] is False

    updated = client.put(f"/update/{body['id']}", json={"reading_status": "read", "grade": 5}, headers=AUTH)
    assert updated.status_code == 200
    assert updated.json()["finished_date"] == date.today().isoformat()

    assert client.delete(f"/delete/{body['id']}", headers=AUTH).status_code == 204


def test_visitor_cannot_create_example(client):
    response = client.post("/create", json={**NEW_BOOK, "is_example": True}, headers=AUTH)
    assert response.json()["is_example"] is False


def test_old_visitor_books_are_cleaned(client, db):
    example = add_example(db)
    old = Book(title="Velho", author="A", gender="B", add_date=date.today() - timedelta(days=3))
    db.add(old)
    db.commit()

    titles = [b["title"] for b in client.get("/books", headers=AUTH).json()]
    assert "Velho" not in titles
    assert example.title in titles


def test_visitor_books_are_capped(client, db):
    add_example(db)
    for i in range(5):
        client.post("/create", json={**NEW_BOOK, "title": f"Livro {i}"}, headers=AUTH)

    books = client.get("/books", headers=AUTH).json()
    visitor_titles = [b["title"] for b in books if not b["is_example"]]
    assert visitor_titles == ["Livro 2", "Livro 3", "Livro 4"]
    assert len(books) == 4


def test_profile_is_created_and_locked(client):
    profile = client.get("/profile", headers=AUTH)
    assert profile.status_code == 200
    assert profile.json()["id"] == 1

    assert client.put("/profile", json={"photo_url": "https://x"}, headers=AUTH).status_code == 403
    upload = client.post("/profile/upload", files={"file": ("a.png", b"x", "image/png")}, headers=AUTH)
    assert upload.status_code == 403
