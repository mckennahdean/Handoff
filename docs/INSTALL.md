# Installing Handoff

There are two ways to run Handoff:

- **Docker** (recommended for trying it out): the whole app runs in containers. You only need Docker Desktop and Git.
- **Developer setup**: the backend and frontend run directly on your machine, so code changes appear immediately. Use this to work on Handoff.

Both need a Gemini API key. The free tier is enough: get one at https://aistudio.google.com/apikey.

## Option 1: Docker

### Requirements

- Docker Desktop (running)
- Git

### Steps

1. Clone the repository:

```
   git clone https://github.com/mckennahdean/Handoff.git
   cd Handoff
```

2. Create your settings file from the example:

```
   cp backend/.env.example .env
```

3. Open `.env` in a text editor and fill in two values:

   - `GEMINI_API_KEY`: your Gemini API key.
   - `JWT_SECRET_KEY`: a random secret that signs login tokens. Generate one with the command below, then paste the output after the `=`:

```
     python -c "import secrets; print(secrets.token_hex(32))"
```

   Leave the other settings as they are. `DATABASE_URL` points at `localhost`, which is correct for the developer setup; Docker Compose replaces it automatically inside the containers.

4. Build and start the database, backend, and frontend:

```
   docker compose up --build -d
```

   The first build takes a few minutes. Check that all three containers report `healthy`:

```
   docker compose ps
```

5. (Optional) Load the demo data, seven procedures for Maple & Main Coffee, a fictional coffee shop:

```
   docker compose exec backend python -m backend.seed_demo
```

   This takes about two minutes, because it pauses between procedures to stay under the free tier's embedding limit. It is safe to run again: procedures that already exist are skipped.

6. Open http://localhost:8080 and create an account. **The first account becomes the owner.** Passwords need at least 12 characters, with uppercase and lowercase letters, a number, and a special character.

7. To add employees, copy the invite code from the Team Access card on the owner dashboard. Employees enter it when they sign up.

### Stopping and updating

```
docker compose down          # stops the app; your data is kept
git pull
docker compose up --build -d # rebuilds with the latest code
```

> **Warning:** `docker compose down -v` also deletes the database volume, which permanently erases every procedure, account, and knowledge gap. See [Backing up your data](#backing-up-your-data) first.

## Option 2: Developer setup

### Requirements

- Python 3.13 or later
- Node.js 22 LTS
- Docker Desktop (for the database)
- Git

### One-time setup

1. Clone the repository and create `.env` exactly as in Docker steps 1 to 3 above. Keep `.env` in the repository root.

2. Create a Python virtual environment and install the backend dependencies.

   Windows (PowerShell):

```
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r backend/requirements.txt
```

   macOS or Linux:

```
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r backend/requirements.txt
```

3. Install the frontend dependencies:

```
   cd frontend
   npm install
   cd ..
```

### Every time you work on Handoff

Use two terminals, both in the repository root, with the virtual environment active in the first.

**Terminal 1: database and backend**

```
docker compose up -d db
python -m backend.create_tables
python -m uvicorn backend.main:app --reload
```

`create_tables` is safe to run every time: it creates missing tables and applies small schema updates, and does nothing when the database is already current. The backend serves at http://127.0.0.1:8000, with interactive API documentation at http://127.0.0.1:8000/docs.

**Terminal 2: frontend**

```
cd frontend
npm run dev
```

Open http://localhost:5173. To load the demo data in this setup, run `python -m backend.seed_demo` from the repository root.

If the Docker version of Handoff is also running, stop its backend and frontend first so the ports are free: `docker compose stop backend frontend`.

## Configuration

All settings live in `.env` in the repository root. `backend/.env.example` documents each one.

| Setting | Required | Purpose |
|---|---|---|
| `GEMINI_API_KEY` | Yes | Access to Google Gemini |
| `JWT_SECRET_KEY` | Yes | Signs login tokens. Every install needs its own. |
| `DATABASE_URL` | Yes | PostgreSQL connection (the default matches `docker-compose.yml`) |
| `TEST_DATABASE_URL` | No | A separate database for integration tests (see below) |
| `ANSWER_THRESHOLD` | No | Minimum similarity to answer a question (default 0.68, chosen from the evaluation) |
| `GAP_GROUPING_THRESHOLD` | No | Minimum similarity to group two unanswered questions (default 0.75) |
| `GEMINI_TEXT_MODEL`, `GEMINI_STRUCTURE_MODEL`, `GEMINI_EMBEDDING_MODEL` | No | Which Gemini models to use |
| `CORS_ORIGINS` | No | Browser addresses allowed to call the API |

## Running the tests

Backend tests (from the repository root, virtual environment active):

```
python -m pytest backend/ -v --ignore=backend/test.py --ignore=backend/test_embedding.py
```

The AI is replaced by a fake in every test, so tests are free, fast, and repeatable.

**Integration tests** run the real database code against PostgreSQL. They need their own database, because every run deletes and recreates all of its tables:

1. Create the test database once:

```
   docker exec handoff-db psql -U handoff_user -d handoff -c "CREATE DATABASE handoff_test;"
```

2. In `.env`, remove the `#` in front of the `TEST_DATABASE_URL` line.

Without `TEST_DATABASE_URL`, integration tests are skipped rather than failed. As a safety check, they refuse to run against any database without "test" in its name.

Coverage report:

```
python -m pytest backend/ --cov=backend --ignore=backend/test.py --ignore=backend/test_embedding.py
```

Frontend lint:

```
cd frontend
npm run lint
```

The same checks run automatically on every pull request (see the CI/CD section of the [README](../README.md)).

## Backing up your data

Create a backup (the `-F c` format is compact and safe to copy between machines):

```
docker exec handoff-db pg_dump -U handoff_user -d handoff -F c -f /tmp/handoff.dump
docker cp handoff-db:/tmp/handoff.dump ./handoff-backup.dump
```

Restore it into a running database:

```
docker cp ./handoff-backup.dump handoff-db:/tmp/handoff.dump
docker exec handoff-db pg_restore -U handoff_user -d handoff --clean /tmp/handoff.dump
```

## Troubleshooting

**"JWT_SECRET_KEY is not configured" when signing up or logging in.** `.env` has no secret. Generate one (Docker step 3), then restart the backend.

**I changed `.env` but nothing changed.** Settings are read when the backend starts. In the developer setup, stop uvicorn (`Ctrl + C`) and start it again; `--reload` watches code files, not `.env`. In Docker, recreate the backend container, because `restart` keeps the old settings:

```
docker compose up -d --force-recreate backend
```

**My frontend change does not appear at http://localhost:8080.** The Docker frontend is a built copy of the code. Rebuild it with `docker compose up --build -d`, or use the developer setup, which shows changes immediately. For the same reason, `VITE_API_URL` is fixed when the frontend image is built.

**"Handoff's AI has reached its usage limit for now."** The Gemini free tier limits requests per minute and per day. Wait a minute and try again; if it continues, the daily limit is used up. Check your key's limits at https://ai.dev/rate-limit.

**The demo seed stopped partway.** Usually a usage limit. Run it again: procedures that were already added are skipped.

**Integration tests show as SKIPPED.** `TEST_DATABASE_URL` is not set. See [Running the tests](#running-the-tests).

**A port is already in use (5432, 8000, 5173, or 8080).** Another copy of Handoff, or another program, is using it. `docker compose ps` shows what Docker is running; stop the Docker backend and frontend before using the developer setup.

**Recording does not start.** The browser needs microphone permission. Browsers only allow recording on `localhost` or HTTPS addresses, so open Handoff through `localhost`, not your computer's network address.

**On Windows, `pip install -r backend/requirements.txt` fails after regenerating the file.** In PowerShell, `>` saves files as UTF-16, which pip cannot read. Regenerate the file with:

```
pip freeze | Out-File -Encoding utf8 backend\requirements.txt
```