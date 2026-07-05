from pydantic import BaseModel, Field
from typing import Optional

class SchemaBook(BaseModel):
    title: str=Field(min_length=1, max_length=150, description="Título do livro")
    cover_url: Optional[str] = Field(default=None, description="URL da capa do livro")
    author: str=Field(min_length=1, max_length=100, description="Nome do autor")
    gender: str=Field(min_length=1, max_length=50, description="Tipo de gênero")
    synopsis: Optional[str]=Field(default=None, max_length=2000, description="Descreva a sinopse do livro")
    grade: Optional[int]=Field(default=None,ge=1,le=5, description="Nota para o livro")
    comment: Optional[str]=Field(default=None,max_length=300, description="Comentário para o livro")
    reading_status: Optional[str] = Field(default="toRead", description="Status de leitura: toRead, reading ou read")
    favorite: Optional[bool]=Field(default=False, description="Adiciona a lista de favoritos")

class SchemaBookResponse(SchemaBook):
    id: int

class UpdateSchemaBook(SchemaBook):
    title: Optional[str]=Field(default=None, min_length=1, max_length=150)
    cover_url: Optional[str] = Field(default=None)
    author: Optional[str]=Field(default=None,min_length=1, max_length=100)
    gender: Optional[str]=Field(default=None, min_length=1, max_length=50)
    reading_status: Optional[str] = Field(default=None, description="Status de leitura: toRead, reading ou read")
    favorite: Optional[bool]=Field(default=None)

class SchemaProfile(BaseModel):
    photo_url: Optional[str] = None

class SchemaProfileResponse(SchemaProfile):
    id: int