"""Every API route must reject requests without a login token.

Auth in FastAPI is opt-in per route, so a new route can silently
forget it. This test checks every route the app has, including
routes added later, instead of one hand-written test per route.
"""
import re

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

import backend.main as main_module

client = TestClient(main_module.app)

# Routes anyone may call: the health check, how you get a token,
# and account recovery (which proves identity with a recovery code).
PUBLIC_ROUTES = {
    ("GET", "/"),
    ("GET", "/api/auth/setup-status"),
    ("POST", "/api/auth/signup"),
    ("POST", "/api/auth/login"),
    ("POST", "/api/auth/recover"),
}


@pytest.fixture(autouse=True)
def nobody_logged_in():
    # Other test files log in a fake user; this test needs nobody.
    saved = dict(main_module.app.dependency_overrides)
    main_module.app.dependency_overrides.clear()
    yield
    main_module.app.dependency_overrides.update(saved)


def test_every_route_except_public_ones_requires_login():
    unprotected = []

    for route in main_module.app.routes:
        if not isinstance(route, APIRoute):
            continue

        for method in route.methods:
            if (method, route.path) in PUBLIC_ROUTES:
                continue

            # Fill path parameters like {procedure_id} with a dummy id.
            path = re.sub(r"\{[^}]+\}", "1", route.path)
            response = client.request(method, path)

            if response.status_code != 401:
                unprotected.append(f"{method} {route.path}")

    assert unprotected == []