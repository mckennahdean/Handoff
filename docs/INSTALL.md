# Installing Handoff

There are two ways to run Handoff:

- **Docker** (recommended for trying it out): the whole app runs in containers.
- **Developer setup**: the backend and frontend run directly on your machine, so code changes appear immediately. Use this to work on Handoff.

Both start with the same first step. No administrator rights are needed for any step.

## Step 1: Get the code and configure it

Everyone does this step. You need **Git** and a **Gemini API key** (the free tier is enough: get one at https://aistudio.google.com/apikey).

Clone the repository:

```
git clone https://github.com/mckennahdean/Handoff.git
cd Handoff
```

Create your settings file from the example:

```
cp backend/.env.example .env
```

Open `.env` in a text editor and fill in two values:

- `GEMINI_API_KEY`: your Gemini API key.
- `JWT_SECRET_KEY`: a random secret that signs login tokens. Every install needs its own. Generate one with the command below, then paste the output after the `=`.

If you have Docker Desktop (it must be running):

```
docker run --rm python:3.13-slim python -c "import secrets; print(secrets.token_hex(32))"
```

If you have Python instead:

```
python -c "import secrets; print(secrets.token_hex(32))"
```

Leave the other settings as they are. `DATABASE_URL` points at `localhost`, which is correct for the developer setup; Docker Compose replaces it automatically inside the containers.

## Step 2: Choose how to run Handoff

- [Option A: Docker](#option-a-docker), to try Handoff or run it for a team
- [Option B: Developer setup](#option-b-developer-setup), to work on the code

## Option A: Docker

**Also requires:** Docker Desktop, running.

### Start Handoff

Build and start the database, backend, and frontend:

```
docker compose up --build -d
```

The first build takes a few minutes. Then check the containers:

```
docker compose ps
```

The database and backend should report `healthy`, and the frontend should report `Up`.

### Load the demo data (optional)

This adds seven procedures for Maple & Main Coffee, a fictional coffee shop:

```
docker compose exec backend python -m backend.seed_demo
```

It takes about two minutes, because it pauses between procedures to stay under the free tier's embedding limit. It is safe to run again: procedures that already exist are skipped.

### Create the owner account

Open http://localhost:8080 and sign up. **The first account becomes the owner.** Passwords need at least 12 characters, with uppercase and lowercase letters, a number, and a special character.

To add employees, copy the invite code from the Team Access card on the owner dashboard. Employees enter it when they sign up.

### Stop and update

Stop the app (your data is kept):

```
docker compose down
```

Update to the latest code and rebuild:

```
git pull
docker compose up --build -d
```

> **Warning:** `docker compose down -v` also deletes the database volume, which permanently erases every procedure, account, and knowledge gap. See [Backing up your data](#backing-up-your-data) first.

## Option B: Developer setup

**Also requires:** Python 3.13 or later, Node.js 22 LTS, and Docker Desktop (for the database).

### One-time setup

Create a Python virtual environment and install the backend's packages into it.

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

If Windows says running scripts is disabled, see [Troubleshooting](#troubleshooting).

Install the frontend's packages:

```
cd frontend
npm install
cd ..
```

### Every time you work on Handoff

Use two terminals, both starting in the repository root.

**Terminal 1: database and backend.** First activate the virtual environment. Do this in every new terminal, because the backend's packages are installed there, not system-wide. Your prompt should then begin with `(.venv)`.

Windows (PowerShell):

```
.venv\Scripts\Activate.ps1
```

macOS or Linux:

```
source .venv/bin/activate
```

Then start the database and the backend:

```
docker compose up -d db
python -m backend.create_tables
python -m uvicorn backend.main:app --reload
```

`create_tables` is safe to run every time: it creates missing tables and applies small schema updates, and does nothing when the database is already current. The backend serves at http://127.0.0.1:8000, with interactive API documentation at http://127.0.0.1:8000/docs.

**Terminal 2: frontend.** No virtual environment is needed here: npm keeps the frontend's packages in `frontend/node_modules`, inside the project.

```
cd frontend
npm run dev
```

Open http://localhost:5173. To load the demo data, run `python -m backend.seed_demo` in Terminal 1's environment (from the repository root, with `(.venv)` active).

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

These use the developer setup. With the virtual environment active, from the repository root:

```
python -m pytest backend/ -v --ignore=backend/test.py --ignore=backend/test_embedding.py
```

The AI is replaced by a fake in every test, so tests are free, fast, and repeatable.

### Integration tests

Integration tests run the real database code against PostgreSQL. They need their own database, because every run deletes and recreates all of its tables. Set it up once, in this order.

First, with the database running, create the test database:

```
docker exec handoff-db psql -U handoff_user -d handoff -c "CREATE DATABASE handoff_test;"
```

Then, in `.env`, remove the `#` in front of the `TEST_DATABASE_URL` line.

Without `TEST_DATABASE_URL`, integration tests are skipped rather than failed. As a safety check, they refuse to run against any database without "test" in its name.

### Coverage and lint

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

**"JWT_SECRET_KEY is not configured" when signing up or logging in.** `.env` has no secret. Generate one as in [Step 1](#step-1-get-the-code-and-configure-it), then restart the backend.

**"No module named ..." (for example `sqlalchemy` or `uvicorn`).** The virtual environment is not active in that terminal. Activate it as in [Every time you work on Handoff](#every-time-you-work-on-handoff); your prompt should begin with `(.venv)`.

**Windows says "running scripts is disabled on this system" when activating the virtual environment.** PowerShell blocks scripts by default. Allow local scripts for your user account (no administrator rights needed), then activate again:

```
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

**I changed `.env` but nothing changed.** Settings are read when the backend starts. In the developer setup, stop uvicorn (`Ctrl + C`) and start it again; `--reload` watches code files, not `.env`. In Docker, recreate the backend container, because `restart` keeps the old settings:

```
docker compose up -d --force-recreate backend
```

**My frontend change does not appear at http://localhost:8080.** The Docker frontend is a built copy of the code. Rebuild it with `docker compose up --build -d`, or use the developer setup, which shows changes immediately. For the same reason, `VITE_API_URL` is fixed when the frontend image is built.

**"Handoff's AI has reached its usage limit for now."** The Gemini free tier limits requests per minute and per day. Wait a minute and try again; if it continues, the daily limit is used up. Check your key's limits at https://ai.dev/rate-limit.

**The demo seed stopped partway.** Usually a usage limit. Run it again: procedures that were already added are skipped.

**Integration tests show as SKIPPED.** `TEST_DATABASE_URL` is not set. See [Integration tests](#integration-tests).

**Integration tests show ERROR with `database "handoff_test" does not exist`.** The test database has not been created yet. Run the `CREATE DATABASE` command in [Integration tests](#integration-tests).

**A port is already in use (5432, 8000, 5173, or 8080).** Usually the Docker version and the developer setup are running at the same time. `docker compose ps` shows what Docker is running. Stop the Docker backend and frontend before starting the developer setup:

```
docker compose stop backend frontend
```

**Recording does not start.** The browser needs microphone permission. Browsers only allow recording on `localhost` or HTTPS addresses, so open Handoff through `localhost`, not your computer's network address.

**On Windows, `pip install -r backend/requirements.txt` fails after regenerating the file.** In PowerShell, `>` saves files as UTF-16, which pip cannot read. Regenerate the file with:

```
pip freeze | Out-File -Encoding utf8 backend\requirements.txt
```