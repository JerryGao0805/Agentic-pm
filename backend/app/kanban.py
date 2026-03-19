from __future__ import annotations

from copy import deepcopy
from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator

FIXED_COLUMN_IDS = (
    "col-backlog",
    "col-discovery",
    "col-progress",
    "col-review",
    "col-done",
)


class CardPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    details: str


class ColumnPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    cardIds: list[str]


class BoardPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    columns: list[ColumnPayload]
    cards: dict[str, CardPayload]

    @model_validator(mode="after")
    def _validate_kanban_structure(self) -> BoardPayload:
        column_ids = [column.id for column in self.columns]
        unique_column_ids = set(column_ids)

        if len(column_ids) != len(unique_column_ids):
            raise ValueError("Column IDs must be unique.")

        if unique_column_ids != set(FIXED_COLUMN_IDS):
            raise ValueError(
                "Board must include exactly the fixed column IDs: "
                + ", ".join(FIXED_COLUMN_IDS)
            )

        all_column_card_ids: list[str] = []
        for column in self.columns:
            all_column_card_ids.extend(column.cardIds)

        if len(all_column_card_ids) != len(set(all_column_card_ids)):
            raise ValueError("Each card ID must appear in at most one column.")

        unknown_cards = [card_id for card_id in all_column_card_ids if card_id not in self.cards]
        if unknown_cards:
            raise ValueError("Columns reference unknown card IDs.")

        if set(self.cards.keys()) != set(all_column_card_ids):
            raise ValueError("Every card must appear in exactly one column.")

        for card_key, card in self.cards.items():
            if card_key != card.id:
                raise ValueError("Card map keys must match each card object's id.")

        return self


INITIAL_BOARD_DATA: dict[str, Any] = {
    "columns": [
        {"id": "col-backlog", "title": "Backlog", "cardIds": ["card-1", "card-2"]},
        {"id": "col-discovery", "title": "Discovery", "cardIds": ["card-3"]},
        {
            "id": "col-progress",
            "title": "In Progress",
            "cardIds": ["card-4", "card-5"],
        },
        {"id": "col-review", "title": "Review", "cardIds": ["card-6"]},
        {"id": "col-done", "title": "Done", "cardIds": ["card-7", "card-8"]},
    ],
    "cards": {
        "card-1": {
            "id": "card-1",
            "title": "Align roadmap themes",
            "details": "Draft quarterly themes with impact statements and metrics.",
        },
        "card-2": {
            "id": "card-2",
            "title": "Gather customer signals",
            "details": "Review support tags, sales notes, and churn feedback.",
        },
        "card-3": {
            "id": "card-3",
            "title": "Prototype analytics view",
            "details": "Sketch initial dashboard layout and key drill-downs.",
        },
        "card-4": {
            "id": "card-4",
            "title": "Refine status language",
            "details": "Standardize column labels and tone across the board.",
        },
        "card-5": {
            "id": "card-5",
            "title": "Design card layout",
            "details": "Add hierarchy and spacing for scanning dense lists.",
        },
        "card-6": {
            "id": "card-6",
            "title": "QA micro-interactions",
            "details": "Verify hover, focus, and loading states.",
        },
        "card-7": {
            "id": "card-7",
            "title": "Ship marketing page",
            "details": "Final copy approved and asset pack delivered.",
        },
        "card-8": {
            "id": "card-8",
            "title": "Close onboarding sprint",
            "details": "Document release notes and share internally.",
        },
    },
}


def default_board() -> dict[str, Any]:
    return deepcopy(INITIAL_BOARD_DATA)
