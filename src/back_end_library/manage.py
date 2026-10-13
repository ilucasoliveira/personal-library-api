"""Comandos de administração.

Criar uma conta (a senha é pedida no terminal, não fica no histórico):
    poetry run python -m back_end_library.manage create-user --email voce@exemplo.com --name "Seu nome"

Na biblioteca que já existia antes das contas, use --claim-orphans para que a conta nova
receba todos os livros sem dono e a foto do perfil antigo:
    poetry run python -m back_end_library.manage create-user --email ... --name ... --claim-orphans

Definir uma senha nova para quem esqueceu (o app não tem recuperação por email):
    poetry run python -m back_end_library.manage reset-password --email alguem@exemplo.com
"""
import argparse
import getpass
import sys

from sqlalchemy import inspect, text

from .auth import hash_password
from .database import SessionLocal, engine
from .models import Book, User


def read_password() -> str:
    while True:
        password = getpass.getpass("Senha (mínimo 8 caracteres): ")
        if len(password) < 8:
            print("A senha precisa ter pelo menos 8 caracteres.")
            continue
        if len(password.encode("utf-8")) > 72:
            print("A senha pode ter no máximo 72 bytes.")
            continue
        if password != getpass.getpass("Repita a senha: "):
            print("As senhas não conferem.")
            continue
        return password


def old_profile_photo(db) -> str | None:
    """Foto do perfil único de antes das contas (tabela profile), se existir."""
    if not inspect(engine).has_table("profile"):
        return None
    return db.execute(text("SELECT photo_url FROM profile WHERE id = 1")).scalar()


def create_user(email: str, name: str, claim_orphans: bool, language: str):
    if not inspect(engine).has_table("users"):
        sys.exit("A tabela users não existe. Rode antes: poetry run alembic upgrade head")

    email = email.strip().lower()
    db = SessionLocal()
    try:
        if db.query(User).filter(User.email == email).first():
            sys.exit(f"Já existe uma conta com o email {email}.")

        user = User(email=email, name=name.strip(), password_hash=hash_password(read_password()), language=language)
        db.add(user)
        db.flush()

        if claim_orphans:
            claimed = (
                db.query(Book).filter(Book.user_id.is_(None)).update({Book.user_id: user.id}, synchronize_session=False)
            )
            user.photo_url = old_profile_photo(db)
            print(f"{claimed} livro(s) sem dono agora pertencem a {email}.")

        db.commit()
        print(f"Conta criada: {email} (id {user.id}).")
    finally:
        db.close()


def reset_password(email: str):
    email = email.strip().lower()
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email, User.is_visitor.is_(False)).first()
        if user is None:
            sys.exit(f"Nenhuma conta com o email {email}.")
        user.password_hash = hash_password(read_password())
        # derruba as sessões abertas com a senha antiga
        user.token_version = (user.token_version or 0) + 1
        db.commit()
        print(f"Senha de {email} alterada.")
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Administração do My Own BookShelf")
    commands = parser.add_subparsers(dest="command", required=True)

    create = commands.add_parser("create-user", help="cria uma conta")
    create.add_argument("--email", required=True)
    create.add_argument("--name", required=True)
    create.add_argument("--language", choices=["pt", "en"], default="pt")
    create.add_argument("--claim-orphans", action="store_true", help="assume os livros sem dono")

    reset = commands.add_parser("reset-password", help="define uma senha nova para uma conta")
    reset.add_argument("--email", required=True)

    args = parser.parse_args()
    if args.command == "create-user":
        create_user(args.email, args.name, args.claim_orphans, args.language)
    elif args.command == "reset-password":
        reset_password(args.email)


if __name__ == "__main__":
    main()
