"""Senhas (bcrypt) e login por token (JWT).

Fluxo: o usuário entra com email e senha em /auth/login e recebe um token.
O front manda esse token no cabeçalho Authorization: Bearer <token> em toda requisição.
"""
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .config import BCRYPT_ROUNDS, JWT_EXPIRE_DAYS, JWT_SECRET
from .database import get_db
from .models import User

ALGORITHM = "HS256"

# tokenUrl faz o botão "Authorize" do /docs funcionar com email e senha
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

INVALID_TOKEN = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid or expired session.",
    headers={"WWW-Authenticate": "Bearer"},
)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(BCRYPT_ROUNDS)).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        # hash inválido (ex.: a conta de visitante, que não tem senha)
        return False


# usado quando o email não existe: o login leva o mesmo tempo e não revela quais emails têm conta
DUMMY_HASH = hash_password("not-a-real-password")


def create_access_token(user: User) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),
        # versão da senha: trocar a senha invalida os tokens antigos
        "ver": user.token_version or 0,
        "iat": now,
        "exp": now + timedelta(days=JWT_EXPIRE_DAYS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        user_id = int(payload["sub"])
        version = int(payload.get("ver", 0))
    except (jwt.PyJWTError, KeyError, ValueError, TypeError):
        raise INVALID_TOKEN

    user = db.get(User, user_id)
    if user is None or version != (user.token_version or 0):
        # conta excluída, ou senha trocada depois que o token foi emitido
        raise INVALID_TOKEN
    return user
