from __future__ import annotations

import json
from typing import Any

from app.config import settings
from app.db import ensure_user_id, get_connection
from app.kanban import default_board


class BoardRepository:
    def get_board(self, username: str) -> dict[str, Any]:
        connection = None
        cursor = None
        try:
            connection = get_connection(database=settings.db_name)
            cursor = connection.cursor()

            user_id = ensure_user_id(cursor, username)

            cursor.execute("SELECT board_json FROM boards WHERE user_id = %s", (user_id,))
            row = cursor.fetchone()

            if row is None:
                board = default_board()
                cursor.execute(
                    "INSERT INTO boards (user_id, board_json) VALUES (%s, CAST(%s AS JSON))",
                    (user_id, json.dumps(board)),
                )
                connection.commit()
                return board

            connection.commit()
            return self._decode_board_json(row[0])
        finally:
            if cursor is not None:
                cursor.close()
            if connection is not None:
                connection.close()

    def save_board(self, username: str, board: dict[str, Any]) -> None:
        connection = None
        cursor = None
        serialized_board = json.dumps(board)
        try:
            connection = get_connection(database=settings.db_name)
            cursor = connection.cursor()

            user_id = ensure_user_id(cursor, username)

            cursor.execute(
                """
                INSERT INTO boards (user_id, board_json)
                VALUES (%s, CAST(%s AS JSON))
                ON DUPLICATE KEY UPDATE board_json = CAST(%s AS JSON)
                """,
                (user_id, serialized_board, serialized_board),
            )
            connection.commit()
        finally:
            if cursor is not None:
                cursor.close()
            if connection is not None:
                connection.close()

    @staticmethod
    def _decode_board_json(raw_value: Any) -> dict[str, Any]:
        if isinstance(raw_value, dict):
            return raw_value
        if isinstance(raw_value, (bytes, bytearray)):
            return json.loads(raw_value.decode("utf-8"))
        if isinstance(raw_value, str):
            return json.loads(raw_value)
        raise ValueError("Unexpected board_json value type.")
