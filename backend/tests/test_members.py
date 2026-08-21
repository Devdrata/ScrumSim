from tests.helpers import signup_and_setup_project


def test_completing_assigned_task_builds_skill_profile(client):
    headers, _org_id, project_id = signup_and_setup_project(client, email="admin@acme.com")
    members = client.get("/members", headers=headers).json()
    my_id = members[0]["id"]

    item = client.post(
        f"/projects/{project_id}/backlog",
        json={
            "title": "Build login page",
            "story_points": 5,
            "required_skills": ["react", "css"],
            "assignee_id": my_id,
        },
        headers=headers,
    ).json()
    assert item["required_skills"] == ["react", "css"]

    patch_resp = client.patch(f"/backlog/{item['id']}", json={"status": "done"}, headers=headers)
    assert patch_resp.status_code == 200

    members_after = {m["id"]: m for m in client.get("/members", headers=headers).json()}
    stats = {s["skill"]: s for s in members_after[my_id]["skill_stats"]}
    assert stats["react"]["completed_task_count"] == 1
    assert stats["react"]["completed_story_points"] == 5
    assert stats["css"]["completed_task_count"] == 1


def test_skill_profile_does_not_double_count_on_noop_save(client):
    headers, _org_id, project_id = signup_and_setup_project(client, email="admin2@acme.com")
    members = client.get("/members", headers=headers).json()
    my_id = members[0]["id"]

    item = client.post(
        f"/projects/{project_id}/backlog",
        json={"title": "Ship API", "story_points": 3, "required_skills": ["backend"], "assignee_id": my_id},
        headers=headers,
    ).json()
    client.patch(f"/backlog/{item['id']}", json={"status": "done"}, headers=headers)
    # unrelated follow-up edit while already done - must not re-count
    client.patch(f"/backlog/{item['id']}", json={"description": "done and documented"}, headers=headers)

    members_after = {m["id"]: m for m in client.get("/members", headers=headers).json()}
    stats = {s["skill"]: s for s in members_after[my_id]["skill_stats"]}
    assert stats["backend"]["completed_task_count"] == 1


def test_assignee_must_be_org_member(client):
    headers, _org_id, project_id = signup_and_setup_project(client, email="admin3@acme.com")
    other_headers, _other_org, _other_project = signup_and_setup_project(client, email="outsider@other.com")
    outsider_id = client.get("/auth/me", headers=other_headers).json()["id"]

    resp = client.post(
        f"/projects/{project_id}/backlog",
        json={"title": "Task", "assignee_id": outsider_id},
        headers=headers,
    )
    assert resp.status_code == 400
