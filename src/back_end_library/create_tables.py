"""Cria as tabelas no banco do DATABASE_URL.

Uso: poetry run python -m back_end_library.create_tables
"""
from .database import engine
from .models import Base

if __name__ == "__main__":
    Base.metadata.create_all(engine)
    print("Tabelas criadas.")
