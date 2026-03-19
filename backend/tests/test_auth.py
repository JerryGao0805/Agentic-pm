from pathlib import Path
import sys

from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.main import app


def test_session_is_unauthenticated_by_default():
    with TestClient(app) as client:
        response = client.get("/api/auth/session")

    assert response.status_code == 200
    assert response.json() == {"authenticated": False, "username": None}


def test_login_success_sets_authenticated_session():
    with TestClient(app) as client:
        login_response = client.post(
            "/api/auth/login",
            json={"username": "user", "password": "password"},
        )
        session_response = client.get("/api/auth/session")

    assert login_response.status_code == 200
    assert login_response.json() == {"authenticated": True, "username": "user"}
    assert session_response.status_code == 200
    assert session_response.json() == {"authenticated": True, "username": "user"}


def test_login_failure_returns_401():
    with TestClient(app) as client:
        response = client.post(
            "/api/auth/login",
            json={"username": "user", "password": "wrong"},
        )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials."}


def test_logout_clears_authenticated_session():
    with TestClient(app) as client:
        client.post("/api/auth/login", json={"username": "user", "password": "password"})
        logout_response = client.post("/api/auth/logout")
        session_response = client.get("/api/auth/session")

    assert logout_response.status_code == 200
    assert logout_response.json() == {"authenticated": False, "username": None}
    assert session_response.status_code == 200
    assert session_response.json() == {"authenticated": False, "username": None}
