from tests.helpers import signup_and_setup_project


def test_admin_creates_invite_and_member_accepts_into_same_org(client):
    admin_headers, org_id, _project_id = signup_and_setup_project(client, email="admin@acme.com")

    invite_resp = client.post(
        "/invites", json={"email": "newhire@acme.com", "role": "member"}, headers=admin_headers
    )
    assert invite_resp.status_code == 201
    invite = invite_resp.json()
    token = invite["accept_url"].rsplit("/", 1)[-1]

    preview_resp = client.get(f"/invites/{token}")
    assert preview_resp.status_code == 200
    assert preview_resp.json()["email"] == "newhire@acme.com"

    accept_resp = client.post(f"/invites/{token}/accept", json={"password": "password123"})
    assert accept_resp.status_code == 201
    body = accept_resp.json()
    assert body["user"]["org_id"] == org_id
    assert body["user"]["role"] == "member"

    new_member_headers = {"Authorization": f"Bearer {body['access_token']}"}
    members = client.get("/members", headers=new_member_headers).json()
    assert any(m["email"] == "newhire@acme.com" for m in members)
    assert any(m["email"] == "admin@acme.com" for m in members)


def test_invite_cannot_be_accepted_twice(client):
    admin_headers, _org_id, _project_id = signup_and_setup_project(client, email="admin2@acme.com")
    invite = client.post(
        "/invites", json={"email": "second@acme.com", "role": "member"}, headers=admin_headers
    ).json()
    token = invite["accept_url"].rsplit("/", 1)[-1]

    first = client.post(f"/invites/{token}/accept", json={"password": "password123"})
    assert first.status_code == 201
    second = client.post(f"/invites/{token}/accept", json={"password": "password123"})
    assert second.status_code == 404


def test_revoked_invite_cannot_be_accepted(client):
    admin_headers, _org_id, _project_id = signup_and_setup_project(client, email="admin3@acme.com")
    invite = client.post(
        "/invites", json={"email": "third@acme.com", "role": "member"}, headers=admin_headers
    ).json()

    revoke_resp = client.delete(f"/invites/{invite['id']}", headers=admin_headers)
    assert revoke_resp.status_code == 204

    token = invite["accept_url"].rsplit("/", 1)[-1]
    accept_resp = client.post(f"/invites/{token}/accept", json={"password": "password123"})
    assert accept_resp.status_code == 404


def test_non_admin_cannot_create_invite(client):
    admin_headers, _org_id, _project_id = signup_and_setup_project(client, email="admin4@acme.com")
    invite = client.post(
        "/invites", json={"email": "member4@acme.com", "role": "member"}, headers=admin_headers
    ).json()
    token = invite["accept_url"].rsplit("/", 1)[-1]
    member_body = client.post(f"/invites/{token}/accept", json={"password": "password123"}).json()
    member_headers = {"Authorization": f"Bearer {member_body['access_token']}"}

    resp = client.post("/invites", json={"email": "another@acme.com", "role": "member"}, headers=member_headers)
    assert resp.status_code == 403
