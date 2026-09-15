# Handoff

Handoff is an AI-powered knowledge capture and question-answering system designed to help small businesses document procedures and preserve operational knowledge. Owners narrate procedures, an AI transcribes and structures them, the owner reviews and approves, and employees query the knowledge base in plain language. The system answers with citation when confident and abstains when it isn't.

## Design principles

- **Abstention is a feature, not a failure.** Handoff never guesses when approved knowledge is insufficient; it logs the gap for future documentation.
- **The human Approval Gate.** No procedure enters the knowledge base without explicit owner review.
- **Gap detection.** Unanswered questions are surfaced to owners rather than silently ignored.
- **The LLM never touches the database directly.** All persistence goes through the backend, keeping the AI grounded and auditable.

## Technology stack

- **Frontend:** Vue 3, Vite, Vue Router
- **Backend:** Python 3.13, FastAPI, SQLAlchemy
- **Database:** PostgreSQL 16 with pgvector extension
- **AI:** Google Gemini (gemini-3.1-flash-lite for text and transcription, gemini-embedding-001 for vectors)
- **CI/CD:** GitHub Actions (backend pytest, frontend lint and build)
- **Development environment:** Docker Compose

## Team

- **Thomas Dean** — Lead Architect
- **McKenna Dean** — Interface Designer
- **Renata Gabdrakhmanova** — Integration Lead

## Project structure

- `frontend/` — Vue application
- `backend/` — FastAPI application, SQLAlchemy models, and Gemini services
- `docs/architecture/` — System design specification and UML component diagram
- `docs/api/` — API specifications and interface contracts
- `tests/` — Application tests (backend tests currently in `backend/test_main.py`)
- `.github/workflows/` — CI/CD pipeline configuration
- `docker-compose.yml` — Local database container

## Running Handoff locally

### One-time setup

1. Install prerequisites: Python 3.13+, Node 22 LTS, Docker Desktop, Git.

2. Clone the repository:

        git clone https://github.com/mckennahdean/Handoff.git
        cd Handoff

3. Get a Gemini API key at https://aistudio.google.com/apikey (free tier is sufficient).

4. Create a `.env` file at the **repository root** with these lines:

        GEMINI_API_KEY=your-key-here
        DATABASE_URL=postgresql+psycopg://handoff_user:handoff_password@localhost:5432/handoff

5. Set up the Python virtual environment:

        python -m venv .venv
        .\.venv\Scripts\Activate.ps1
        pip install -r backend/requirements.txt

6. Install frontend dependencies:

        cd frontend
        npm install
        cd ..

### Every-time startup (three terminals)

**Terminal 1 - Database and schema:**

    docker compose up -d db
    python -m backend.create_tables

**Terminal 2 - Backend:**

    .\.venv\Scripts\Activate.ps1
    python -m uvicorn backend.main:app --reload

Backend serves at http://127.0.0.1:8000.

**Terminal 3 - Frontend:**

    cd frontend
    npm run dev

Frontend serves at http://localhost:5173.

### Using the application

Open http://localhost:5173, create an Owner account, capture a procedure by recording or typing, then approve it. Log out, create an Employee account, and ask Handoff a question about the procedure to see the retrieval-augmented answer with citation.

## Testing

Backend tests use pytest and mock the AI service boundary:

    python -m pytest backend/test_main.py -v

CI automatically runs backend tests and frontend lint/build on every pull request to `main`.

## Documentation

- **System Design Specification:** `docs/architecture/`
- **API contracts:** `docs/api/`
- **UML component diagram:** `docs/architecture/Capstone-Handoff.drawio.png`

## License

MIT License. See [LICENSE](LICENSE) for details.
