# Handoff Frontend

Vue 3 application that provides the user interface for capturing procedures, reviewing AI-structured content, and querying approved knowledge.

## Technology

- Vue 3
- Vite
- Vue Router
- Native `fetch` for backend communication
- oxlint and eslint for linting

## Views

- `HomeView` — Landing page
- `LoginView` / `SignupView` — Authentication (alpha uses `localStorage`; server-side auth is planned for beta)
- `OwnerDashboardView` — Owner navigation hub
- `EmployeeDashboardView` — Employee navigation hub
- `CaptureProcedureView` — Record, upload, or type a procedure for AI structuring
- `ProcedureReviewView` — Owner review and approval of AI-structured procedures
- `ProceduresView` — List of approved procedures
- `QueryView` — Ask Handoff questions and receive grounded answers
- `GapsView` — Documentation gaps identified from unanswered queries

## Running the frontend

From the `frontend` directory:

    npm install
    npm run dev

The dev server runs at http://localhost:5173 and expects the backend running at http://127.0.0.1:8000.

## Linting and build

    npm run lint
    npm run build

CI runs both on every pull request to `main`.
