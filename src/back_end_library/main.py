from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import books, profile
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="Thur's Library",
    description="A personal library for a special person.",
    version="1.0.0",
    contact={
        "name":"Lucas de Oliveira",
        "email":"lucasdeoliveira973@gmail.com"
    }
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(books.router, tags=["Books' Routes"])

app.include_router(profile.router, tags=["Profile's Routes"])

app.mount("/uploads", StaticFiles(directory="src/back_end_library/uploads"), name="uploads")