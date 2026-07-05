from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, Boolean, Date
from typing import Optional
from datetime import date

class Base(DeclarativeBase):
    pass

class Book(Base):
    __tablename__="livros"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(150))
    cover_url: Mapped[Optional[str]] = mapped_column(String(1000))
    author: Mapped[str] = mapped_column(String(100))
    gender: Mapped[str] = mapped_column(String(50))
    synopsis: Mapped[Optional[str]] = mapped_column(String(2000))
    grade: Mapped[Optional[int]] = mapped_column(Integer)
    comment: Mapped[Optional[str]] = mapped_column(String(300))
    reading_status: Mapped[str] = mapped_column(String(20), default="toRead")
    favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    add_date: Mapped[date] = mapped_column(Date, default=date.today)
    finished_date: Mapped[Optional[date]] = mapped_column(Date)

class Profile(Base):
    __tablename__="profile"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    photo_url: Mapped[Optional[str]] = mapped_column(String(1000))
