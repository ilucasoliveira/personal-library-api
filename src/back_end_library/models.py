from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(60))
    photo_url: Mapped[Optional[str]] = mapped_column(String(1000))
    theme: Mapped[str] = mapped_column(String(20), default="twilight")
    accent: Mapped[Optional[str]] = mapped_column(String(7))
    language: Mapped[str] = mapped_column(String(5), default="pt")
    # conta compartilhada da demo: livros de exemplo e configurações bloqueadas
    is_visitor: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Book(Base):
    __tablename__ = "livros"

    id: Mapped[int] = mapped_column(primary_key=True)
    # nulo só em livros de antes das contas; o comando manage claim-orphans atribui um dono
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
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
    is_example: Mapped[bool] = mapped_column(Boolean, default=False)
