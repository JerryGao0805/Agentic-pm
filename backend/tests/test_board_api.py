from typing import Any

from fastapi.testclient import TestClient
from mysql.connector import Error as MySQLError

import app.main as main_module
from app.config import settings
from app.kanban import default_board


class FailingBoardService:
    def get_board(self, username: str) -> dict[str, Any]:
        raise MySQLError("Connection refused")

    def save_board(self, username: str, board: Any) -> dict[str, Any]:
        raise MySQLError("Connection refused")


class FakeBoardService:
    def __init__(self) -> None:
        self.saved_payload: dict[str, Any] | None = None

    def get_board(self, username: str) -> dict[str, Any]:
        board = default_board()
        board["columns"][0]["title"] = f"Backlog ({username})"
        return board

    def save_board(self, username: str, board: Any) -> dict[str, Any]:
        payload = board.model_dump() if hasattr(board, "model_dump") else board
        self.saved_payload = payload
        return payload


def test_get_board_requires_authentication(monkeypatch) -> None:
    monkeypatch.setattr(main_module, "board_service", FakeBoardService())

    with TestClient(main_module.app) as client:
        response = client.get("/api/board")

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required."}


def test_get_board_returns_board_for_authenticated_user(monkeypatch) -> None:
    monkeypatch.setattr(main_module, "board_service", FakeBoardService())

    with TestClient(main_module.app) as client:
        client.cookies.set(settings.auth_cookie_name, settings.sign_session(settings.auth_username))
        response = client.get("/api/board")

    assert response.status_code == 200
    payload = response.json()
    assert payload["columns"][0]["id"] == "col-backlog"
    assert payload["columns"][0]["title"] == f"Backlog ({settings.auth_username})"


def test_put_board_rejects_invalid_structure(monkeypatch) -> None:
    fake_service = FakeBoardService()
    monkeypatch.setattr(main_module, "board_service", fake_service)

    invalid_board = default_board()
    invalid_board["columns"][0]["id"] = "col-unknown"

    with TestClient(main_module.app) as client:
        client.cookies.set(settings.auth_cookie_name, settings.sign_session(settings.auth_username))
        response = client.put("/api/board", json=invalid_board)

    assert response.status_code == 422
    assert fake_service.saved_payload is None


def test_put_board_saves_valid_payload(monkeypatch) -> None:
    fake_service = FakeBoardService()
    monkeypatch.setattr(main_module, "board_service", fake_service)

    board = default_board()
    board["columns"][0]["title"] = "Ideas"

    with TestClient(main_module.app) as client:
        client.cookies.set(settings.auth_cookie_name, settings.sign_session(settings.auth_username))
        response = client.put("/api/board", json=board)

    assert response.status_code == 200
    assert response.json()["columns"][0]["title"] == "Ideas"
    assert fake_service.saved_payload is not None
    assert fake_service.saved_payload["columns"][0]["title"] == "Ideas"


def test_get_board_returns_503_on_database_error(monkeypatch) -> None:
    monkeypatch.setattr(main_module, "board_service", FailingBoardService())

    with TestClient(main_module.app, raise_server_exceptions=False) as client:
        client.cookies.set(settings.auth_cookie_name, settings.sign_session(settings.auth_username))
        response = client.get("/api/board")

    assert response.status_code == 503
    assert response.json() == {"detail": "Database temporarily unavailable."}


def test_put_board_returns_503_on_database_error(monkeypatch) -> None:
    monkeypatch.setattr(main_module, "board_service", FailingBoardService())

    board = default_board()

    with TestClient(main_module.app, raise_server_exceptions=False) as client:
        client.cookies.set(settings.auth_cookie_name, settings.sign_session(settings.auth_username))
        response = client.put("/api/board", json=board)

    assert response.status_code == 503
    assert response.json() == {"detail": "Database temporarily unavailable."}
