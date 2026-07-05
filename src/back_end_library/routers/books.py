from ..schemas import SchemaBook, SchemaBookResponse, UpdateSchemaBook
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBasicCredentials
from ..auth import user_authenticate
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Book

router = APIRouter()

@router.post("/create", status_code=201, response_model=SchemaBookResponse)
def create_book(book: SchemaBook, credentials: HTTPBasicCredentials=Depends(user_authenticate), db: Session=Depends(get_db)):
    new_book = Book(**book.model_dump())
    db.add(new_book)
    db.commit()
    db.refresh(new_book)
    return new_book

@router.get("/books", response_model=list[SchemaBookResponse])
def read_books(credentials: HTTPBasicCredentials=Depends(user_authenticate), db: Session=Depends(get_db)):
    books = db.query(Book).all()
    return books

@router.get("/books/{id}", response_model=SchemaBookResponse)
def read_one_book(id: int, credentials: HTTPBasicCredentials=Depends(user_authenticate), db: Session=Depends(get_db)):
    book = db.query(Book).filter(Book.id == id).first()
    
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    
    return book

@router.put("/update/{id}", response_model=SchemaBookResponse)
def update_book(id: int, update_book: UpdateSchemaBook, credentials: HTTPBasicCredentials=Depends(user_authenticate), db: Session=Depends(get_db)):
    book = db.query(Book).filter(Book.id == id).first()
    
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    
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
    if update_book.reading_status is not None:
        book.reading_status = update_book.reading_status
    if update_book.favorite is not None:
        book.favorite = update_book.favorite
    if update_book.cover_url is not None:
        book.cover_url = update_book.cover_url
    
    db.commit()
    db.refresh(book)
    return book

@router.delete("/delete/{id}", status_code=204)
def delete_book(id: int, credential: HTTPBasicCredentials=Depends(user_authenticate), db: Session=Depends(get_db)):
    book = db.query(Book).filter(Book.id == id).first()
    
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    
    db.delete(book)
    db.commit()