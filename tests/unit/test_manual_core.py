from decimal import Decimal

import pytest
from pydantic import HttpUrl, ValidationError

from smart_jobs.api.schemas import OpportunityCreate
from smart_jobs.main import opportunity_fingerprint


def test_opportunity_salary_range_is_validated() -> None:
    with pytest.raises(ValidationError):
        OpportunityCreate(
            company="Empresa",
            title="Cargo",
            description="Descricao",
            salary_min=Decimal("10000"),
            salary_max=Decimal("5000"),
        )


def test_exact_duplicate_has_the_same_fingerprint() -> None:
    payload = OpportunityCreate(
        company="Empresa",
        title="Cargo",
        description="Descricao",
        source_url=HttpUrl("https://example.com/vaga"),
    )

    assert len(opportunity_fingerprint(payload)) == 64
    assert opportunity_fingerprint(payload) == opportunity_fingerprint(payload)
