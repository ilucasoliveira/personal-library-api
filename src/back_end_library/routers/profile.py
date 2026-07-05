import os
import uuid
from fastapi import APIRouter, Depends, UploadFile, File
from fastapi.security import HTTPBasicCredentials
from sqlalchemy.orm import Session
from ..models import Profile
from ..schemas import SchemaProfile, SchemaProfileResponse
from ..database import get_db
from ..auth import user_authenticate

router = APIRouter()

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
    caminho = os.path.join("src/back_end_library/uploads", nome_arquivo)
    
    with open(caminho, "wb") as f:
        conteudo = await file.read()
        f.write(conteudo)
    
    profile = db.query(Profile).filter(Profile.id == 1). first()
    profile.photo_url = f"http://localhost:8000/uploads/{nome_arquivo}"
    db.commit()
    db.refresh(profile)
    
    return profile