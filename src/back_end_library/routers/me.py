"""A conta de quem está logado: dados, preferências (tema, cor, idioma), senha, foto e exclusão."""
import os
import uuid

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..auth import create_access_token, get_current_user, hash_password, verify_password
from ..database import get_db
from ..models import Book, User
from ..schemas import AccountDelete, PasswordChange, TokenResponse, UserResponse, UserSettings

router = APIRouter(prefix="/me")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
BUCKET_NAME = "profile-photos"

VISITOR_LOCKED = "The visitor account cannot be changed."
WRONG_PASSWORD = "Incorrect password."

MAX_PHOTO_BYTES = 2 * 1024 * 1024
PHOTO_TYPES = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp", "image/gif": "gif"}


def remove_photo(photo_url: str | None):
    """Apaga do Storage uma foto enviada por aqui. Melhor esforço: se falhar, só fica um arquivo órfão."""
    prefix = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/"
    if not photo_url or not SUPABASE_URL or not photo_url.startswith(prefix):
        return
    path = photo_url[len(prefix):]
    try:
        httpx.delete(
            f"{SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}/{path}",
            headers={"apikey": SUPABASE_SERVICE_KEY, "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}"},
            timeout=10,
        )
    except httpx.HTTPError:
        pass


def block_visitor(user: User):
    if user.is_visitor:
        raise HTTPException(status_code=403, detail=VISITOR_LOCKED)


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
                raise HTTPException(status_code=422, detail="Name cannot be empty.")
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
        raise HTTPException(status_code=400, detail=WRONG_PASSWORD)

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
        raise HTTPException(status_code=415, detail="Photo must be JPG, PNG, WEBP or GIF.")

    content = await file.read(MAX_PHOTO_BYTES + 1)
    if len(content) > MAX_PHOTO_BYTES:
        raise HTTPException(status_code=413, detail="Photo must be at most 2 MB.")

    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise HTTPException(status_code=503, detail="Photo upload is not configured.")

    # uma pasta por usuário no bucket
    file_name = f"user-{user.id}/{uuid.uuid4()}.{extension}"
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": file.content_type,
    }
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(
            f"{SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}/{file_name}", headers=headers, content=content
        )

    if response.status_code not in (200, 201):
        raise HTTPException(status_code=502, detail="Could not upload the photo. Try again later.")

    old_photo = user.photo_url
    user.photo_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{file_name}"
    db.commit()
    remove_photo(old_photo)
    db.refresh(user)
    return user


@router.delete("", status_code=204)
def delete_me(data: AccountDelete, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Apaga a conta e todos os livros dela. Pede a senha de novo para confirmar."""
    block_visitor(user)
    if not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=400, detail=WRONG_PASSWORD)

    photo = user.photo_url
    db.query(Book).filter(Book.user_id == user.id).delete(synchronize_session=False)
    db.delete(user)
    db.commit()
    remove_photo(photo)
