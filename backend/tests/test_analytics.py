import uuid
from datetime import datetime, timedelta, timezone

from app.models.backlog_item import BacklogItem, BacklogItemStatus
from tests.helpers import signup_and_setup_project


def test_analytics_active_sprint_burndown(client):
    headers, _org_id, project_id = signup_and_setup_project(client)

    sprint = client.post(f"/projects/{project_id}/sprints", json={"name": "Sprint 1"}, headers=headers).json()
    client.patch(f"/sprints/{sprint['id']}", json={"status": "active"}, headers=headers)

    item1 = client.post(f"/projects/{project_id}/backlog", json={"title": "A"}, headers=headers).json()
    item2 = client.post(f"/projects/{project_id}/backlog", json={"title": "B"}, headers=headers).json()
    client.patch(f"/backlog/{item1['id']}", json={"sprint_id": sprint["id"], "status": "done"}, headers=headers)
    client.patch(f"/backlog/{item2['id']}", json={"sprint_id": sprint["id"]}, headers=headers)

    resp = client.get(f"/projects/{project_id}/analytics", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["active_sprint"]["total_items"] == 2
    assert body["active_sprint"]["completed_items"] == 1
    assert body["active_sprint"]["completion_rate"] == 0.5


def test_analytics_flags_stuck_in_progress_items(client, db_session):
    headers, _org_id, project_id = signup_and_setup_project(client)

    item = client.post(f"/projects/{project_id}/backlog", json={"title": "Stuck"}, headers=headers).json()
    client.patch(f"/backlog/{item['id']}", json={"status": "in_progress"}, headers=headers)

    # backdate updated_at to simulate an item that's been stuck for a while
    row = db_session.get(BacklogItem, uuid.UUID(item["id"]))
    row.updated_at = datetime.now(timezone.utc) - timedelta(days=5)
    db_session.commit()

    resp = client.get(f"/projects/{project_id}/analytics", headers=headers)
    body = resp.json()
    assert len(body["bottlenecks"]) == 1
    assert body["bottlenecks"][0]["id"] == item["id"]
    assert body["bottlenecks"][0]["days_in_status"] >= 4.9
