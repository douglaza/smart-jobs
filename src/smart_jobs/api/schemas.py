from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl, model_validator


class ProfileCreate(BaseModel):
    consented: bool

    @model_validator(mode="after")
    def require_consent(self) -> "ProfileCreate":
        if not self.consented:
            raise ValueError("Cadastro exige consentimento explicito")
        return self


class ProfileRead(BaseModel):
    id: UUID
    consented: bool
    created_at: datetime
    updated_at: datetime


class FactCreate(BaseModel):
    fact: Annotated[str, Field(min_length=3, max_length=5000)]
    source: Annotated[str, Field(min_length=3, max_length=500)]
    evidence: Annotated[str, Field(min_length=3, max_length=10000)]
    confirmed: bool = False


class FactRead(FactCreate):
    id: UUID
    created_at: datetime


class PreferenceWrite(BaseModel):
    roles: list[str] = Field(default_factory=list)
    seniorities: list[str] = Field(default_factory=list)
    modalities: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    salary_min: Decimal | None = Field(default=None, ge=0)
    salary_currency: str | None = Field(default=None, min_length=3, max_length=3)
    salary_period: str | None = None
    salary_regime: str | None = None
    cutoff: int | None = Field(default=None, ge=0, le=100)
    eliminatory_criteria: list[str] = Field(default_factory=list)


class PreferenceRead(PreferenceWrite):
    id: UUID
    version: int
    updated_at: datetime


class OpportunityCreate(BaseModel):
    company: Annotated[str, Field(min_length=1, max_length=300)]
    title: Annotated[str, Field(min_length=1, max_length=300)]
    description: Annotated[str, Field(min_length=1, max_length=100000)]
    location: str | None = Field(default=None, max_length=300)
    modality: str | None = Field(default=None, max_length=30)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    salary_min: Decimal | None = Field(default=None, ge=0)
    salary_max: Decimal | None = Field(default=None, ge=0)
    salary_period: str | None = Field(default=None, max_length=20)
    salary_regime: str | None = Field(default=None, max_length=20)
    source_url: HttpUrl | None = None

    @model_validator(mode="after")
    def validate_salary_range(self) -> "OpportunityCreate":
        if (
            self.salary_min is not None
            and self.salary_max is not None
            and self.salary_min > self.salary_max
        ):
            raise ValueError("salary_min nao pode ser maior que salary_max")
        return self


class OpportunityRead(OpportunityCreate):
    id: UUID
    state: str
    created_at: datetime


class DraftClaim(BaseModel):
    statement: Annotated[str, Field(min_length=1, max_length=2000)]
    fact_ids: Annotated[list[UUID], Field(min_length=1, max_length=100)]

    @model_validator(mode="after")
    def require_unique_fact_ids(self) -> "DraftClaim":
        if len(set(self.fact_ids)) != len(self.fact_ids):
            raise ValueError("fact_ids nao podem conter duplicatas")
        return self


class DraftCreate(BaseModel):
    content: Annotated[str, Field(min_length=1, max_length=50000)]
    claims: Annotated[list[DraftClaim], Field(min_length=1, max_length=100)]

    @model_validator(mode="after")
    def require_claims_in_content(self) -> "DraftCreate":
        normalized_content = self.content.casefold()
        if any(
            claim.statement.casefold() not in normalized_content
            for claim in self.claims
        ):
            raise ValueError("Cada afirmacao rastreada precisa aparecer no conteudo")
        return self


class DraftClaimRead(BaseModel):
    statement: str
    fact_ids: list[UUID]


class DraftRevisionRead(BaseModel):
    id: UUID
    draft_id: UUID
    version: int
    content: str
    fact_ids: list[UUID]
    claims: list[DraftClaimRead]
    content_hash: str
    approved_for_manual_application: bool
    created_at: datetime


class DraftRead(BaseModel):
    id: UUID
    opportunity_id: UUID
    revisions: list[DraftRevisionRead]
    created_at: datetime


class DraftApprovalWrite(BaseModel):
    expected_content_hash: Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
    decision: Literal["approved", "rejected"]


class DraftApprovalRead(BaseModel):
    id: UUID
    revision_id: UUID
    action: str
    decision: str
    content_hash: str
    created_at: datetime


class ApplicationCreate(BaseModel):
    opportunity_id: UUID
    draft_revision_id: UUID | None = None


class ApplicationTransition(BaseModel):
    target_state: Literal[
        "awaiting_approval",
        "approved",
        "sent",
        "test",
        "interview",
        "offer",
        "rejected",
        "withdrawn",
        "accepted",
        "declined",
    ]
    draft_revision_id: UUID | None = None
    manual_submission_confirmed: bool = False


class ApplicationRead(BaseModel):
    id: UUID
    opportunity_id: UUID
    draft_revision_id: UUID | None
    state: str
    created_at: datetime
    updated_at: datetime


class ApplicationEventRead(BaseModel):
    id: UUID
    application_id: UUID
    from_state: str | None
    to_state: str
    source: str
    confirmation: str | None
    created_at: datetime
