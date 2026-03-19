from __future__ import annotations

from typing import Literal

from app.repositories.chat_repository import ChatRepository

ChatRole = Literal["user", "assistant"]


class ChatService:
    def __init__(self, repository: ChatRepository | None = None) -> None:
        self._repository = repository or ChatRepository()

    def list_messages(self, username: str) -> list[dict[str, str]]:
        return self._repository.list_messages(username)

    def append_message(self, username: str, role: ChatRole, content: str) -> None:
        normalized_content = content.strip()
        if not normalized_content:
            raise ValueError("Chat message cannot be empty.")
        self._repository.append_message(username, role, normalized_content)
