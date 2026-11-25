from datetime import datetime
from decimal import Decimal
from typing import Annotated
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
