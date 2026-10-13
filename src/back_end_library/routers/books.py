from ..schemas import SchemaBook, SchemaBookResponse, UpdateSchemaBook
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBasicCredentials
from ..auth import user_authenticate
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Book
from ..config import DEMO_MODE, DEMO_MAX_VISITOR_BOOKS, DEMO_VISITOR_BOOK_DAYS
from datetime import date, timedelta

router = APIRouter()

EXAMPLE_LOCKED = "Examples cannot be deleted or updated."


def clean_visitor_books(db: Session):
    """Na demo, apaga os livros de visitantes mais antigos que o prazo configurado."""
    if not DEMO_MODE:
        return
    limit_date = date.today() - timedelta(days=DEMO_VISITOR_BOOK_DAYS)
    db.query(Book).filter(Book.is_example.is_(False), Book.add_date < limit_date).delete(
        synchronize_session=False
    )
    db.commit()


def make_room_for_visitor_book(db: Session):
    """Na demo, mantém no máximo DEMO_MAX_VISITOR_BOOKS livros de visitantes (sai o mais antigo)."""
    if not DEMO_MODE:
        return
    visitor_books = db.query(Book).filter(Book.is_example.is_(False)).order_by(Book.id)
    excess = visitor_books.count() - DEMO_MAX_VISITOR_BOOKS + 1
    if excess > 0:
        for old_book in visitor_books.limit(excess).all():
            db.delete(old_book)
        db.commit()


def get_book_or_404(id: int, db: Session) -> Book:
    book = db.query(Book).filter(Book.id == id).first()

    if book is None:
        raise HTTPException(status_code=404, detail="Book not found.")

    return book


@router.post("/create", status_code=201, response_model=SchemaBookResponse)
def create_book(book: SchemaBook, credentials: HTTPBasicCredentials=Depends(user_authenticate), db: Session=Depends(get_db)):
    clean_visitor_books(db)
    make_room_for_visitor_book(db)

    new_book = Book(**book.model_dump())
    if new_book.reading_status == "read":
        new_book.finished_date = date.today()
    db.add(new_book)
    db.commit()
    db.refresh(new_book)
    return new_book

@router.get("/books", response_model=list[SchemaBookResponse])
def read_books(credentials: HTTPBasicCredentials=Depends(user_authenticate), db: Session=Depends(get_db)):
    clean_visitor_books(db)
    books = db.query(Book).all()
    return books

@router.get("/books/{id}", response_model=SchemaBookResponse)
def read_one_book(id: int, credentials: HTTPBasicCredentials=Depends(user_authenticate), db: Session=Depends(get_db)):
    return get_book_or_404(id, db)

@router.put("/update/{id}", response_model=SchemaBookResponse)
def update_book(id: int, update_book: UpdateSchemaBook, credentials: HTTPBasicCredentials=Depends(user_authenticate), db: Session=Depends(get_db)):
    book = get_book_or_404(id, db)

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
def delete_book(id: int, credential: HTTPBasicCredentials=Depends(user_authenticate), db: Session=Depends(get_db)):
    book = get_book_or_404(id, db)

    if book.is_example:
        raise HTTPException(status_code=403, detail=EXAMPLE_LOCKED)

    db.delete(book)
    db.commit()
