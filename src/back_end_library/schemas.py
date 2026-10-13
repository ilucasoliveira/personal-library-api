from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

Theme = Literal["twilight", "paper", "sepia", "forest"]
ReadingStatus = Literal["toRead", "reading", "read"]
Language = Literal["pt", "en"]
HEX_COLOR = r"^#[0-9a-fA-F]{6}$"


# ---------- livros ----------

class SchemaBook(BaseModel):
    title: str = Field(min_length=1, max_length=150, description="Título do livro")
    cover_url: Optional[str] = Field(default=None, max_length=1000, description="URL da capa do livro")
    author: str = Field(min_length=1, max_length=100, description="Nome do autor")
    gender: str = Field(min_length=1, max_length=50, description="Tipo de gênero")
    synopsis: Optional[str] = Field(default=None, max_length=2000, description="Descreva a sinopse do livro")
    grade: Optional[int] = Field(default=None, ge=1, le=5, description="Nota para o livro")
    comment: Optional[str] = Field(default=None, max_length=300, description="Comentário para o livro")
    reading_status: ReadingStatus = Field(default="toRead", description="Status de leitura: toRead, reading ou read")
    favorite: Optional[bool] = Field(default=False, description="Adiciona a lista de favoritos")


class SchemaBookResponse(SchemaBook):
    id: int
    finished_date: Optional[date] = None
    is_example: bool = False


class UpdateSchemaBook(SchemaBook):
    title: Optional[str] = Field(default=None, min_length=1, max_length=150)
    cover_url: Optional[str] = Field(default=None, max_length=1000)
    author: Optional[str] = Field(default=None, min_length=1, max_length=100)
    gender: Optional[str] = Field(default=None, min_length=1, max_length=50)
    reading_status: Optional[ReadingStatus] = Field(default=None, description="Status de leitura: toRead, reading ou read")
    favorite: Optional[bool] = Field(default=None)


# ---------- usuários ----------

def _check_password(value: str) -> str:
    # o bcrypt só considera os primeiros 72 bytes da senha
    if len(value.encode("utf-8")) > 72:
        raise ValueError("Password must be at most 72 bytes.")
    return value


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    email: EmailStr
    password: str = Field(min_length=8)
    language: Language = "pt"

    _password = field_validator("password")(_check_password)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Name cannot be empty.")
        return value


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    photo_url: Optional[str] = None
    theme: str
    accent: Optional[str] = None
    language: str
    is_visitor: bool


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class UserSettings(BaseModel):
    """Campos opcionais: só o que vier no corpo é alterado. accent: null volta à cor do tema."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=60)
    theme: Optional[Theme] = None
    accent: Optional[str] = Field(default=None, pattern=HEX_COLOR)
    language: Optional[Language] = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)

    _password = field_validator("new_password")(_check_password)


class AccountDelete(BaseModel):
    password: str
