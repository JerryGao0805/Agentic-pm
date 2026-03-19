import json
from typing import Any

import app.repositories.board_repository as repository_module
from app.kanban import default_board
from app.repositories.board_repository import BoardRepository


class RecordingCursor:
    def __init__(self, fetch_values: list[Any] | None = None) -> None:
        self.statements: list[tuple[str, Any]] = []
        self._fetch_values = fetch_values or []
        self._fetch_index = 0

    def execute(self, statement: str, params: Any = None) -> None:
        self.statements.append((" ".join(statement.split()), params))

    def fetchone(self) -> Any:
        if self._fetch_index < len(self._fetch_values):
            value = self._fetch_values[self._fetch_index]
            self._fetch_index += 1
            return value
        return None

    def close(self) -> None:
        return None


class RecordingConnection:
    def __init__(self, cursor: RecordingCursor) -> None:
        self._cursor = cursor
        self.commit_count = 0

    def cursor(self) -> RecordingCursor:
        return self._cursor

    def commit(self) -> None:
        self.commit_count += 1

    def close(self) -> None:
        return None


def test_get_board_returns_existing_payload(monkeypatch) -> None:
    board = default_board()
    cursor = RecordingCursor(fetch_values=[(json.dumps(board),)])
    connection = RecordingConnection(cursor)

    monkeypatch.setattr(repository_module, "get_connection", lambda database=None: connection)
    monkeypatch.setattr(repository_module, "ensure_user_id", lambda _cursor, _username: 21)

    repository = BoardRepository()
    loaded = repository.get_board("user")

    assert loaded == board
    assert all("INSERT INTO boards" not in statement for statement, _ in cursor.statements)


def test_get_board_seeds_default_board_when_missing(monkeypatch) -> None:
    cursor = RecordingCursor(fetch_values=[None])
    connection = RecordingConnection(cursor)

    monkeypatch.setattr(repository_module, "get_connection", lambda database=None: connection)
    monkeypatch.setattr(repository_module, "ensure_user_id", lambda _cursor, _username: 21)

    repository = BoardRepository()
    loaded = repository.get_board("user")

    assert loaded == default_board()
    assert any("INSERT INTO boards" in statement for statement, _ in cursor.statements)


def test_save_board_uses_upsert(monkeypatch) -> None:
    board = default_board()
    cursor = RecordingCursor()
    connection = RecordingConnection(cursor)

    monkeypatch.setattr(repository_module, "get_connection", lambda database=None: connection)
    monkeypatch.setattr(repository_module, "ensure_user_id", lambda _cursor, _username: 21)

    repository = BoardRepository()
    repository.save_board("user", board)

    assert any("ON DUPLICATE KEY UPDATE" in statement for statement, _ in cursor.statements)
    assert connection.commit_count == 1
