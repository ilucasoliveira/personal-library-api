from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..config import DEMO_MAX_VISITOR_BOOKS, DEMO_MODE, DEMO_VISITOR_BOOK_DAYS, MAX_BOOKS_PER_USER
from ..database import get_db
from ..errors import ApiError
from ..models import Book, User
from ..schemas import SchemaBook, SchemaBookResponse, UpdateSchemaBook

router = APIRouter()

EXAMPLE_LOCKED = "Examples cannot be deleted or updated."
BOOK_LIMIT = "Book limit reached."


def is_demo_visitor(user: User) -> bool:
    return DEMO_MODE and user.is_visitor


def own_books(db: Session, user: User):
    """Toda consulta de livros passa por aqui: cada pessoa só enxerga a própria estante."""
    return db.query(Book).filter(Book.user_id == user.id)


def clean_visitor_books(db: Session, user: User):
    """Na conta de visitante, apaga os livros adicionados há mais tempo que o prazo configurado."""
    if not is_demo_visitor(user):
        return
    limit_date = date.today() - timedelta(days=DEMO_VISITOR_BOOK_DAYS)
    own_books(db, user).filter(Book.is_example.is_(False), Book.add_date < limit_date).delete(
        synchronize_session=False
    )
    db.commit()


def make_room_for_new_book(db: Session, user: User):
    """Visitante: mantém no máximo DEMO_MAX_VISITOR_BOOKS (sai o mais antigo). Contas: barra no limite."""
    if is_demo_visitor(user):
        visitor_books = own_books(db, user).filter(Book.is_example.is_(False)).order_by(Book.id)
        excess = visitor_books.count() - DEMO_MAX_VISITOR_BOOKS + 1
        if excess > 0:
            for old_book in visitor_books.limit(excess).all():
                db.delete(old_book)
            db.commit()
    elif own_books(db, user).count() >= MAX_BOOKS_PER_USER:
        raise ApiError(409, "book_limit", BOOK_LIMIT)


def get_book_or_404(id: int, db: Session, user: User) -> Book:
    # livro de outra pessoa responde 404, igual a um livro que não existe
    book = own_books(db, user).filter(Book.id == id).first()
    if book is None:
        raise ApiError(404, "book_not_found", "Book not found.")
    return book


# Rotas REST (/books e /books/{id}). As antigas (/create, /update/{id}, /delete/{id}) continuam
# respondendo igual, marcadas como obsoletas na documentação, para não quebrar quem já usa.
@router.post("/books", status_code=201, response_model=SchemaBookResponse)
@router.post("/create", status_code=201, response_model=SchemaBookResponse, deprecated=True)
def create_book(book: SchemaBook, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    clean_visitor_books(db, user)
    make_room_for_new_book(db, user)

    new_book = Book(**book.model_dump(), user_id=user.id)
    if new_book.reading_status == "read":
        new_book.finished_date = date.today()
    db.add(new_book)
    db.commit()
    db.refresh(new_book)
    return new_book


@router.get("/books", response_model=list[SchemaBookResponse])
def read_books(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    clean_visitor_books(db, user)
    return own_books(db, user).order_by(Book.id).all()


@router.get("/books/{id}", response_model=SchemaBookResponse)
def read_one_book(id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_book_or_404(id, db, user)


@router.patch("/books/{id}", response_model=SchemaBookResponse)
@router.put("/books/{id}", response_model=SchemaBookResponse)
@router.put("/update/{id}", response_model=SchemaBookResponse, deprecated=True)
def update_book(
    id: int, update_book: UpdateSchemaBook, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Muda só os campos enviados. null apaga sinopse, nota, comentário ou capa;
    título, autor, gênero, status e favorito não aceitam null (422)."""
    book = get_book_or_404(id, db, user)

    if book.is_example:
        raise ApiError(403, "example_read_only", EXAMPLE_LOCKED)

    changes = update_book.model_dump(exclude_unset=True)
    for field, value in changes.items():
        if field == "reading_status" and value != book.reading_status:
            # a data de leitura acompanha o status: entra ao marcar como lido, sai ao desmarcar
            book.finished_date = date.today() if value == "read" else None
        setattr(book, field, value)

    db.commit()
    db.refresh(book)
    return book


@router.delete("/books/{id}", status_code=204)
@router.delete("/delete/{id}", status_code=204, deprecated=True)
def delete_book(id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    book = get_book_or_404(id, db, user)

    if book.is_example:
        raise ApiError(403, "example_read_only", EXAMPLE_LOCKED)

    db.delete(book)
    db.commit()
