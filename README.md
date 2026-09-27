# Handoff

AI knowledge capture and grounded Q&A for small businesses.

An owner explains a procedure out loud. Handoff transcribes it, structures it into steps and warnings, and asks about anything the owner skipped. Nothing reaches employees until the owner approves it. Employees then ask questions in their own words and get an answer with a citation, or an honest "not documented" that becomes a knowledge gap for the owner to fill.

<!-- screenshot: answered question with citation and last-confirmed date -->

## Why Handoff

Small businesses keep their procedures in people's heads. When that person is off shift or leaves, the knowledge goes with them. A general-purpose chatbot makes this worse, because it guesses. Handoff is built around one rule: **answer only from what the owner approved, and say so when it can't.**

## Features

- **Voice capture.** Record, upload, or type a procedure. The AI transcribes it and structures it into steps and warnings.
- **Capture gaps.** The AI asks up to five follow-up questions about what the owner skipped. Answers are merged in under an insert-only guardrail: the AI can add steps, but code rejects any change to the owner's own words.
- **Approval Gate.** Drafts are invisible to employees and to search until the owner approves them. Editing an approved procedure creates a new version.
- **Grounded answers.** Every answer cites its procedure and the date the owner last confirmed it.
- **Two abstention gates.** The Threshold Gate stops questions that nothing in the knowledge base is close to, without an AI call. The Generation Gate has the AI confirm that the closest procedure actually contains the answer.
- **Knowledge gaps.** Unanswered questions are logged, grouped by meaning, and ranked by how often they are asked, with every wording kept ("Also Asked As"). Approving a procedure that answers a gap resolves it automatically; deleting that procedure reopens it.
- **Roles and security.** Owner and employee accounts, invite codes, Argon2 password hashing, and signed login tokens. A test checks that every non-public API route requires a login.

## Performance

Measured offline on Maple & Main Coffee, a fictional coffee shop created for testing (7 procedures, 43 labeled questions, 30 labeled question pairs). Method, raw results, and how to rerun: [evaluation/README.md](evaluation/README.md).

| Measure | Result |
|---|---|
| Correct procedure retrieved | 29 of 29 answerable questions |
| Answered when it should | 29 of 29 |
| Abstained when it should | 14 of 14 |
| Answer quality | 28 fully correct, 1 partial, 0 invented facts |
| Median response time | 1.3 to 3.6 seconds across two runs |
| Automated tests | 78 passing, 77% line coverage (CI requires at least 70%) |

### Known limitations

- **Thin margins.** Some correct answers score just above the 0.68 answer threshold (the lowest is 0.691). A wording mismatch can cause a miss: "What time does the store open?" scored 0.670 until the owner added the word "store" to the procedure. The knowledge gap loop is how owners find and fix these.
- **Grouping by topic, not intent.** Different questions on the same topic can be grouped together (similarity up to 0.807). "Also Asked As" keeps every wording visible so the owner decides.
- **Auto-resolve uses one gate.** Resolving a gap on approval uses the Threshold Gate only. In the evaluation, 1 of 14 should-abstain questions would be marked resolved if its closest procedure were re-approved. Adding the Generation Gate to auto-resolve is planned future work.
- **AI provider limits.** On the Gemini free tier, text generation is limited to 15 requests per minute, and response times depend on the provider's load (the slowest measured answer took 33 seconds).
- **One business per install.**

## Quick start (Docker)

You need Docker Desktop, Git, and a free Gemini API key from https://aistudio.google.com/apikey.

```
git clone https://github.com/mckennahdean/Handoff.git
cd Handoff
cp backend/.env.example .env
```

Open `.env` and fill in `GEMINI_API_KEY` and `JWT_SECRET_KEY` (the file explains how to generate the secret). Then:

```
docker compose up --build -d
docker compose exec backend python -m backend.seed_demo
```

The second command is optional. It loads the Maple & Main demo procedures and takes about two minutes. Open http://localhost:8080 and create the first account, which becomes the owner.

Developer setup, running tests, and troubleshooting: [docs/INSTALL.md](docs/INSTALL.md).

## Architecture

A Vue 3 single-page app talks to a FastAPI backend, which stores procedures, users, and knowledge gaps in PostgreSQL with the pgvector extension. Each procedure step and warning is embedded separately, so a question is matched against the exact step that answers it. Every AI call lives in one module (`backend/gemini_service.py`), so changing AI providers touches one file. Details and diagram: [docs/architecture/](docs/architecture/).

## CI/CD

Every pull request runs:

1. Backend tests against a real PostgreSQL and pgvector database, with a coverage report and a 70% floor
2. Frontend lint and production build
3. Docker image builds and a smoke test of the full running stack

Images that pass are published to the GitHub Container Registry (`ghcr.io/mckennahdean/handoff-backend` and `handoff-frontend`), tagged by commit, by pull request, and `latest` from `main`.

## Documentation

| Document | Contents |
|---|---|
| [Install guide](docs/INSTALL.md) | Docker and developer setup, configuration, tests, troubleshooting |
| [User guide](docs/USER_GUIDE.md) | Owner and employee workflows |
| [API reference](docs/api/) | Every endpoint, who can call it, and what it returns |
| [Architecture](docs/architecture/) | Components, data flow, and design decisions |
| [Evaluation](evaluation/README.md) | How accuracy, abstention, and latency were measured |
| [Contributions](docs/CONTRIBUTIONS.md) | What each team member built |

## Technology

Vue 3, Vite, Vue Router · Python 3.13, FastAPI, SQLAlchemy · PostgreSQL 16 with pgvector · Google Gemini (gemini-3.1-flash-lite, gemini-embedding-001) · Docker Compose, nginx · GitHub Actions, GitHub Container Registry

## Team

UMGC CMSC 495 Computer Science Capstone, Fall 2026.

- **Thomas Dean**, Lead Architect
- **McKenna Dean**, Interface Designer
- **Renata Gabdrakhmanova**, Integration Lead

## License

MIT. See [LICENSE](LICENSE).