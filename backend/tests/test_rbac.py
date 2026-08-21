from tests.helpers import signup_and_setup_project


def _add_member(client, admin_headers, email: str) -> dict:
    invite = client.post("/invites", json={"email": email, "role": "member"}, headers=admin_headers).json()
    token = invite["accept_url"].rsplit("/", 1)[-1]
    body = client.post(f"/invites/{token}/accept", json={"password": "password123"}).json()
    return {"Authorization": f"Bearer {body['access_token']}"}, body["user"]["id"]


def test_member_forbidden_from_admin_actions(client):
    admin_headers, _org_id, _project_id = signup_and_setup_project(client, email="admin@acme.com")
    member_headers, member_id = _add_member(client, admin_headers, "member@acme.com")

    assert client.post("/teams", json={"name": "New Team"}, headers=member_headers).status_code == 403
    assert (
        client.patch(f"/members/{member_id}", json={"role": "admin"}, headers=member_headers).status_code == 403
    )
    assert client.delete(f"/members/{member_id}", headers=member_headers).status_code == 403
    assert client.delete("/integrations/github", headers=member_headers).status_code == 403


def test_admin_can_perform_admin_actions(client):
    admin_headers, _org_id, _project_id = signup_and_setup_project(client, email="admin2@acme.com")
    _member_headers, member_id = _add_member(client, admin_headers, "member2@acme.com")

    assert client.post("/teams", json={"name": "New Team"}, headers=admin_headers).status_code == 201
    resp = client.patch(f"/members/{member_id}", json={"role": "admin"}, headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["role"] == "admin"


def test_member_can_self_update_profile(client):
    admin_headers, _org_id, _project_id = signup_and_setup_project(client, email="admin3@acme.com")
    member_headers, _member_id = _add_member(client, admin_headers, "member3@acme.com")

    resp = client.patch(
        "/members/me", json={"full_name": "Pat Member", "skills": ["python", "react"]}, headers=member_headers
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["full_name"] == "Pat Member"
    assert body["skills"] == ["python", "react"]


def test_admin_cannot_remove_self(client):
    admin_headers, org_id, _project_id = signup_and_setup_project(client, email="admin4@acme.com")
    members = client.get("/members", headers=admin_headers).json()
    self_id = next(m["id"] for m in members if m["email"] == "admin4@acme.com")

    resp = client.delete(f"/members/{self_id}", headers=admin_headers)
    assert resp.status_code == 400
