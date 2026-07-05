# 📚 Personal Library API

A REST API for managing a personal digital library — built as a gift for someone special.

This project started as a way to give my boyfriend Arthur ("Thur") his own space to track every book he reads: what he's currently reading, what he wants to read next, and his personal ratings and thoughts on each one. What began as a personal gift grew into a full-stack application with a production-ready backend, real deployment, and a design system built entirely from scratch.

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
- Lightweight `/ping` health-check endpoint for uptime monitoring

---

## 🏗 Project Structure

```
src/back_end_library/
├── main.py            # FastAPI app instance, middleware, router registration
├── database.py         # SQLAlchemy engine/session setup (NullPool for pooled connections)
├── models.py           # ORM models (Book, Profile)
├── schemas.py          # Pydantic schemas for validation/serialization
├── auth.py             # HTTP Basic Auth dependency
├── routers/
│   ├── books.py         # Book CRUD endpoints
│   └── profile.py       # Profile + photo upload endpoints (Supabase Storage)
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
# then fill in DATABASE_URL, MEU_USUARIO, MINHA_SENHA, ALLOWED_ORIGINS,
# SUPABASE_URL, SUPABASE_SERVICE_KEY

# Create database tables
poetry run python src/back_end_library/create_tables.py

# Run the development server
poetry run fastapi dev src/back_end_library/main.py
```

---

## ☁️ Deployment

This API runs in production on **[Render](https://render.com)** (free tier web service), connected to a **[Supabase](https://supabase.com)** PostgreSQL database and Supabase Storage for file uploads. Uptime is kept alive via a scheduled ping from **[UptimeRobot](https://uptimerobot.com)** hitting the `/ping` endpoint every 5 minutes.

**Live API docs:** [personal-library-api-gnvq.onrender.com/docs](https://personal-library-api-gnvq.onrender.com/docs)

> Note: interactive docs are public, but every endpoint requires valid credentials to return data — this API serves a private personal library.

---

## 📄 License

This project is licensed under the MIT License.