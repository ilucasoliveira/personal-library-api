import os
from fastapi import FastAPI, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session
from .config import ALLOW_SIGNUP, DEMO_MODE, JWT_SECRET
from .database import get_db
from .errors import install_error_handlers
from .routers import auth, books, me

# sem o segredo ninguém consegue entrar; melhor a API nem subir
if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET is not set. Define it in the .env or in the server environment.")

allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

description = (
    "Your personal library. Each account has its own shelf. Log in with **Authorize**"
    " (email in the username field) or create an account at `/auth/register`."
)
if DEMO_MODE:
    description += (
        " **Demo mode:** `/auth/visitor` logs into a shared visitor account whose example books"
        " are read-only and whose added books are removed automatically."
    )

app = FastAPI(
    title="My Own BookShelf",
    description=description,
    version="2.0.0",
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
    return {"status": "ok", "demo": DEMO_MODE, "signup": ALLOW_SIGNUP}


@app.head("/ping")
def ping_head(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return Response()


app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

install_error_handlers(app)

app.include_router(auth.router, tags=["Auth"])
app.include_router(me.router, tags=["Account"])
app.include_router(books.router, tags=["Books' Routes"])
