# 📚 Personal Library API (My Own BookShelf)

A REST API for a personal digital library with user accounts. Each person gets their own shelf: what they're reading, what they want to read next, ratings, notes, and their own theme and language.

**Try it:** [my-own-bookshelf.vercel.app](https://my-own-bookshelf.vercel.app). Create an account, or click **"Continue as visitor"** ("Entrar como visitante" in Portuguese) to explore a sample shelf. Details in [Live app](#-live-app) below.

Started as a small side project and grew into a full-stack application with a production deployment, persistent file storage, and a design system built from scratch on the frontend side.

---

## 🛠 Tech Stack

[![CI](https://github.com/ilucasoliveira/personal-library-api/actions/workflows/ci.yml/badge.svg)](https://github.com/ilucasoliveira/personal-library-api/actions/workflows/ci.yml)
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
- **JWT (PyJWT) + bcrypt** — token-based login with hashed passwords
- **Poetry** — dependency and environment management
- **httpx** — outbound requests to Supabase Storage's REST API
- **Alembic** — database migrations
- **pytest** — automated tests (auth, shelf isolation, account settings, visitor rules, error codes, partial updates) against a temporary SQLite database, run by GitHub Actions on every push (`.github/workflows/ci.yml`)

---

## ✨ Features

- **User accounts**: sign up and log in with email and password (bcrypt hashes, JWT bearer tokens)
- **One shelf per account**: every book query is scoped to the logged-in user; someone else's book answers `404`
- **Personal settings**: theme (`twilight`, `paper`, `sepia`, `forest`), accent color and language (`pt` / `en`) saved on the account
- Change password (every other session is logged out) and delete account (removes every book of the account)
- Full CRUD for books: create, read, update, delete
- Reading status tracking: `toRead`, `reading` or `read` (anything else is rejected with `422`)
- Ratings from 0.25 to 5 stars in quarter steps, plus personal comments per book
- Favorite marking
- Profile photo upload per user, stored in Supabase Storage (JPG, PNG, WEBP or GIF, up to 2 MB)
- Basic abuse protection: limits on failed logins per email, sign ups per IP and books per account
- Integration-ready with an external book search (Google Books API) on the frontend
- Environment-based configuration (no secrets committed to source control)
- Configurable CORS via environment variable, supporting multiple deployed origins
- `/ping` health-check endpoint for uptime monitoring, which also touches the database so the free-tier database never goes idle
- **Sign up switch** (`ALLOW_SIGNUP`): turn it off to run an invite-only instance, where accounts are created with `manage create-user`
- **Visitor account** (`DEMO_MODE=true`): a shared account with read-only example books, automatic cleanup of the books visitors add and locked settings

---

## 🏗 Project Structure

```
src/back_end_library/
├── main.py            # FastAPI app instance, middleware, router registration
├── database.py         # SQLAlchemy engine/session setup (NullPool for pooled connections)
├── models.py           # ORM models (User, Book)
├── schemas.py          # Pydantic schemas for validation/serialization
├── auth.py             # Password hashing (bcrypt) and JWT login dependency
├── ratelimit.py        # In-memory limits for failed logins and sign ups
├── config.py           # Environment settings (sign up, limits, visitor account)
├── manage.py           # Admin commands (create an account, claim old books)
├── seed_demo.py        # Resets the visitor account with sample books
├── create_tables.py    # Creates the tables on a fresh database
├── routers/
│   ├── auth.py          # Sign up, log in, visitor log in
│   ├── me.py            # Account: settings, password, photo, delete
│   └── books.py         # Book CRUD, scoped to the logged-in user
alembic/                # Migrations
tests/                  # pytest suite
```

---

## 🔌 API Endpoints

| Method | Endpoint             | Description                     |
|--------|-----------------------|----------------------------------|
| POST   | `/auth/register`      | Create an account (returns a token) |
| POST   | `/auth/login`         | Log in with email and password (form data: `username`, `password`) |
| POST   | `/auth/visitor`       | Log in to the shared visitor account (only with `DEMO_MODE=true`) |
| GET    | `/me`                 | Current account                  |
| PUT    | `/me`                 | Update name, theme, accent color or language |
| PUT    | `/me/password`        | Change password; ends every other session and returns a new token |
| POST   | `/me/photo`           | Upload a profile photo           |
| DELETE | `/me`                 | Delete the account and all its books |
| POST   | `/books`              | Add a new book                  |
| GET    | `/books`              | List your books                 |
| GET    | `/books/{id}`         | Get one of your books            |
| PATCH / PUT | `/books/{id}`    | Update a book: only the fields sent change; `null` clears synopsis, rating, comment or cover |
| DELETE | `/books/{id}`         | Delete a book                    |
| GET/HEAD | `/ping`             | Health check; GET also reports `demo` and `signup` |

Every endpoint except `/ping` and `/auth/*` requires `Authorization: Bearer <token>`. In the interactive docs at `/docs`, use **Authorize** with your email in the username field.

The old book routes (`POST /create`, `PUT /update/{id}`, `DELETE /delete/{id}`) still work and are marked as deprecated in `/docs`.

Errors always come as `{"detail": "<message>", "code": "<code>"}`. The `code` is stable (for example `book_not_found`, `example_read_only`, `invalid_credentials`, `validation_error`), so clients should branch on it instead of on the message.

---

## 🎭 Live app

The public deployment runs with `ALLOW_SIGNUP=true` and `DEMO_MODE=true`: anyone can create an account, or try the shared visitor account without signing up.

- **App:** [my-own-bookshelf.vercel.app](https://my-own-bookshelf.vercel.app)
- **API docs:** [bookshelf-demo-api.onrender.com/docs](https://bookshelf-demo-api.onrender.com/docs)

Visitor account rules, enforced by the API (not just hidden in the UI):

- **Example books are read-only**: updating or deleting one returns `403 Forbidden`
- **Visitor books are temporary**: anything added is removed after `DEMO_VISITOR_BOOK_DAYS` (default 1 day), and only the latest `DEMO_MAX_VISITOR_BOOKS` (default 30) are kept
- **Settings are locked**: name, password, photo and account deletion return `403 Forbidden`
- Real accounts are never touched by these rules

To create or reset the visitor account (it only touches the visitor's books):

```bash
# DATABASE_URL must point to the public database and DEMO_MODE=true (the script refuses to run otherwise)
poetry run alembic upgrade head
poetry run python -m back_end_library.seed_demo
```

The example covers are pinned Open Library cover IDs, picked by hand (Brazilian editions where available), so the seed needs no network. An example without a `cover_id` is looked up on Google Books (set `GOOGLE_BOOKS_KEY`) with Open Library as a fallback.

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
# then fill in DATABASE_URL, JWT_SECRET, ALLOWED_ORIGINS, SUPABASE_URL,
# SUPABASE_SERVICE_KEY (and ALLOW_SIGNUP / DEMO_MODE as needed)

# New database: create the tables and mark the migrations as applied
poetry run python -m back_end_library.create_tables
poetry run alembic stamp head
# Existing database: apply the pending migrations instead
poetry run alembic upgrade head

# Create an account from the terminal (useful with ALLOW_SIGNUP=false)
poetry run python -m back_end_library.manage create-user --email you@example.com --name "Your name"
# Set a new password for someone who forgot it (there is no email recovery)
poetry run python -m back_end_library.manage reset-password --email you@example.com

# Run the development server
poetry run fastapi dev src/back_end_library/main.py

# Run the tests
poetry run pytest
```

---

## ☁️ Deployment

This API runs on **[Render](https://render.com)** (free tier web service), connected to a **[Supabase](https://supabase.com)** PostgreSQL database and Supabase Storage for profile photos. The `/ping` endpoint touches the database, so an uptime monitor (such as [UptimeRobot](https://uptimerobot.com)) can keep the free instance awake.

**Live API docs:** [bookshelf-demo-api.onrender.com/docs](https://bookshelf-demo-api.onrender.com/docs)

**Upgrading a database from before accounts existed:** run `alembic upgrade head`, then create an account with `manage create-user ... --claim-orphans`. Every book without an owner (and the old profile photo) goes to that account.

---

## 📄 License

This project is licensed under the MIT License.
