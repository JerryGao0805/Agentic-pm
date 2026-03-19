from typing import Any

import pytest
from pydantic import ValidationError

from app.kanban import default_board
from app.services.board_service import BoardService


class FakeBoardRepository:
    def __init__(self) -> None:
        self.saved_by_username: dict[str, dict[str, Any]] = {}

    def get_board(self, username: str) -> dict[str, Any]:
        return self.saved_by_username.get(username, default_board())

    def save_board(self, username: str, board: dict[str, Any]) -> None:
        self.saved_by_username[username] = board


def test_get_board_validates_repository_data() -> None:
    repository = FakeBoardRepository()
    service = BoardService(repository=repository)

    board = service.get_board("user")

    assert board["columns"][0]["id"] == "col-backlog"
    assert board["cards"]["card-1"]["title"] == "Align roadmap themes"


def test_save_board_rejects_invalid_payload() -> None:
    repository = FakeBoardRepository()
    service = BoardService(repository=repository)
    invalid_board = default_board()
    invalid_board["columns"][0]["id"] = "not-fixed"

    with pytest.raises(ValidationError):
        service.save_board("user", invalid_board)


def test_save_board_persists_valid_board() -> None:
    repository = FakeBoardRepository()
    service = BoardService(repository=repository)
    board = default_board()
    board["columns"][0]["title"] = "Ideas"

    saved = service.save_board("user", board)

    assert saved["columns"][0]["title"] == "Ideas"
    assert repository.saved_by_username["user"]["columns"][0]["title"] == "Ideas"
