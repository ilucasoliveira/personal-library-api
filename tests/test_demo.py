from datetime import date, timedelta

from back_end_library.models import Book, User

from .conftest import register, bearer

NEW_BOOK = {"title": "Meu livro", "author": "Alguém", "gender": "Romance"}


def visitor_id(db) -> int:
    return db.query(User).filter(User.is_visitor.is_(True)).one().id


def add_example(db, title="Exemplo"):
    book = Book(title=title, author="Autor", gender="Romance", is_example=True, user_id=visitor_id(db))
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


def test_example_book_cannot_be_updated(client, visitor, db):
    book = add_example(db)
    assert client.put(f"/update/{book.id}", json={"favorite": True}, headers=visitor).status_code == 403


def test_example_book_cannot_be_deleted(client, visitor, db):
    book = add_example(db)
    assert client.delete(f"/delete/{book.id}", headers=visitor).status_code == 403
    assert client.get(f"/books/{book.id}", headers=visitor).status_code == 200


def test_visitor_can_manage_own_book(client, visitor):
    book = client.post("/create", json=NEW_BOOK, headers=visitor).json()
    assert client.put(f"/update/{book['id']}", json={"grade": 4}, headers=visitor).status_code == 200
    assert client.delete(f"/delete/{book['id']}", headers=visitor).status_code == 204


def test_old_visitor_books_are_cleaned(client, visitor, db):
    example = add_example(db)
    old = Book(title="Velho", author="A", gender="B", user_id=visitor_id(db), add_date=date.today() - timedelta(days=3))
    db.add(old)
    db.commit()

    titles = [b["title"] for b in client.get("/books", headers=visitor).json()]
    assert titles == [example.title]


def test_visitor_books_are_capped(client, visitor, db):
    add_example(db)
    for i in range(5):
        client.post("/create", json={**NEW_BOOK, "title": f"Livro {i}"}, headers=visitor)

    books = client.get("/books", headers=visitor).json()
    added = [b["title"] for b in books if not b["is_example"]]
    # limite de 3 nos testes: saem os mais antigos
    assert added == ["Livro 2", "Livro 3", "Livro 4"]
    assert sum(b["is_example"] for b in books) == 1


def test_demo_rules_do_not_touch_real_accounts(client, visitor, db):
    ana = bearer(register(client))
    user_id = db.query(User).filter(User.email == "ana@example.com").one().id
    db.add(Book(title="Antigo", author="A", gender="B", user_id=user_id, add_date=date.today() - timedelta(days=30)))
    db.commit()

    # o visitante lista e cria livros (o que dispara a limpeza), mas a estante da Ana não muda
    client.get("/books", headers=visitor)
    client.post("/create", json=NEW_BOOK, headers=visitor)
    assert [b["title"] for b in client.get("/books", headers=ana).json()] == ["Antigo"]


def test_visitor_settings_are_locked(client, visitor):
    assert client.get("/me", headers=visitor).json()["is_visitor"] is True
    assert client.put("/me", json={"theme": "paper"}, headers=visitor).status_code == 403
    assert client.put("/me/password", json={"current_password": "x", "new_password": "12345678"}, headers=visitor).status_code == 403
    assert client.request("DELETE", "/me", json={"password": "x"}, headers=visitor).status_code == 403
