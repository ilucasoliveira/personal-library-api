from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..config import DEMO_MAX_VISITOR_BOOKS, DEMO_MODE, DEMO_VISITOR_BOOK_DAYS, MAX_BOOKS_PER_USER
from ..database import get_db
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
        raise HTTPException(status_code=409, detail=BOOK_LIMIT)


def get_book_or_404(id: int, db: Session, user: User) -> Book:
    # livro de outra pessoa responde 404, igual a um livro que não existe
    book = own_books(db, user).filter(Book.id == id).first()
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found.")
    return book


@router.post("/create", status_code=201, response_model=SchemaBookResponse)
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


@router.put("/update/{id}", response_model=SchemaBookResponse)
def update_book(
    id: int, update_book: UpdateSchemaBook, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    book = get_book_or_404(id, db, user)

    if book.is_example:
        raise HTTPException(status_code=403, detail=EXAMPLE_LOCKED)

    if update_book.title is not None:
        book.title = update_book.title
    if update_book.author is not None:
        book.author = update_book.author
    if update_book.gender is not None:
        book.gender = update_book.gender
    if update_book.synopsis is not None:
        book.synopsis = update_book.synopsis
    if update_book.grade is not None:
        book.grade = update_book.grade
    if update_book.comment is not None:
        book.comment = update_book.comment
    if update_book.favorite is not None:
        book.favorite = update_book.favorite
    if update_book.cover_url is not None:
        book.cover_url = update_book.cover_url
    if update_book.reading_status is not None:
        book.reading_status = update_book.reading_status
        if book.reading_status == "read":
            book.finished_date = date.today()
        else:
            book.finished_date = None

    db.commit()
    db.refresh(book)
    return book


@router.delete("/delete/{id}", status_code=204)
def delete_book(id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    book = get_book_or_404(id, db, user)

    if book.is_example:
        raise HTTPException(status_code=403, detail=EXAMPLE_LOCKED)

    db.delete(book)
    db.commit()
