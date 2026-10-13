# 📚 Personal Library API (My Own BookShelf)

A REST API for managing a personal digital library. Track what you're reading, what you want to read next, and your ratings and notes on every book.

**Try the live demo:** see [Live demo](#-live-demo) below. Public credentials, sample books, and your own books to play with.

Started as a small side project and grew into a full-stack application with a production deployment, persistent file storage, and a design system built from scratch on the frontend side.

---

## 🛠 Tech Stack

![Python](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.139-009688?logo=fastapi&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?logo=sqlalchemy&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supabase-4169E1?logo=postgresql&logoColor=white)
![Poetry](https://img.shields.io/badge/Poetry-dependency%20management-60A5FA?logo=poetry&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)

- **FastAPI** — async-ready Python web framework with automatic OpenAPI docs
- **SQLAlchemy 2.0** — using the modern `Mapped`/`mapped_column` declarative style
- **Pydantic v2** — request/response validation and serialization
- **PostgreSQL** (hosted on Supabase) — relational data storage
- **Supabase Storage** — persistent file storage for profile photo uploads
- **HTTP Basic Auth** — endpoint protection
- **Poetry** — dependency and environment management
- **httpx** — outbound requests to Supabase Storage's REST API
- **Alembic** — database migrations
- **pytest** — automated tests for the demo rules, running against a temporary SQLite database

---

## ✨ Features

- Full CRUD for books: create, read, update, delete
- Reading status tracking (`to read`, `reading`, `read`)
- 5-star rating system and personal comments per book
- Favorite marking
- Profile endpoint with photo upload, stored persistently via Supabase Storage
- Integration-ready with an external book search (Google Books API) on the frontend
- Environment-based configuration (no secrets committed to source control)
- Configurable CORS via environment variable, supporting multiple deployed origins
- `/ping` health-check endpoint for uptime monitoring, which also touches the database so the free-tier database never goes idle
- **Demo mode** (`DEMO_MODE=true`): the same codebase powers a public demo, with read-only example books, automatic cleanup of visitor books and a locked profile

---

## 🏗 Project Structure

```
src/back_end_library/
├── main.py            # FastAPI app instance, middleware, router registration
├── database.py         # SQLAlchemy engine/session setup (NullPool for pooled connections)
├── models.py           # ORM models (Book, Profile)
├── schemas.py          # Pydantic schemas for validation/serialization
├── auth.py             # HTTP Basic Auth dependency
├── config.py           # Environment settings (demo mode and its limits)
├── seed_demo.py        # Resets the demo database with sample books
├── create_tables.py    # Creates the tables on a fresh database
├── routers/
│   ├── books.py         # Book CRUD endpoints
│   └── profile.py       # Profile + photo upload endpoints (Supabase Storage)
alembic/                # Migrations
tests/                  # pytest suite (demo rules, auth, profile)
```

---

## 🔌 API Endpoints

| Method | Endpoint             | Description                     |
|--------|-----------------------|----------------------------------|
| POST   | `/create`             | Add a new book                  |
| GET    | `/books`              | List all books                  |
| GET    | `/books/{id}`         | Get a single book                |
| PUT    | `/update/{id}`        | Update a book (partial updates)  |
| DELETE | `/delete/{id}`        | Delete a book                    |
| GET    | `/profile`            | Get profile data                 |
| PUT    | `/profile`            | Update profile data              |
| POST   | `/profile/upload`     | Upload a profile photo           |
| GET/HEAD | `/ping`              | Health check (used for uptime monitoring) |

All endpoints (except `/ping`) require HTTP Basic Auth. Interactive docs available at `/docs` (Swagger UI) once running.

---

## 🎭 Live demo

The demo runs this same code with `DEMO_MODE=true`, on its own database, so visitors never touch a real library.

| | |
|---|---|
| Username | `visitante` |
| Password | `biblioteca2026` |

Rules in demo mode, enforced by the API (not just hidden in the UI):

- **Example books are read-only**: updating or deleting one returns `403 Forbidden`
- **Visitor books are temporary**: anything a visitor adds is removed after `DEMO_VISITOR_BOOK_DAYS` (default 1 day), and only the latest `DEMO_MAX_VISITOR_BOOKS` (default 30) are kept
- **The profile is locked**: changing the photo returns `403 Forbidden`

To reset the demo database to the sample books:

```bash
# .env must point to the DEMO database and have DEMO_MODE=true (the script refuses to run otherwise)
poetry run python -m back_end_library.seed_demo
```

Covers come from Google Books (set `GOOGLE_BOOKS_KEY` to avoid the anonymous quota) with Open Library as a fallback.

---

## 🚀 Running Locally

**Requirements:** Python 3.14+, [Poetry](https://python-poetry.org/), a PostgreSQL database.

```bash
# Clone the repository
git clone https://github.com/ilucasoliveira/personal-library-api.git
cd personal-library-api

# Install dependencies
poetry install

# Set up environment variables
cp .env.example .env
# then fill in DATABASE_URL, APP_USERNAME, APP_PASSWORD, ALLOWED_ORIGINS,
# SUPABASE_URL, SUPABASE_SERVICE_KEY (and DEMO_MODE for a demo deployment)

# Create database tables and mark the migrations as applied
poetry run python -m back_end_library.create_tables
poetry run alembic stamp head

# Run the development server
poetry run fastapi dev src/back_end_library/main.py

# Run the tests
poetry run pytest
```

---

## ☁️ Deployment

This API runs in production on **[Render](https://render.com)** (free tier web service), connected to a **[Supabase](https://supabase.com)** PostgreSQL database and Supabase Storage for file uploads. Uptime is kept alive via a scheduled ping from **[UptimeRobot](https://uptimerobot.com)** hitting the `/ping` endpoint every 5 minutes.

**Live API docs:** [personal-library-api-gnvq.onrender.com/docs](https://personal-library-api-gnvq.onrender.com/docs)

> Note: interactive docs are public, but every endpoint requires valid credentials to return data. The production instance serves a private personal library; use the [live demo](#-live-demo) to try the API.

---

## 📄 License

This project is licensed under the MIT License.
