import os
from dotenv import load_dotenv

load_dotenv()


def _flag(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in ("1", "true", "yes", "on")


# Modo demonstração: liga as regras da demo pública (livros de exemplo só leitura,
# limpeza automática dos livros de visitantes e perfil bloqueado).
DEMO_MODE = _flag("DEMO_MODE")

# Quantos livros de visitantes a demo guarda ao mesmo tempo (os mais antigos saem primeiro).
DEMO_MAX_VISITOR_BOOKS = int(os.getenv("DEMO_MAX_VISITOR_BOOKS", "30"))

# Por quantos dias um livro adicionado por visitante fica na demo.
DEMO_VISITOR_BOOK_DAYS = int(os.getenv("DEMO_VISITOR_BOOK_DAYS", "1"))
