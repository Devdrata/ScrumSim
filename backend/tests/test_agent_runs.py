import uuid

from app.models.agent_run import AgentRun, AgentType
from tests.helpers import signup_and_setup_project


def _create_backlog_run(db_session, org_id: str, project_id: str, ordered_item_ids: list[str]) -> AgentRun:
    run = AgentRun(
        org_id=uuid.UUID(org_id),
        project_id=uuid.UUID(project_id),
        agent_type=AgentType.BACKLOG,
        input_context={},
        proposed_output={"ordered_item_ids": ordered_item_ids, "rationale": "test"},
    )
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)
    return run


def test_backlog_agent_run_approve_applies_priority(client, db_session):
    headers, org_id, project_id = signup_and_setup_project(client)

    item1 = client.post(f"/projects/{project_id}/backlog", json={"title": "A"}, headers=headers).json()
    item2 = client.post(f"/projects/{project_id}/backlog", json={"title": "B"}, headers=headers).json()

    run = _create_backlog_run(db_session, org_id, project_id, [item2["id"], item1["id"]])

    resp = client.post(f"/agents/runs/{run.id}/approve", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "approved"

    items = {i["id"]: i for i in client.get(f"/projects/{project_id}/backlog", headers=headers).json()}
    assert items[item2["id"]]["priority_rank"] == 1
    assert items[item1["id"]]["priority_rank"] == 2


def test_agent_run_reject_does_not_apply(client, db_session):
    headers, org_id, project_id = signup_and_setup_project(client)
    item1 = client.post(f"/projects/{project_id}/backlog", json={"title": "A"}, headers=headers).json()

    run = _create_backlog_run(db_session, org_id, project_id, [item1["id"]])

    resp = client.post(f"/agents/runs/{run.id}/reject", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "rejected"

    items = client.get(f"/projects/{project_id}/backlog", headers=headers).json()
    assert items[0]["priority_rank"] is None


def test_agent_run_double_review_conflicts(client, db_session):
    headers, org_id, project_id = signup_and_setup_project(client)
    run = _create_backlog_run(db_session, org_id, project_id, [])

    first = client.post(f"/agents/runs/{run.id}/approve", headers=headers)
    assert first.status_code == 200
    second = client.post(f"/agents/runs/{run.id}/approve", headers=headers)
    assert second.status_code == 409


def test_agent_run_not_visible_to_other_org(client, db_session):
    headers_a, org_id_a, project_id_a = signup_and_setup_project(client, email="a@acme.com")
    headers_b, _org_id_b, _project_id_b = signup_and_setup_project(client, email="b@other.com")

    run = _create_backlog_run(db_session, org_id_a, project_id_a, [])

    resp = client.post(f"/agents/runs/{run.id}/approve", headers=headers_b)
    assert resp.status_code == 404


def _create_planner_run(db_session, org_id: str, project_id: str, sprint_id: str, recommended_items: list[dict]) -> AgentRun:
    run = AgentRun(
        org_id=uuid.UUID(org_id),
        project_id=uuid.UUID(project_id),
        agent_type=AgentType.PLANNER,
        input_context={"target_sprint_id": sprint_id},
        proposed_output={"summary": "test", "recommended_items": recommended_items},
    )
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)
    return run


def test_planner_approval_assigns_valid_org_member(client, db_session):
    headers, org_id, project_id = signup_and_setup_project(client, email="planner-owner@acme.com")
    item = client.post(f"/projects/{project_id}/backlog", json={"title": "A"}, headers=headers).json()
    sprint = client.post(f"/projects/{project_id}/sprints", json={"name": "Sprint 1"}, headers=headers).json()
    member_id = client.get("/members", headers=headers).json()[0]["id"]

    run = _create_planner_run(
        db_session,
        org_id,
        project_id,
        sprint["id"],
        [{"backlog_item_id": item["id"], "rationale": "fits", "assignee_user_id": member_id}],
    )
    resp = client.post(f"/agents/runs/{run.id}/approve", headers=headers)
    assert resp.status_code == 200

    updated = client.get(f"/projects/{project_id}/backlog", headers=headers).json()[0]
    assert updated["assignee_id"] == member_id
    assert updated["status"] == "in_sprint"


def test_planner_approval_ignores_assignee_outside_org(client, db_session):
    headers, org_id, project_id = signup_and_setup_project(client, email="planner-owner2@acme.com")
    _other_headers, _other_org, _other_project = signup_and_setup_project(client, email="outsider2@other.com")
    outsider_id = client.get("/auth/me", headers=_other_headers).json()["id"]

    item = client.post(f"/projects/{project_id}/backlog", json={"title": "A"}, headers=headers).json()
    sprint = client.post(f"/projects/{project_id}/sprints", json={"name": "Sprint 1"}, headers=headers).json()

    run = _create_planner_run(
        db_session,
        org_id,
        project_id,
        sprint["id"],
        [{"backlog_item_id": item["id"], "rationale": "fits", "assignee_user_id": outsider_id}],
    )
    resp = client.post(f"/agents/runs/{run.id}/approve", headers=headers)
    assert resp.status_code == 200

    updated = client.get(f"/projects/{project_id}/backlog", headers=headers).json()[0]
    assert updated["assignee_id"] is None
