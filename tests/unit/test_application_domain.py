import pytest
from pydantic import ValidationError

from smart_jobs.api.schemas import DraftCreate
from smart_jobs.domain.applications import (
    InvalidApplicationTransition,
    validate_application_transition,
)
from smart_jobs.domain.drafts import draft_content_hash


def test_submission_requires_human_confirmation() -> None:
    with pytest.raises(InvalidApplicationTransition):
        validate_application_transition(
            "approved",
            "sent",
            manual_submission_confirmed=False,
        )

    validate_application_transition(
        "approved",
        "sent",
        manual_submission_confirmed=True,
    )


def test_terminal_application_state_cannot_transition() -> None:
    with pytest.raises(InvalidApplicationTransition):
        validate_application_transition(
            "withdrawn",
            "interview",
            manual_submission_confirmed=False,
        )


def test_draft_hash_covers_content_and_fact_references() -> None:
    fact_id = "3f29eab0-d8a2-4c15-96d2-668fc570b68a"

    baseline = draft_content_hash(
        "Afirmacao confirmada",
        [("Afirmacao confirmada", [fact_id])],
    )
    assert baseline == draft_content_hash(
        "Afirmacao confirmada",
        [("Afirmacao confirmada", [fact_id])],
    )
    assert baseline != draft_content_hash(
        "Conteudo alterado",
        [("Afirmacao confirmada", [fact_id])],
    )
    assert baseline != draft_content_hash(
        "Afirmacao confirmada",
        [("Afirmacao confirmada", [])],
    )


def test_draft_claim_must_appear_in_content() -> None:
    from uuid import uuid4

    with pytest.raises(ValidationError):
        DraftCreate.model_validate(
            {
                "content": "Texto sem a afirmacao rastreada.",
                "claims": [
                    {
                        "statement": "Afirmacao ausente.",
                        "fact_ids": [uuid4()],
                    }
                ],
            }
        )
