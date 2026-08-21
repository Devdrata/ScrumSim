from tests.helpers import signup_and_setup_project


def test_backlog_item_crud(client):
    headers, _org_id, project_id = signup_and_setup_project(client)

    create_resp = client.post(f"/projects/{project_id}/backlog", json={"title": "Do the thing"}, headers=headers)
    assert create_resp.status_code == 201
    item = create_resp.json()
    assert item["status"] == "backlog"

    list_resp = client.get(f"/projects/{project_id}/backlog", headers=headers)
    assert len(list_resp.json()) == 1

    patch_resp = client.patch(f"/backlog/{item['id']}", json={"status": "in_progress"}, headers=headers)
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "in_progress"


def test_backlog_item_org_isolation(client):
    _headers_a, _org_id_a, project_id_a = signup_and_setup_project(client, email="a@acme.com")
    headers_b, _org_id_b, _project_id_b = signup_and_setup_project(client, email="b@other.com")

    resp = client.get(f"/projects/{project_id_a}/backlog", headers=headers_b)
    assert resp.status_code == 404


def test_sprint_crud_and_status_update(client):
    headers, _org_id, project_id = signup_and_setup_project(client)

    create_resp = client.post(f"/projects/{project_id}/sprints", json={"name": "Sprint 1"}, headers=headers)
    assert create_resp.status_code == 201
    sprint = create_resp.json()
    assert sprint["status"] == "planned"

    patch_resp = client.patch(f"/sprints/{sprint['id']}", json={"status": "active"}, headers=headers)
    assert patch_resp.json()["status"] == "active"


def test_backlog_item_supports_tree_and_scrum_fields(client):
    headers, _org_id, project_id = signup_and_setup_project(client)

    epic = client.post(
        f"/projects/{project_id}/backlog",
        json={"title": "Checkout flow", "item_type": "epic"},
        headers=headers,
    ).json()
    assert epic["item_type"] == "epic"
    assert epic["required_skills"] == []

    story = client.post(
        f"/projects/{project_id}/backlog",
        json={
            "title": "Payment step",
            "item_type": "story",
            "parent_id": epic["id"],
            "story_points": 8,
            "required_skills": ["payments"],
            "acceptance_criteria": "Card payments succeed",
        },
        headers=headers,
    ).json()
    assert story["parent_id"] == epic["id"]
    assert story["story_points"] == 8

    tree = client.get(f"/projects/{project_id}/backlog/tree", headers=headers).json()
    assert len(tree) == 1
    assert tree[0]["id"] == epic["id"]
    assert [c["id"] for c in tree[0]["children"]] == [story["id"]]

    flat = client.get(f"/projects/{project_id}/backlog", headers=headers).json()
    assert len(flat) == 2


def test_backlog_item_parent_must_be_same_project(client):
    headers, _org_id, project_id_a = signup_and_setup_project(client, email="a2@acme.com")
    team = client.post("/teams", json={"name": "Team B"}, headers=headers).json()
    project_b = client.post(f"/teams/{team['id']}/projects", json={"name": "Project B"}, headers=headers).json()

    item_a = client.post(f"/projects/{project_id_a}/backlog", json={"title": "A"}, headers=headers).json()

    resp = client.post(
        f"/projects/{project_b['id']}/backlog",
        json={"title": "Cross-project child", "parent_id": item_a["id"]},
        headers=headers,
    )
    assert resp.status_code == 400


def test_standup_entry_create_and_list(client):
    headers, _org_id, project_id = signup_and_setup_project(client)

    resp = client.post(f"/projects/{project_id}/standups", json={"content": "Shipped the login page"}, headers=headers)
    assert resp.status_code == 201
    assert resp.json()["author"] == "user"

    list_resp = client.get(f"/projects/{project_id}/standups", headers=headers)
    assert len(list_resp.json()) == 1
