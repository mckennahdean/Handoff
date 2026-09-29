# Handoff Backend

Python and FastAPI backend for Handoff. Setup and tests: [docs/INSTALL.md](../docs/INSTALL.md). Endpoints: [docs/api](../docs/api/).

| Module | Responsibility |
|---|---|
| `main.py` | Procedure, question, and knowledge gap routes; maps AI errors to 429 and 503 |
| `auth_routes.py` | Signup, login, recovery, and user management routes |
| `auth_service.py` | Passwords (Argon2), tokens (JWT), approval, throttling, recovery codes, and role checks |
| `db_service.py` | All procedure, chunk, and knowledge gap queries |
| `gemini_service.py` | Every AI call (transcription, structuring, answers, embeddings), so changing providers touches one file |
| `models.py` | Database tables (SQLAlchemy) |
| `create_tables.py` | Creates tables and applies idempotent migrations on every start |
| `seed_demo.py` | Loads the Maple & Main demo procedures |
| `reset_password.py` | Break-glass recovery command for whoever runs the server |
| `config.py`, `database.py` | Settings and the database connection |