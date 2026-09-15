# Tests

Application tests for Handoff.

Backend tests currently live in `backend/test_main.py` and are executed via pytest:

    python -m pytest backend/test_main.py -v

The `backend/test.py` and `backend/test_embedding.py` files are development scripts and are excluded from the CI test run.

CI automatically runs the backend test suite on every pull request to `main`. See `.github/workflows/ci.yml`.
