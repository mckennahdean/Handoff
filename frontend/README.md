# Handoff Frontend

Vue 3 application that provides the user interface for capturing procedures, reviewing AI-structured content, and querying approved knowledge.

## Technology

- Vue 3
- Vite
- Vue Router
- Native `fetch` for backend communication
- oxlint and eslint for linting

## Views

- `LoginView` and `SignupView`: sign-in and signup. Every signup after the first owner waits for approval.
- `RecoverAccountView`: reset a forgotten password with a recovery code.
- `RecoveryCodesView`: shown once after a first sign-in to save recovery codes.
- `OwnerDashboardView`: owner navigation hub with live counts.
- `UserManagementView`: owner-only approval queue, roles, recovery codes, and account deletion.
- `EmployeeDashboardView`: employee navigation hub.
- `CaptureProcedureView`: record, upload, or type a procedure for AI structuring.
- `ProcedureReviewView`: owner review, capture gaps, and approval of AI-structured procedures.
- `ProceduresView`: approved procedures (owners also see drafts).
- `ProcedureDetailView`: read-only view of one approved procedure, opened with **View** from the Procedures page.
- `QueryView`: ask Handoff questions and receive grounded answers.
- `GapsView`: knowledge gaps from questions Handoff could not answer.
- `NotFoundView`: custom 404 page with team pet photos.

Every request goes through `src/api.js`, which attaches the login token and returns to the login page when the server rejects a session.

## Running the frontend

From the `frontend` directory:

    npm install
    npm run dev

The dev server runs at http://localhost:5173 and expects the backend running at http://127.0.0.1:8000.

## Linting and build

    npm run lint
    npm run build

CI runs both on every pull request to `main`.
