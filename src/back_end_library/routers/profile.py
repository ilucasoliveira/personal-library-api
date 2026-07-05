import os
import uuid
import httpx
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.security import HTTPBasicCredentials
from sqlalchemy.orm import Session
from ..models import Profile
from ..schemas import SchemaProfile, SchemaProfileResponse
from ..database import get_db
from ..auth import user_authenticate

router = APIRouter()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
BUCKET_NAME = "profile-photos"

@router.get("/profile", response_model=SchemaProfileResponse)
def read_profile(crendentials: HTTPBasicCredentials=Depends(user_authenticate), db: Session=Depends(get_db)):
    profile = db.query(Profile).filter(Profile.id == 1).first()
    return profile

@router.put("/profile", response_model=SchemaProfileResponse)
def update_profile(data: SchemaProfile, credentials: HTTPBasicCredentials=Depends(user_authenticate), db: Session=Depends(get_db)):
    profile = db.query(Profile).filter(Profile.id == 1).first()

    if data.photo_url is not None:
        profile.photo_url = data.photo_url

    db.commit()
    db.refresh(profile)
    return profile

@router.post("/profile/upload")
async def upload_photo(file: UploadFile = File(...), credentials: HTTPBasicCredentials=Depends(user_authenticate), db: Session=Depends(get_db)):
    extensao = file.filename.split(".")[-1]
    nome_arquivo = f"{uuid.uuid4()}.{extensao}"
    conteudo = await file.read()

    upload_url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}/{nome_arquivo}"
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": file.content_type or "application/octet-stream",
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(upload_url, headers=headers, content=conteudo)

    if response.status_code not in (200, 201):
        raise HTTPException(status_code=502, detail=f"Erro ao enviar foto para o Supabase Storage: {response.text}")

    public_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{nome_arquivo}"

    profile = db.query(Profile).filter(Profile.id == 1).first()
    profile.photo_url = public_url
    db.commit()
    db.refresh(profile)

    return profile