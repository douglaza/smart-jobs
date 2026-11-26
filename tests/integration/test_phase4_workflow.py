import os
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from smart_jobs.main import app


@pytest.mark.integration
def test_draft_approval_and_manual_application_lifecycle() -> None:
    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL must point to an isolated PostgreSQL test database")

    client = TestClient(app)
    persisted_applications = client.get("/api/v1/applications")
    assert persisted_applications.status_code == 200
    for existing in persisted_applications.json():
        if existing["state"] == "sent":
            persisted_events = client.get(
                f"/api/v1/applications/{existing['id']}/events"
            )
            assert persisted_events.status_code == 200
            assert persisted_events.json()[-1]["to_state"] == "sent"
            assert persisted_events.json()[-1]["confirmation"] == "human_confirmed"
            break

    marker = str(uuid4())
    opportunity_response = client.post(
        "/api/v1/opportunities",
        json={
            "company": f"Synthetic Company {marker}",
            "title": f"Synthetic role {marker}",
            "description": f"Synthetic fixture {marker}",
        },
    )
    assert opportunity_response.status_code == 201
    opportunity_id = opportunity_response.json()["id"]

    profile_response = client.post(
        "/api/v1/profile",
        json={"consented": True},
    )
    assert profile_response.status_code == 200

    fact_response = client.post(
        "/api/v1/profile/facts",
        json={
            "fact": f"Synthetic verified Python experience {marker}",
            "source": f"synthetic fixture {marker}",
            "evidence": f"synthetic evidence only {marker}",
            "confirmed": True,
        },
    )
    assert fact_response.status_code == 200
    fact_id = fact_response.json()["id"]

    unconfirmed_fact = client.post(
        "/api/v1/profile/facts",
        json={
            "fact": f"Unconfirmed synthetic detail {marker}",
            "source": f"synthetic fixture {marker}",
            "evidence": f"synthetic evidence only {marker}",
            "confirmed": False,
        },
    )
    assert unconfirmed_fact.status_code == 200
    ungrounded_draft = client.post(
        f"/api/v1/opportunities/{opportunity_id}/drafts",
        json={
            "content": f"Unconfirmed statement {marker}.",
            "claims": [
                {
                    "statement": f"Unconfirmed statement {marker}.",
                    "fact_ids": [unconfirmed_fact.json()["id"]],
                }
            ],
        },
    )
    assert ungrounded_draft.status_code == 422

    draft_response = client.post(
        f"/api/v1/opportunities/{opportunity_id}/drafts",
        json={
            "content": (
                f"Synthetic introduction {marker}. Synthetic experience {marker}."
            ),
            "claims": [
                {
                    "statement": f"Synthetic experience {marker}.",
                    "fact_ids": [fact_id],
                }
            ],
        },
    )
    assert draft_response.status_code == 201
    draft = draft_response.json()
    draft_id = draft["id"]
    first_revision = draft["revisions"][0]

    approve_url = f"/api/v1/drafts/{draft_id}/revisions/{first_revision['id']}/approval"
    first_approval = client.post(
        approve_url,
        json={
            "expected_content_hash": first_revision["content_hash"],
            "decision": "approved",
        },
    )
    assert first_approval.status_code == 201

    updated_revision_response = client.post(
        f"/api/v1/drafts/{draft_id}/revisions",
        json={
            "content": (
                f"Changed synthetic introduction {marker}. Changed experience {marker}."
            ),
            "claims": [
                {
                    "statement": f"Changed experience {marker}.",
                    "fact_ids": [fact_id],
                }
            ],
        },
    )
    assert updated_revision_response.status_code == 201
    latest_revision = updated_revision_response.json()
    assert latest_revision["version"] == 2

    current_draft = client.get(f"/api/v1/drafts/{draft_id}").json()
    assert current_draft["revisions"][0]["approved_for_manual_application"] is False
    assert current_draft["revisions"][1]["approved_for_manual_application"] is False
    stale_approval = client.post(
        approve_url,
        json={
            "expected_content_hash": first_revision["content_hash"],
            "decision": "approved",
        },
    )
    assert stale_approval.status_code == 409

    application_response = client.post(
        "/api/v1/applications",
        json={
            "opportunity_id": opportunity_id,
            "draft_revision_id": first_revision["id"],
        },
    )
    assert application_response.status_code == 201
    application = application_response.json()
    application_id = application["id"]
    duplicate_application = client.post(
        "/api/v1/applications",
        json={"opportunity_id": opportunity_id},
    )
    assert duplicate_application.status_code == 409

    awaiting = client.post(
        f"/api/v1/applications/{application_id}/transitions",
        json={
            "target_state": "awaiting_approval",
            "draft_revision_id": latest_revision["id"],
        },
    )
    assert awaiting.status_code == 200
    not_approved = client.post(
        f"/api/v1/applications/{application_id}/transitions",
        json={"target_state": "approved"},
    )
    assert not_approved.status_code == 409

    latest_approval = client.post(
        f"/api/v1/drafts/{draft_id}/revisions/{latest_revision['id']}/approval",
        json={
            "expected_content_hash": latest_revision["content_hash"],
            "decision": "approved",
        },
    )
    assert latest_approval.status_code == 201
    approved = client.post(
        f"/api/v1/applications/{application_id}/transitions",
        json={"target_state": "approved"},
    )
    assert approved.status_code == 200

    no_confirmation = client.post(
        f"/api/v1/applications/{application_id}/transitions",
        json={"target_state": "sent"},
    )
    assert no_confirmation.status_code == 409
    confirmed_submission = client.post(
        f"/api/v1/applications/{application_id}/transitions",
        json={
            "target_state": "sent",
            "manual_submission_confirmed": True,
        },
    )
    assert confirmed_submission.status_code == 200
    assert confirmed_submission.json()["state"] == "sent"

    events_response = client.get(f"/api/v1/applications/{application_id}/events")
    assert events_response.status_code == 200
    events = events_response.json()
    assert [event["to_state"] for event in events] == [
        "draft",
        "awaiting_approval",
        "approved",
        "sent",
    ]
    assert events[-1]["confirmation"] == "human_confirmed"

    persisted_application = client.get(f"/api/v1/applications/{application_id}").json()
    assert persisted_application["state"] == "sent"
    assert UUID(persisted_application["draft_revision_id"]) == UUID(
        latest_revision["id"]
    )
