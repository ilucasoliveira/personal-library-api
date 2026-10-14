from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

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
    grade: Optional[float] = Field(
        default=None, ge=0.25, le=5, multiple_of=0.25, description="Nota de 0.25 a 5, de 0.25 em 0.25"
    )
    comment: Optional[str] = Field(default=None, max_length=300, description="Comentário para o livro")
    reading_status: ReadingStatus = Field(default="toRead", description="Status de leitura: toRead, reading ou read")
    favorite: Optional[bool] = Field(default=False, description="Adiciona a lista de favoritos")

    @field_validator("cover_url", "synopsis", "comment", mode="before")
    @classmethod
    def blank_is_none(cls, value):
        # texto vazio ou só espaços vale como "sem valor"
        if isinstance(value, str) and not value.strip():
            return None
        return value


class SchemaBookResponse(SchemaBook):
    id: int
    add_date: Optional[date] = None
    finished_date: Optional[date] = None
    is_example: bool = False


class UpdateSchemaBook(SchemaBook):
    title: Optional[str] = Field(default=None, min_length=1, max_length=150)
    cover_url: Optional[str] = Field(default=None, max_length=1000)
    author: Optional[str] = Field(default=None, min_length=1, max_length=100)
    gender: Optional[str] = Field(default=None, min_length=1, max_length=50)
    reading_status: Optional[ReadingStatus] = Field(default=None, description="Status de leitura: toRead, reading ou read")
    favorite: Optional[bool] = Field(default=None)

    @model_validator(mode="after")
    def required_fields_not_null(self):
        # estes campos podem ficar de fora do corpo, mas não podem ser apagados com null
        for field in ("title", "author", "gender", "reading_status", "favorite"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        return self


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
    created_at: Optional[datetime] = None


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
