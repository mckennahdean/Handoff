# Handoff API Reference

The Handoff backend is a FastAPI application. When it is running, interactive documentation is available at http://127.0.0.1:8000/docs (developer setup) or http://localhost:8000/docs (Docker), where every endpoint can be tried directly.

## Authentication

Most endpoints require a login token. Get one from `POST /api/auth/login` (or signup), then send it with every request:

```
Authorization: Bearer <access_token>
```

Tokens expire after 8 hours. There are two roles: **owner** and **employee**. The user is reloaded from the database on every request, so role changes and deleted accounts take effect immediately.

A test (`backend/test_route_guards.py`) checks every route the app has and fails if any route other than the four public ones below answers without a login.

## Errors

Errors return JSON with a readable `detail` message:

```json
{ "detail": "Procedure not found." }
```

| Status | Meaning |
|---|---|
| 400 | The request was invalid (for example, empty text) |
| 401 | Not logged in, or the token is invalid or expired |
| 403 | Logged in, but the role is not allowed |
| 404 | Not found. Employees also get 404 for unapproved drafts, so a draft's existence is not revealed. |
| 413 | Audio file larger than 10 MB |
| 422 | A required field is missing or has the wrong type |
| 429 | The AI service's usage limit was reached; wait and try again |
| 502 | The AI tried to change the owner's existing steps, so the merge was cancelled |
| 503 | The AI or search service is temporarily unavailable |

## Endpoints

### Public (no login)

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Health check |
| GET | `/api/auth/setup-status` | Reports whether the first (owner) account has been created |
| POST | `/api/auth/signup` | Create an account |
| POST | `/api/auth/login` | Sign in and receive a token |

### Any logged-in user

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/auth/me` | The current user |
| GET | `/api/procedures` | List procedures (employees see approved only; owners also see drafts) |
| GET | `/api/procedures/{procedure_id}` | One procedure with its steps and warnings |
| POST | `/api/query` | Ask a question |

### Owner only

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/upload-audio` | Transcribe an audio recording |
| POST | `/api/structure-procedure` | Structure text into steps, warnings, and capture-gap questions |
| POST | `/api/procedures/drafts` | Save a structured procedure as an unapproved draft |
| POST | `/api/procedures/merge-answers` | Add the owner's gap answers as new steps (insert-only) |
| POST | `/api/approve-procedure` | Approve a draft or an edited procedure |
| DELETE | `/api/procedures/{procedure_id}` | Delete a procedure and reopen the gaps it resolved |
| GET | `/api/gaps` | List knowledge gaps |
| POST | `/api/gaps/{gap_id}/dismiss` | Dismiss a knowledge gap |
| GET | `/api/business/invite-code` | The current invite code |
| POST | `/api/business/invite-code/regenerate` | Replace the invite code |
| GET | `/api/business/users` | List everyone with access |
| PATCH | `/api/business/users/{user_id}/role` | Change a user's role (not your own) |
| DELETE | `/api/business/users/{user_id}` | Delete an employee account |

## Request and response details

### Sign up: `POST /api/auth/signup`

```json
{
  "name": "Sam Rivera",
  "email": "sam@example.com",
  "password": "a-Strong-password-2026",
  "business_name": "Maple & Main Coffee",
  "invite_code": null
}
```

The first account becomes the owner and provides `business_name`. Every later account provides `invite_code` instead. Returns `201` with a token, like login.

### Log in: `POST /api/auth/login`

```json
{ "email": "sam@example.com", "password": "a-Strong-password-2026" }
```

Returns `access_token` and `user` (including `role`). A wrong email and a wrong password return the same `401` message, so the response never reveals which emails have accounts.

### Ask a question: `POST /api/query`

```json
{ "question": "What time does the store open?" }
```

When an approved procedure contains the answer:

```json
{
  "status": "answered",
  "answer": "The store opens at 6:30 AM.",
  "source_procedure": "Opening the Cafe",
  "procedure_id": 1,
  "similarity": 0.701,
  "last_confirmed": "2026-09-26T23:45:00Z"
}
```

When none does, Handoff abstains and records a knowledge gap:

```json
{
  "status": "not_documented",
  "message": "This information is not currently documented.",
  "gap_logged": true,
  "similarity": 0.670
}
```

`gap_logged` is `false` if the gap could not be saved, so the response never claims a gap was recorded when it was not. An outage returns `503` (or `429` for a usage limit) and records nothing.

### Structure a procedure: `POST /api/structure-procedure`

Request: `{ "text": "First, unlock the back door..." }`

Returns `title`, `steps`, `warnings`, and up to five `gap_questions` (capture gaps) about what the owner may have skipped.

### Merge gap answers: `POST /api/procedures/merge-answers`

Request: the current `title`, `steps`, and `warnings`, plus `answers`, a list of `{ "question": ..., "answer": ... }`. Returns the updated steps and warnings. Every original step must come back unchanged and in order; otherwise the response is `502` and nothing changes.

### Approve: `POST /api/approve-procedure`

Request: `title`, `steps`, `warnings`, and the `procedure_id` of the draft or procedure being approved.

```json
{
  "status": "approved",
  "procedure_id": 1,
  "title": "Opening the Cafe",
  "version": 3,
  "last_confirmed": "2026-09-26T23:45:00Z",
  "resolved_gaps": 1
}
```

Approval is all or nothing: if embedding fails, nothing is saved. `resolved_gaps` counts the open knowledge gaps this procedure now answers, which are resolved automatically.

### Change a role: `PATCH /api/business/users/{user_id}/role`

```json
{ "role": "owner" }
```

Returns the updated user (`id`, `name`, `email`, `role`). Returns `400` if the role is not `owner` or `employee`, or if the user is the caller: owners cannot change their own role, so the business always keeps at least one owner. Returns `404` if the user does not exist.

### Delete an employee: `DELETE /api/business/users/{user_id}`

Returns `{ "message": "Employee account deleted." }`. Owner accounts cannot be deleted (`400`). The deleted person's next request is rejected with `401`, because every request reloads the user from the database.