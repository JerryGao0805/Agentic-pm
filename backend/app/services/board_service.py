from __future__ import annotations

from typing import Any

from app.kanban import BoardPayload
from app.repositories.board_repository import BoardRepository


class BoardService:
    def __init__(self, repository: BoardRepository | None = None) -> None:
        self._repository = repository or BoardRepository()

    def get_board(self, username: str) -> dict[str, Any]:
        board = self._repository.get_board(username)
        validated_board = BoardPayload.model_validate(board)
        return validated_board.model_dump()

    def save_board(self, username: str, board: BoardPayload | dict[str, Any]) -> dict[str, Any]:
        validated_board = BoardPayload.model_validate(board)
        board_payload = validated_board.model_dump()
        self._repository.save_board(username, board_payload)
        return board_payload
