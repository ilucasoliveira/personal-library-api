import os
from fastapi import FastAPI, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session
from .config import DEMO_MODE
from .database import get_db
from .routers import books, profile

allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

description = "Your personal library."
if DEMO_MODE:
    description += (
        " **Demo mode:** example books are read-only, books added by visitors are"
        " removed automatically and the profile cannot be changed."
    )

app = FastAPI(
    title="My Own BookShelf",
    description=description,
    version="1.1.0",
    contact={
        "name": "Lucas de Oliveira",
        "email": "lucasdeoliveira973@gmail.com",
    },
)


# O ping também toca o banco: assim o monitor de uptime mantém a API acordada
# e evita que o projeto gratuito do Supabase seja pausado por inatividade.
@app.get("/ping")
def ping(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok", "demo": DEMO_MODE}


@app.head("/ping")
def ping_head(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return Response()


app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(books.router, tags=["Books' Routes"])

app.include_router(profile.router, tags=["Profile's Routes"])
