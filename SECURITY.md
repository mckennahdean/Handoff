# Security

Handoff is self-hosted by one small business. This document lists the threats we designed against, the control for each, and the automated test or measurement that proves it, followed by the risks that remain.

## Reporting a vulnerability

Please do not open a public issue. Contact a maintainer listed in [docs/CONTRIBUTIONS.md](docs/CONTRIBUTIONS.md) directly, with steps to reproduce. We will confirm the report and share a fix plan.

## Threat model

Threats are grouped with STRIDE. Evidence names are tests in `backend/`, or results from [evaluation/](evaluation/README.md).

| Category | Threat | Control | Evidence |
|---|---|---|---|
| Spoofing | Guessing a password | Argon2 hashing; 5 failures pause sign-in for 15 minutes, counted under a row lock | `test_five_failed_logins_pause_sign_in_for_fifteen_minutes`, `test_password_is_hashed_not_stored_plain` |
| Spoofing | Guessing a recovery code | 8 codes of about 50 bits each, stored with Argon2; failures count toward the same pause | `test_recovery_codes_are_stored_hashed_and_work_once`, `test_wrong_recovery_codes_count_toward_the_lock` |
| Spoofing | Forged or expired session token | JWT signature and 8-hour expiry checked on every request | `test_forged_token_is_rejected`, `test_expired_token_is_rejected` |
| Spoofing | Old session after a password reset | Tokens issued before the last password change are refused | `test_a_password_reset_ends_older_sessions` |
| Spoofing | Unknown person creating an account | Every signup waits for the owner's approval | `test_signup_after_the_owner_waits_for_approval`, `test_a_token_for_a_pending_account_is_refused` |
| Tampering | The AI rewriting the owner's steps | Insert-only guardrail: every original step must come back word for word and in order, or the merge is refused | `test_guardrail_rejects_reworded_steps`, `test_guardrail_rejects_reordered_steps`, `test_merge_rejects_ai_that_rewrites_steps` |
| Information disclosure | Learning which emails have accounts | Login, signup, and recovery give one answer and do the same hashing work whether or not the email exists | `test_login_gives_one_answer_for_wrong_password_and_unknown_email`, `test_signup_gives_the_same_answer_for_an_existing_email`, `test_recover_gives_one_answer_for_every_failure` |
| Information disclosure | Employees seeing unapproved drafts | Drafts have no embeddings, so search cannot return them; employees get 404, not 403 | `test_drafts_are_never_retrieved`, `test_employee_cannot_view_pending_draft` |
| Information disclosure | Secrets leaking through images or config | `.env` is excluded from every Docker build; an empty `JWT_SECRET_KEY` fails loudly instead of signing with a default | Verified in the CI image build |
| Denial of service | Anyone burning the AI quota | Every route except the public ones requires a login | `test_every_route_except_public_ones_requires_login` |
| Denial of service | Flooding the approval queue | At most 20 pending accounts (429 after that) | `test_signup_is_refused_when_too_many_accounts_are_pending` |
| Denial of service | Very long passwords exhausting the CPU | Passwords are capped at 128 characters | `test_overly_long_password_is_rejected` |
| Elevation of privilege | An employee using owner functions | Owner-only routes; the role is reloaded from the database on every request, not trusted from the token | `test_employee_cannot_approve_procedure`, `test_the_database_not_the_token_decides_who_you_are` |
| Elevation of privilege | Leaving the business with no owner | Owners cannot change their own role or be deleted | `test_owner_cannot_change_their_own_role`, `test_owner_accounts_cannot_be_deleted` |
| AI output | Invented or ungrounded answers | Answers come only from an approved procedure; the Threshold Gate and Generation Gate abstain otherwise | Evaluation: 14 of 14 correct abstentions, 0 invented facts |

## Hardening

- Containers run as non-root users.
- CORS is an explicit allowlist, never `*`.
- nginx sends `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, and a strict referrer policy.
- CI publishes images with a short-lived token and plain commands instead of third-party actions.
- Last resort for a locked-out sole owner: `python -m backend.reset_password <email>` on the server, because whoever controls the server already controls the data.

## Known residual risks

- **No multi-factor authentication.** Passkeys or TOTP are future work.
- **Throttling is per account, not per address.** One password tried against many accounts is not slowed. A rate limit at a reverse proxy would close this.
- **The session token lives in browser storage.** Any script running on the page could read it. Vue escapes all rendered text, the app uses no `v-html` and no third-party scripts, but there is no Content-Security-Policy header yet.
- **One shared signing secret (HS256).** Anyone with `JWT_SECRET_KEY` can create tokens. Rotating it signs everyone out.
- **HTTP in the local setup.** A real deployment needs TLS at a reverse proxy.
- **No audit log** of approvals, role changes, or deletions.
- **Prompt injection.** A crafted question could try to steer the model. Answers are limited to approved content and gated, but model output cannot be fully guaranteed (OWASP Top 10 for LLM Applications, LLM01).

## Standards referenced

NIST SP 800-63B (Digital Identity Guidelines: Authentication), OWASP Authentication Cheat Sheet, OWASP API Security Top 10 (2023), OWASP Top 10 for LLM Applications, and the STRIDE threat model.