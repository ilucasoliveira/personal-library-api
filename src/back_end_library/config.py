import os
from dotenv import load_dotenv

load_dotenv()


def _flag(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in ("1", "true", "yes", "on")


# Modo demonstração: liga a conta de visitante (livros de exemplo só leitura,
# limpeza automática dos livros que visitantes adicionam e configurações bloqueadas).
DEMO_MODE = _flag("DEMO_MODE")

# Quantos livros de visitantes a demo guarda ao mesmo tempo (os mais antigos saem primeiro).
DEMO_MAX_VISITOR_BOOKS = int(os.getenv("DEMO_MAX_VISITOR_BOOKS", "30"))

# Por quantos dias um livro adicionado por visitante fica na demo.
DEMO_VISITOR_BOOK_DAYS = int(os.getenv("DEMO_VISITOR_BOOK_DAYS", "1"))

# Cadastro de novos usuários. Desligado por padrão: só o deploy público liga.
ALLOW_SIGNUP = _flag("ALLOW_SIGNUP")

# Limite de livros por usuário (proteção contra abuso no deploy público).
MAX_BOOKS_PER_USER = int(os.getenv("MAX_BOOKS_PER_USER", "2000"))

# Token de login (JWT): segredo obrigatório e validade em dias.
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_EXPIRE_DAYS = int(os.getenv("JWT_EXPIRE_DAYS", "7"))

# Custo do hash de senha (bcrypt). 12 é o recomendado; os testes usam menos para rodar rápido.
BCRYPT_ROUNDS = int(os.getenv("BCRYPT_ROUNDS", "12"))

# Temas que o front oferece; a API só aceita estes nomes.
THEMES = ("twilight", "paper", "sepia", "forest")
LANGUAGES = ("pt", "en")
