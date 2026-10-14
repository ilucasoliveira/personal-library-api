"""A conta de quem está logado: dados, preferências (tema, cor, idioma), senha, foto e exclusão."""
import logging
import os
import uuid

import httpx
from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from ..auth import create_access_token, get_current_user, hash_password, verify_password
from ..database import get_db
from ..errors import ApiError
from ..models import Book, User
from ..schemas import AccountDelete, PasswordChange, TokenResponse, UserResponse, UserSettings

router = APIRouter(prefix="/me")
logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
BUCKET_NAME = "profile-photos"

VISITOR_LOCKED = "The visitor account cannot be changed."
WRONG_PASSWORD = "Incorrect password."

MAX_PHOTO_BYTES = 2 * 1024 * 1024
PHOTO_TYPES = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp", "image/gif": "gif"}


def storage_headers(extra: dict | None = None) -> dict:
    """Cabeçalhos para o Storage do Supabase.

    A chave nova (sb_secret_...) não é um JWT: vai só no "apikey". Se ela for também em
    "Authorization: Bearer", o Supabase tenta ler como JWT e recusa ("Invalid Compact JWS").
    A chave antiga (service_role, um JWT que começa com "eyJ") vai nos dois, como antes.
    """
    headers = {"apikey": SUPABASE_SERVICE_KEY}
    if SUPABASE_SERVICE_KEY and SUPABASE_SERVICE_KEY.startswith("eyJ"):
        headers["Authorization"] = f"Bearer {SUPABASE_SERVICE_KEY}"
    return {**headers, **(extra or {})}


def remove_photo(photo_url: str | None):
    """Apaga do Storage uma foto enviada por aqui. Melhor esforço: se falhar, só fica um arquivo órfão."""
    prefix = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/"
    if not photo_url or not SUPABASE_URL or not photo_url.startswith(prefix):
        return
    path = photo_url[len(prefix):]
    try:
        httpx.delete(
            f"{SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}/{path}",
            headers=storage_headers(),
            timeout=10,
        )
    except httpx.HTTPError:
        pass


def block_visitor(user: User):
    if user.is_visitor:
        raise ApiError(403, "visitor_locked", VISITOR_LOCKED)


@router.get("", response_model=UserResponse)
def read_me(user: User = Depends(get_current_user)):
    return user


@router.put("", response_model=UserResponse)
def update_me(data: UserSettings, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    block_visitor(user)

    # só altera o que veio no corpo; "accent": null volta para a cor do tema
    for field, value in data.model_dump(exclude_unset=True).items():
        if field == "name":
            value = (value or "").strip()
            if not value:
                raise ApiError(422, "name_required", "Name cannot be empty.")
        elif field in ("theme", "language") and value is None:
            continue
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user


@router.put("/password", response_model=TokenResponse)
def change_password(data: PasswordChange, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Troca a senha, derruba todas as sessões abertas e devolve um token novo para esta."""
    block_visitor(user)
    if not verify_password(data.current_password, user.password_hash):
        raise ApiError(400, "wrong_password", WRONG_PASSWORD)

    user.password_hash = hash_password(data.new_password)
    user.token_version = (user.token_version or 0) + 1
    db.commit()
    db.refresh(user)
    return TokenResponse(access_token=create_access_token(user), user=user)


@router.post("/photo", response_model=UserResponse)
async def upload_photo(
    file: UploadFile = File(...), user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    block_visitor(user)

    extension = PHOTO_TYPES.get(file.content_type or "")
    if extension is None:
        raise ApiError(415, "photo_type", "Photo must be JPG, PNG, WEBP or GIF.")

    content = await file.read(MAX_PHOTO_BYTES + 1)
    if len(content) > MAX_PHOTO_BYTES:
        raise ApiError(413, "photo_size", "Photo must be at most 2 MB.")

    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise ApiError(503, "photo_unavailable", "Photo upload is not configured.")

    # uma pasta por usuário no bucket
    file_name = f"user-{user.id}/{uuid.uuid4()}.{extension}"
    headers = storage_headers({"Content-Type": file.content_type})
    upload_failed = ApiError(502, "photo_upload_failed", "Could not upload the photo. Try again later.")
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                f"{SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}/{file_name}", headers=headers, content=content
            )
    except httpx.HTTPError as exc:
        # Storage fora do ar ou SUPABASE_URL apontando para um projeto que não existe
        logger.warning("Storage inacessível ao enviar foto: %r", exc)
        raise upload_failed from exc

    if response.status_code not in (200, 201):
        # o motivo vai para o log do servidor (ex.: bucket inexistente, chave errada), não para o usuário
        logger.warning("Storage recusou a foto: %s %s", response.status_code, response.text[:300])
        raise upload_failed

    old_photo = user.photo_url
    user.photo_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{file_name}"
    db.commit()
    remove_photo(old_photo)
    db.refresh(user)
    return user


@router.delete("/photo", response_model=UserResponse)
def delete_photo(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Tira a foto do perfil (volta para a inicial do nome) e apaga o arquivo do Storage."""
    block_visitor(user)
    photo = user.photo_url
    user.photo_url = None
    db.commit()
    remove_photo(photo)
    db.refresh(user)
    return user


@router.delete("", status_code=204)
def delete_me(data: AccountDelete, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Apaga a conta e todos os livros dela. Pede a senha de novo para confirmar."""
    block_visitor(user)
    if not verify_password(data.password, user.password_hash):
        raise ApiError(400, "wrong_password", WRONG_PASSWORD)

    photo = user.photo_url
    db.query(Book).filter(Book.user_id == user.id).delete(synchronize_session=False)
    db.delete(user)
    db.commit()
    remove_photo(photo)
