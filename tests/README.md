# Tests

Handoff's automated tests live next to the code in `backend/`:

| File | What it covers |
|---|---|
| `test_main.py` | Procedure, question, and AI error routes, with the AI replaced by a fake |
| `test_auth.py` | Passwords, tokens, signup, login, owner approval, recovery codes, and role rules |
| `test_gaps.py` | Knowledge gap routes and logic |
| `test_route_guards.py` | Every route except the public ones requires a login, including routes added later |
| `test_integration.py` | The real database code against PostgreSQL and pgvector: retrieval, knowledge gaps, migrations, and account security |

Run them from the repository root with the virtual environment active:

    python -m pytest backend/ -v --ignore=backend/test.py --ignore=backend/test_embedding.py

Integration tests need a separate test database and skip themselves without one; see [Integration tests](../docs/INSTALL.md#integration-tests) in the install guide. `backend/test.py` and `backend/test_embedding.py` are old development scripts, not part of the suite.

CI runs the full suite, including the integration tests against a real PostgreSQL container, on every pull request, and fails if line coverage drops below 70%. See `.github/workflows/ci.yml`.

## Test strategy

This section is Handoff's test plan, kept deliberately lightweight for a three-person team. It follows the risk-based approach of IEEE 29119 (software testing), tailored to short iterations: tests are written with the change they cover, and CI runs every automated level on every pull request.

### Scope and priorities

Testing effort follows risk. The areas where a defect would do the most harm get the deepest coverage:

- **Authentication and access control:** password rules, tokens, owner approval, login throttling, recovery codes, ending sessions after a password reset, and role rules. A defect here exposes a business's data.
- **The Approval Gate:** unapproved drafts must never be searchable or visible to employees.
- **The AI guardrails:** the insert-only merge check, abstention when retrieval is not confident, and honest error responses when the AI service fails.
- **Knowledge gaps:** grouping, auto-resolve on approval, dismissal, and reopening when a procedure is deleted.

### Test levels

| Level | What it checks | Where |
|---|---|---|
| Unit | Routes and logic, with the AI replaced by a fake client so tests are fast, free, and repeatable | `test_main.py`, `test_auth.py`, `test_gaps.py` |
| Route protection | Every route except the public ones requires a login, including routes added later | `test_route_guards.py` |
| Integration | The real database code against PostgreSQL and pgvector, in a separate test database | `test_integration.py` |
| System smoke test | The full Docker stack starts healthy, and the API and web app respond | CI job "Docker build, smoke test, and publish" |
| Static checks | Frontend lint and production build | CI job "Frontend lint and build" |
| Manual walkthrough | A scripted end-to-end run of the user guide's workflows in the Docker stack: signup and approval, recovery codes, capturing a procedure with AI gap questions, approval, and the knowledge gap loop. The screenshots in `docs/images/` come from the run before v1.0.0 | By hand, before a release |
| AI quality | Retrieval, answers, abstention, and question grouping, scored against 43 labeled questions | [`evaluation/`](../evaluation/README.md), offline |

### Entry and exit criteria

- A change is ready for review when the suite passes locally and CI is green on its pull request.
- A pull request merges only when all three CI jobs pass, including the 70% line coverage floor, and a teammate has approved it.
- A release is ready when the suite passes on `main` (110 tests and 89% line coverage at v1.0.0), the smoke-tested images are published, and the manual walkthrough is complete.

### Traceability

Each threat in [SECURITY.md](../SECURITY.md) names the control that addresses it and the test that proves it, so every security requirement traces to a test. Every performance number in the project README traces to a committed results file in [`evaluation/results/`](../evaluation/results/).

### Not covered, and why

- **Automated frontend tests.** The server enforces every rule (login, roles, and the Approval Gate), so a frontend defect can show the wrong screen but cannot bypass a rule. The frontend is checked by lint and a production build on every pull request, and by the manual walkthrough. Component tests (for example, with Vitest) are future work.
- **Load testing.** Handoff's throughput is limited by the AI provider's free-tier quota rather than by its own server, so a load test would mainly measure the provider. Response times were measured instead under two real load conditions (see [evaluation/README.md](../evaluation/README.md)). Load testing belongs before any deployment that serves several businesses on a paid tier.
- **A held-out evaluation set.** The answer threshold was chosen using the same 43 questions it is scored on. The app's live scores matched the offline predictions, but questions written by someone who has not seen the scores would give an independent check.