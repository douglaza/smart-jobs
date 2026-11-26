import hashlib
import json
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from smart_jobs.api.schemas import (
    ApplicationCreate,
    ApplicationEventRead,
    ApplicationRead,
    ApplicationTransition,
    DraftApprovalRead,
    DraftApprovalWrite,
    DraftClaimRead,
    DraftCreate,
    DraftRead,
    DraftRevisionRead,
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
from smart_jobs.domain.applications import (
    InvalidApplicationTransition,
    validate_application_transition,
)
from smart_jobs.domain.drafts import draft_content_hash
from smart_jobs.domain.scoring import CONFIRMED_RUBRIC
from smart_jobs.persistence.database import database_session, engine
from smart_jobs.persistence.models import (
    Application,
    ApplicationEvent,
    Assessment,
    Draft,
    DraftApproval,
    DraftRevision,
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
    consented_profile = session.scalar(
        select(Profile.id)
        .where(Profile.consented.is_(True))
        .order_by(Profile.created_at)
        .limit(1)
    )
    if consented_profile is None:
        raise HTTPException(
            status_code=409,
            detail="Registre consentimento explicito antes de adicionar fatos",
        )
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


def _require_confirmed_facts(session: Session, fact_ids: list[UUID]) -> None:
    confirmed_ids = set(
        session.scalars(
            select(ProfileFact.id).where(
                ProfileFact.id.in_(fact_ids),
                ProfileFact.confirmed.is_(True),
            )
        )
    )
    if confirmed_ids != set(fact_ids):
        raise HTTPException(
            status_code=422,
            detail="Rascunhos so podem referenciar fatos existentes e confirmados",
        )


def _draft_revision_read(
    revision: DraftRevision,
    *,
    approved: bool,
) -> DraftRevisionRead:
    claims: list[DraftClaimRead] = []
    for claim in revision.claims:
        statement = claim["statement"]
        fact_ids = claim["fact_ids"]
        if not isinstance(statement, str) or not isinstance(fact_ids, list):
            raise RuntimeError("Persisted draft claim has an invalid shape")
        if any(not isinstance(fact_id, str) for fact_id in fact_ids):
            raise RuntimeError("Persisted draft fact reference has an invalid shape")
        claims.append(
            DraftClaimRead(
                statement=statement,
                fact_ids=[UUID(fact_id) for fact_id in fact_ids],
            )
        )
    return DraftRevisionRead(
        id=revision.id,
        draft_id=revision.draft_id,
        version=revision.version,
        content=revision.content,
        fact_ids=[UUID(fact_id) for fact_id in revision.fact_ids],
        claims=claims,
        content_hash=revision.content_hash,
        approved_for_manual_application=approved,
        created_at=revision.created_at,
    )


def _draft_claim_values(
    payload: DraftCreate,
) -> tuple[list[str], list[dict[str, str | list[str]]]]:
    fact_ids = list(
        dict.fromkeys(
            str(fact_id) for claim in payload.claims for fact_id in claim.fact_ids
        )
    )
    claims: list[dict[str, str | list[str]]] = []
    for claim in payload.claims:
        claims.append(
            {
                "statement": claim.statement,
                "fact_ids": [str(fact_id) for fact_id in claim.fact_ids],
            }
        )
    return fact_ids, claims


def _draft_hash_input(payload: DraftCreate) -> list[tuple[str, list[str]]]:
    return [
        (claim.statement, [str(fact_id) for fact_id in claim.fact_ids])
        for claim in payload.claims
    ]


@app.post(
    "/api/v1/opportunities/{opportunity_id}/drafts",
    response_model=DraftRead,
    status_code=status.HTTP_201_CREATED,
)
def create_draft(
    opportunity_id: UUID,
    payload: DraftCreate,
    session: SessionDep,
) -> DraftRead:
    if session.get(Opportunity, opportunity_id) is None:
        raise HTTPException(status_code=404, detail="Vaga nao encontrada")
    fact_ids, claims = _draft_claim_values(payload)
    _require_confirmed_facts(
        session,
        [UUID(fact_id) for fact_id in fact_ids],
    )

    draft = Draft(id=uuid4(), opportunity_id=opportunity_id)
    revision = DraftRevision(
        draft_id=draft.id,
        version=1,
        content=payload.content,
        fact_ids=fact_ids,
        claims=claims,
        content_hash=draft_content_hash(
            payload.content,
            _draft_hash_input(payload),
        ),
    )
    session.add_all([draft, revision])
    session.commit()
    session.refresh(draft)
    session.refresh(revision)
    return DraftRead(
        id=draft.id,
        opportunity_id=draft.opportunity_id,
        revisions=[_draft_revision_read(revision, approved=False)],
        created_at=draft.created_at,
    )


@app.post(
    "/api/v1/drafts/{draft_id}/revisions",
    response_model=DraftRevisionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_draft_revision(
    draft_id: UUID,
    payload: DraftCreate,
    session: SessionDep,
) -> DraftRevisionRead:
    draft = session.scalar(select(Draft).where(Draft.id == draft_id).with_for_update())
    if draft is None:
        raise HTTPException(status_code=404, detail="Rascunho nao encontrado")
    fact_ids, claims = _draft_claim_values(payload)
    _require_confirmed_facts(
        session,
        [UUID(fact_id) for fact_id in fact_ids],
    )

    latest = session.scalar(
        select(DraftRevision)
        .where(DraftRevision.draft_id == draft_id)
        .order_by(DraftRevision.version.desc())
        .limit(1)
    )
    if latest is None:
        raise HTTPException(status_code=409, detail="Rascunho sem revisao")
    revision = DraftRevision(
        draft_id=draft.id,
        version=latest.version + 1,
        content=payload.content,
        fact_ids=fact_ids,
        claims=claims,
        content_hash=draft_content_hash(
            payload.content,
            _draft_hash_input(payload),
        ),
    )
    session.add(revision)
    session.commit()
    session.refresh(revision)
    return _draft_revision_read(revision, approved=False)


@app.get("/api/v1/drafts/{draft_id}", response_model=DraftRead)
def get_draft(draft_id: UUID, session: SessionDep) -> DraftRead:
    draft = session.get(Draft, draft_id)
    if draft is None:
        raise HTTPException(status_code=404, detail="Rascunho nao encontrado")
    revisions = list(
        session.scalars(
            select(DraftRevision)
            .where(DraftRevision.draft_id == draft_id)
            .order_by(DraftRevision.version)
        )
    )
    latest = revisions[-1] if revisions else None
    latest_approval = None
    if latest is not None:
        latest_approval = session.scalar(
            select(DraftApproval)
            .where(
                DraftApproval.revision_id == latest.id,
                DraftApproval.action == "manual_application",
            )
            .order_by(DraftApproval.decision_number.desc())
            .limit(1)
        )
    return DraftRead(
        id=draft.id,
        opportunity_id=draft.opportunity_id,
        revisions=[
            _draft_revision_read(
                revision,
                approved=(
                    latest is not None
                    and revision.id == latest.id
                    and latest_approval is not None
                    and latest_approval.decision == "approved"
                    and latest_approval.content_hash == revision.content_hash
                ),
            )
            for revision in revisions
        ],
        created_at=draft.created_at,
    )


@app.post(
    "/api/v1/drafts/{draft_id}/revisions/{revision_id}/approval",
    response_model=DraftApprovalRead,
    status_code=status.HTTP_201_CREATED,
)
def decide_draft_approval(
    draft_id: UUID,
    revision_id: UUID,
    payload: DraftApprovalWrite,
    session: SessionDep,
) -> DraftApproval:
    draft = session.scalar(select(Draft).where(Draft.id == draft_id).with_for_update())
    if draft is None:
        raise HTTPException(status_code=404, detail="Rascunho nao encontrado")
    revision = session.get(DraftRevision, revision_id)
    if revision is None or revision.draft_id != draft_id:
        raise HTTPException(status_code=404, detail="Revisao nao encontrada")
    latest = session.scalar(
        select(DraftRevision)
        .where(DraftRevision.draft_id == draft_id)
        .order_by(DraftRevision.version.desc())
        .limit(1)
    )
    if latest is None or latest.id != revision.id:
        raise HTTPException(
            status_code=409,
            detail="A revisao deixou de ser atual; revise o conteudo mais recente",
        )
    if payload.expected_content_hash != revision.content_hash:
        raise HTTPException(status_code=409, detail="Hash do conteudo nao confere")

    latest_decision_number = session.scalar(
        select(func.max(DraftApproval.decision_number)).where(
            DraftApproval.revision_id == revision.id
        )
    )
    approval = DraftApproval(
        revision_id=revision.id,
        decision_number=(latest_decision_number or 0) + 1,
        action="manual_application",
        decision=payload.decision,
        content_hash=revision.content_hash,
    )
    session.add(approval)
    session.commit()
    session.refresh(approval)
    return approval


def _require_current_approval(
    session: Session,
    revision_id: UUID | None,
    opportunity_id: UUID,
) -> DraftRevision:
    if revision_id is None:
        raise HTTPException(
            status_code=409,
            detail="Associe a revisao aprovada do rascunho antes de continuar",
        )
    revision = session.get(DraftRevision, revision_id)
    if revision is None:
        raise HTTPException(status_code=404, detail="Revisao nao encontrada")
    draft = session.get(Draft, revision.draft_id)
    if draft is None or draft.opportunity_id != opportunity_id:
        raise HTTPException(
            status_code=422,
            detail="A revisao nao pertence a oportunidade da candidatura",
        )
    latest = session.scalar(
        select(DraftRevision)
        .where(DraftRevision.draft_id == revision.draft_id)
        .order_by(DraftRevision.version.desc())
        .limit(1)
    )
    if latest is None or latest.id != revision.id:
        raise HTTPException(
            status_code=409,
            detail="O conteudo mudou; a aprovacao da revisao anterior nao e valida",
        )
    approval = session.scalar(
        select(DraftApproval)
        .where(
            DraftApproval.revision_id == revision.id,
            DraftApproval.action == "manual_application",
        )
        .order_by(DraftApproval.decision_number.desc())
        .limit(1)
    )
    if (
        approval is None
        or approval.decision != "approved"
        or approval.content_hash != revision.content_hash
    ):
        raise HTTPException(
            status_code=409,
            detail="A revisao nao possui aprovacao humana valida para uso manual",
        )
    return revision


@app.post(
    "/api/v1/applications",
    response_model=ApplicationRead,
    status_code=status.HTTP_201_CREATED,
)
def create_application(
    payload: ApplicationCreate,
    session: SessionDep,
) -> Application:
    if session.get(Opportunity, payload.opportunity_id) is None:
        raise HTTPException(status_code=404, detail="Vaga nao encontrada")
    if payload.draft_revision_id is not None:
        revision = session.get(DraftRevision, payload.draft_revision_id)
        if revision is None:
            raise HTTPException(status_code=404, detail="Revisao nao encontrada")
        draft = session.get(Draft, revision.draft_id)
        if draft is None or draft.opportunity_id != payload.opportunity_id:
            raise HTTPException(
                status_code=422,
                detail="A revisao nao pertence a oportunidade da candidatura",
            )

    application = Application(
        opportunity_id=payload.opportunity_id,
        draft_revision_id=payload.draft_revision_id,
        state="draft",
    )
    try:
        session.add(application)
        session.flush()
        session.add(
            ApplicationEvent(
                application_id=application.id,
                from_state=None,
                to_state="draft",
            )
        )
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="Ja existe uma candidatura para esta oportunidade",
        ) from exc
    session.refresh(application)
    return application


@app.get("/api/v1/applications", response_model=list[ApplicationRead])
def list_applications(session: SessionDep) -> list[Application]:
    return list(
        session.scalars(
            select(Application).order_by(
                Application.created_at.desc(),
                Application.id,
            )
        )
    )


@app.get("/api/v1/applications/{application_id}", response_model=ApplicationRead)
def get_application(application_id: UUID, session: SessionDep) -> Application:
    application = session.get(Application, application_id)
    if application is None:
        raise HTTPException(status_code=404, detail="Candidatura nao encontrada")
    return application


@app.post(
    "/api/v1/applications/{application_id}/transitions",
    response_model=ApplicationRead,
)
def transition_application(
    application_id: UUID,
    payload: ApplicationTransition,
    session: SessionDep,
) -> Application:
    application = session.scalar(
        select(Application).where(Application.id == application_id).with_for_update()
    )
    if application is None:
        raise HTTPException(status_code=404, detail="Candidatura nao encontrada")

    try:
        validate_application_transition(
            application.state,
            payload.target_state,
            manual_submission_confirmed=payload.manual_submission_confirmed,
        )
    except InvalidApplicationTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    selected_revision = payload.draft_revision_id or application.draft_revision_id
    if payload.draft_revision_id is not None:
        revision = session.get(DraftRevision, payload.draft_revision_id)
        if revision is None:
            raise HTTPException(status_code=404, detail="Revisao nao encontrada")
        draft = session.get(Draft, revision.draft_id)
        if draft is None or draft.opportunity_id != application.opportunity_id:
            raise HTTPException(
                status_code=422,
                detail="A revisao nao pertence a oportunidade da candidatura",
            )
        application.draft_revision_id = revision.id

    if payload.target_state in {"awaiting_approval", "approved", "sent"}:
        if selected_revision is None:
            raise HTTPException(
                status_code=409,
                detail="Associe um rascunho para continuar a candidatura",
            )
        if payload.target_state in {"approved", "sent"}:
            _require_current_approval(
                session,
                selected_revision,
                application.opportunity_id,
            )

    previous_state = application.state
    application.state = payload.target_state
    session.add(
        ApplicationEvent(
            application_id=application.id,
            from_state=previous_state,
            to_state=payload.target_state,
            source="manual",
            confirmation=(
                "human_confirmed"
                if payload.target_state == "sent"
                and payload.manual_submission_confirmed
                else None
            ),
        )
    )
    session.commit()
    session.refresh(application)
    return application


@app.get(
    "/api/v1/applications/{application_id}/events",
    response_model=list[ApplicationEventRead],
)
def list_application_events(
    application_id: UUID,
    session: SessionDep,
) -> list[ApplicationEvent]:
    if session.get(Application, application_id) is None:
        raise HTTPException(status_code=404, detail="Candidatura nao encontrada")
    return list(
        session.scalars(
            select(ApplicationEvent)
            .where(ApplicationEvent.application_id == application_id)
            .order_by(ApplicationEvent.created_at, ApplicationEvent.id)
        )
    )
