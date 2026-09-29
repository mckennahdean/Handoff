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