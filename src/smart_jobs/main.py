import hashlib
import json
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from smart_jobs.api.schemas import (
    FactCreate,
    FactRead,
    OpportunityCreate,
    OpportunityRead,
    PreferenceRead,
    PreferenceWrite,
    ProfileCreate,
    ProfileRead,
)
from smart_jobs.config import settings
from smart_jobs.domain.scoring import CONFIRMED_RUBRIC
from smart_jobs.persistence.database import database_session, engine
from smart_jobs.persistence.models import (
    Assessment,
    Opportunity,
    Preference,
    Profile,
    ProfileFact,
)

app = FastAPI(title="Smart Jobs", version="0.1.0")


@app.get("/api/v1/health/live")
def health_live() -> dict[str, str]:
    return {"status": "alive"}


@app.get("/api/v1/health/ready")
def health_ready(response: Response) -> dict[str, str]:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "database_unavailable"}

    return {"status": "ready"}


SessionDep = Annotated[Session, Depends(database_session)]


@app.post("/api/v1/profile", response_model=ProfileRead)
def create_profile(payload: ProfileCreate, session: SessionDep) -> Profile:
    profile = session.scalar(select(Profile).order_by(Profile.created_at).limit(1))
    if profile is None:
        profile = Profile(consented=payload.consented)
        session.add(profile)
        session.commit()
        session.refresh(profile)
    return profile


@app.get("/api/v1/profile", response_model=ProfileRead)
def get_profile(session: SessionDep) -> Profile:
    profile = session.scalar(select(Profile).order_by(Profile.created_at).limit(1))
    if profile is None:
        raise HTTPException(status_code=404, detail="Perfil nao cadastrado")
    return profile


@app.post("/api/v1/profile/facts", response_model=FactRead)
def create_fact(payload: FactCreate, session: SessionDep) -> ProfileFact:
    fact = ProfileFact(
        fact=payload.fact,
        source=payload.source,
        evidence=payload.evidence,
        confirmed=payload.confirmed,
    )
    session.add(fact)
    session.commit()
    session.refresh(fact)
    return fact


@app.get("/api/v1/profile/facts", response_model=list[FactRead])
def list_facts(session: SessionDep) -> list[ProfileFact]:
    return list(session.scalars(select(ProfileFact).order_by(ProfileFact.created_at)))


@app.put("/api/v1/preferences", response_model=PreferenceRead)
def write_preferences(payload: PreferenceWrite, session: SessionDep) -> Preference:
    preference = session.scalar(
        select(Preference).order_by(Preference.version.desc()).limit(1)
    )
    if preference is None:
        preference = Preference(version=1)
    else:
        preference = Preference(version=preference.version + 1)
    preference.roles = payload.roles
    preference.seniorities = payload.seniorities
    preference.modalities = payload.modalities
    preference.locations = payload.locations
    preference.salary_min = payload.salary_min
    preference.salary_currency = (
        payload.salary_currency.upper() if payload.salary_currency else None
    )
    preference.salary_period = payload.salary_period
    preference.salary_regime = payload.salary_regime
    preference.cutoff = payload.cutoff
    preference.eliminatory_criteria = payload.eliminatory_criteria
    session.add(preference)
    session.commit()
    session.refresh(preference)
    return preference


@app.get("/api/v1/preferences", response_model=PreferenceRead)
def get_preferences(session: SessionDep) -> Preference:
    preference = session.scalar(
        select(Preference).order_by(Preference.version.desc()).limit(1)
    )
    if preference is None:
        raise HTTPException(status_code=404, detail="Preferencias nao configuradas")
    return preference


def opportunity_fingerprint(payload: OpportunityCreate) -> str:
    canonical = payload.model_dump(mode="json", exclude_none=True)
    source_url = canonical.pop("source_url", None)
    if source_url:
        canonical["source_url"] = str(source_url).rstrip("/")
    encoded = json.dumps(
        canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


@app.post(
    "/api/v1/opportunities",
    response_model=OpportunityRead,
    status_code=status.HTTP_201_CREATED,
)
def create_opportunity(payload: OpportunityCreate, session: SessionDep) -> Opportunity:
    opportunity = Opportunity(
        company=payload.company,
        title=payload.title,
        description=payload.description,
        location=payload.location,
        modality=payload.modality,
        currency=payload.currency.upper() if payload.currency else None,
        salary_min=payload.salary_min,
        salary_max=payload.salary_max,
        salary_period=payload.salary_period,
        salary_regime=payload.salary_regime,
        source_url=str(payload.source_url).rstrip("/") if payload.source_url else None,
        fingerprint=opportunity_fingerprint(payload),
    )
    session.add(opportunity)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        existing = session.scalar(
            select(Opportunity).where(
                Opportunity.fingerprint == opportunity.fingerprint
            )
        )
        if existing:
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "duplicate_opportunity",
                    "existing_id": str(existing.id),
                },
            ) from exc
        raise
    session.refresh(opportunity)
    return opportunity


@app.get("/api/v1/opportunities", response_model=list[OpportunityRead])
def list_opportunities(
    session: SessionDep,
    state: str | None = None,
    query: Annotated[str | None, Query(max_length=300)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[Opportunity]:
    statement = select(Opportunity).order_by(
        Opportunity.created_at.desc(), Opportunity.id
    )
    if state:
        statement = statement.where(Opportunity.state == state)
    if query:
        statement = statement.where(
            Opportunity.title.ilike(f"%{query}%")
            | Opportunity.company.ilike(f"%{query}%")
        )
    return list(session.scalars(statement.offset(offset).limit(limit)))


@app.get("/api/v1/opportunities/{opportunity_id}", response_model=OpportunityRead)
def get_opportunity(opportunity_id: str, session: SessionDep) -> Opportunity:
    from uuid import UUID

    try:
        parsed_id = UUID(opportunity_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Vaga nao encontrada") from exc
    opportunity = session.get(Opportunity, parsed_id)
    if opportunity is None:
        raise HTTPException(status_code=404, detail="Vaga nao encontrada")
    return opportunity


@app.post("/api/v1/opportunities/{opportunity_id}/assessments")
def request_assessment(
    opportunity_id: str,
    session: SessionDep,
) -> dict[str, object]:
    from uuid import UUID

    try:
        parsed_id = UUID(opportunity_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Vaga nao encontrada") from exc

    if session.get(Opportunity, parsed_id) is None:
        raise HTTPException(status_code=404, detail="Vaga nao encontrada")

    assessment = Assessment(
        opportunity_id=parsed_id,
        status="blocked",
        rubric_version=CONFIRMED_RUBRIC.version,
        cutoff=65,
        result=None,
        error_code="real_call_budget_pending",
        model=settings.ollama_model,
    )
    session.add(assessment)
    session.commit()
    session.refresh(assessment)
    return {
        "id": str(assessment.id),
        "status": "blocked",
        "error_code": "real_call_budget_pending",
    }


@app.get("/api/v1/opportunities/{opportunity_id}/assessments")
def list_assessments(
    opportunity_id: str,
    session: SessionDep,
) -> list[dict[str, object]]:
    from uuid import UUID

    try:
        parsed_id = UUID(opportunity_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Vaga nao encontrada") from exc

    assessments = session.scalars(
        select(Assessment)
        .where(Assessment.opportunity_id == parsed_id)
        .order_by(Assessment.created_at.desc())
    )
    return [
        {
            "id": str(item.id),
            "status": item.status,
            "rubric_version": item.rubric_version,
            "cutoff": item.cutoff,
            "error_code": item.error_code,
            "model": item.model,
            "created_at": item.created_at.isoformat(),
        }
        for item in assessments
    ]
