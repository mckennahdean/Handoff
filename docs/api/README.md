# Handoff API Reference

The Handoff backend is a FastAPI application. When it is running, interactive documentation is available at http://127.0.0.1:8000/docs (developer setup) or http://localhost:8000/docs (Docker), where every endpoint can be tried directly.

## Authentication

Most endpoints require a login token. Get one from `POST /api/auth/login`, then send it with every request:

```
Authorization: Bearer <access_token>
```


Tokens expire after 8 hours. There are two roles: **owner** and **employee**. The user is reloaded from the database on every request, so role changes, deleted accounts, and password resets take effect immediately: a token issued before the account's latest password reset is refused.

A test (`backend/test_route_guards.py`) checks every route the app has and fails if any route other than the five public ones below answers without a login.

## Errors

Errors return JSON with a readable `detail` message:

```json
{ "detail": "Procedure not found." }
```

| Status | Meaning |
|---|---|
| 400 | The request was invalid (for example, empty text, a weak password, or a recovery code that does not match) |
| 401 | Not logged in, the token is invalid or expired, or the session ended because the password was reset |
| 403 | Logged in, but the role is not allowed, or the account is still waiting for owner approval |
| 404 | Not found. Employees also get 404 for unapproved drafts, so a draft's existence is not revealed. |
| 413 | Audio file larger than 10 MB |
| 422 | A required field is missing or has the wrong type |
| 429 | The AI service's usage limit was reached, or too many signups are waiting for approval; wait and try again |
| 502 | The AI tried to change the owner's existing steps, so the merge was cancelled |
| 503 | The AI or search service is temporarily unavailable |

## Endpoints

### Public (no login)

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Health check |
| GET | `/api/auth/setup-status` | Reports whether the first (owner) account has been created |
| POST | `/api/auth/signup` | Create an account (the first becomes the owner; later ones wait for approval) |
| POST | `/api/auth/login` | Sign in and receive a token |
| POST | `/api/auth/recover` | Set a new password with a recovery code |

### Any logged-in user

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/auth/me` | The current user |
| POST | `/api/auth/recovery-codes` | Replace your own recovery codes (shown once) |
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
| GET | `/api/business/users` | List everyone with an account, including pending signups |
| POST | `/api/business/users/{user_id}/approve` | Approve a pending account |
| POST | `/api/business/users/{user_id}/recovery-codes` | Issue a new set of recovery codes for someone (shown once) |
| PATCH | `/api/business/users/{user_id}/role` | Change a user's role (not your own) |
| DELETE | `/api/business/users/{user_id}` | Delete an employee account, or reject a pending signup |

## Request and response details

### Sign up: `POST /api/auth/signup`

```json
{
  "name": "Sam Rivera",
  "email": "sam@example.com",
  "password": "a-Strong-password-2026",
  "business_name": "Maple & Main Coffee"
}
```

The first account creates the business (it needs `business_name`), becomes the owner, and receives a token like login. Every later account is created as a pending employee and receives no token:

```json
{
  "status": "pending",
  "message": "Account created. Your business owner needs to approve it before you can sign in."
}
```

The response is identical, and takes the same time, whether or not the email already has an account, so signup cannot be used to discover registered emails. If 20 signups are already waiting, the response is `429`.

### Log in: `POST /api/auth/login`

```json
{ "email": "sam@example.com", "password": "a-Strong-password-2026" }
```

Returns `access_token`, `user` (`id`, `name`, `email`, `role`, `status`), and `needs_recovery_codes`, which is `true` when the account has no unused recovery codes (the app then shows a new set once).

A wrong email, a wrong password, and a paused account all return the same `401` message. After 5 failed attempts in a row, sign-in is paused for 15 minutes. A correct password for a pending account returns `403` with "Your account is waiting for owner approval."

### Recover an account: `POST /api/auth/recover`

```json
{
  "email": "sam@example.com",
  "recovery_code": "K7QPM-2XH9R",
  "new_password": "a-New-Strong-password-2026"
}
```

Returns `{ "message": "Password updated. You can now sign in." }`. The code is used up, and any token issued before the reset stops working. Codes are accepted in any case, with or without the dash.

The new password is checked against the password rules first (`400`). Every other failure (an unknown email, a wrong or used code, a paused account) returns the same `400` message. Wrong codes count toward the same 5-attempt pause as logins.

### Recovery codes: `POST /api/auth/recovery-codes` and `POST /api/business/users/{user_id}/recovery-codes`

```json
{ "codes": ["K7QPM-2XH9R", "..."] }
```

Returns eight new one-time codes and replaces any earlier set. Only Argon2 hashes of the codes are stored, so this response is the only time they can be seen. The owner version returns `404` if the user does not exist.

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

### Approve an account: `POST /api/business/users/{user_id}/approve`

Returns the updated user with `"status": "active"`, or `404` if the user does not exist.

### Change a role: `PATCH /api/business/users/{user_id}/role`

```json
{ "role": "owner" }
```

Returns the updated user (`id`, `name`, `email`, `role`, `status`). Returns `400` if the role is not `owner` or `employee`, or if the user is the caller: owners cannot change their own role, so the business always keeps at least one owner. Returns `404` if the user does not exist.

### Delete an employee: `DELETE /api/business/users/{user_id}`

Returns `{ "message": "Employee account deleted." }`. The same request rejects a pending signup. Owner accounts cannot be deleted (`400`). The deleted person's next request is rejected with `401`, because every request reloads the user from the database.