import os
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from .routers import books, profile

allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

app = FastAPI(
    title="Thur's Library",
    description="A personal library for a special person.",
    version="1.0.0",
    contact={
        "name":"Lucas de Oliveira",
        "email":"lucasdeoliveira973@gmail.com"
    }
)

@app.get("/ping")
def ping():
    return {"status": "ok"}

@app.head("/ping")
def ping_head():
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