import pytest
from pydantic import ValidationError

from app.kanban import BoardPayload, default_board


def test_default_board_passes_validation() -> None:
    payload = BoardPayload.model_validate(default_board())
    assert len(payload.columns) == 5
    assert payload.cards["card-1"].title == "Align roadmap themes"


def test_rejects_unknown_column_ids() -> None:
    invalid_board = default_board()
    invalid_board["columns"][0]["id"] = "col-unknown"

    with pytest.raises(ValidationError):
        BoardPayload.model_validate(invalid_board)


def test_rejects_column_card_that_does_not_exist() -> None:
    invalid_board = default_board()
    invalid_board["columns"][0]["cardIds"].append("missing-card")

    with pytest.raises(ValidationError):
        BoardPayload.model_validate(invalid_board)


def test_rejects_orphaned_card() -> None:
    invalid_board = default_board()
    removed_card_id = invalid_board["columns"][0]["cardIds"].pop(0)
    assert removed_card_id == "card-1"

    with pytest.raises(ValidationError):
        BoardPayload.model_validate(invalid_board)
