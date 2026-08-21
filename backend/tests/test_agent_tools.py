import uuid

from app.agents import tools
from tests.helpers import signup_and_setup_project


def test_gather_org_members_computes_current_sprint_load(client, db_session):
    headers, org_id, project_id = signup_and_setup_project(client)
    me_id = client.get("/auth/me", headers=headers).json()["id"]

    sprint = client.post(f"/projects/{project_id}/sprints", json={"name": "S1"}, headers=headers).json()

    item1 = client.post(
        f"/projects/{project_id}/backlog",
        json={"title": "A", "story_points": 3, "assignee_id": me_id},
        headers=headers,
    ).json()
    client.patch(f"/backlog/{item1['id']}", json={"sprint_id": sprint["id"], "status": "in_sprint"}, headers=headers)

    item2 = client.post(
        f"/projects/{project_id}/backlog",
        json={"title": "B", "story_points": 5, "assignee_id": me_id},
        headers=headers,
    ).json()
    # done items shouldn't count as current load - the work is finished
    client.patch(
        f"/backlog/{item2['id']}", json={"sprint_id": sprint["id"], "status": "done"}, headers=headers
    )

    members = tools.gather_org_members(db_session, uuid.UUID(org_id), uuid.UUID(sprint["id"]))
    me = next(m for m in members if m["id"] == me_id)
    assert me["current_sprint_points"] == 3


def test_gather_org_members_without_sprint_id_has_zero_load(client, db_session):
    headers, org_id, _project_id = signup_and_setup_project(client)
    members = tools.gather_org_members(db_session, uuid.UUID(org_id))
    assert all(m["current_sprint_points"] == 0 for m in members)
