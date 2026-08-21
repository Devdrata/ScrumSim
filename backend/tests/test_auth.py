def test_signup_then_get_me(client):
    resp = client.post("/auth/signup", json={"org_name": "Acme", "email": "a@acme.com", "password": "password123"})
    assert resp.status_code == 201
    token = resp.json()["access_token"]

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "a@acme.com"
    assert me.json()["role"] == "admin"


def test_signup_duplicate_email_conflict(client):
    payload = {"org_name": "Acme", "email": "dup@acme.com", "password": "password123"}
    client.post("/auth/signup", json=payload)
    resp = client.post("/auth/signup", json=payload)
    assert resp.status_code == 409


def test_login_wrong_password(client):
    client.post("/auth/signup", json={"org_name": "Acme", "email": "b@acme.com", "password": "password123"})
    resp = client.post("/auth/login", json={"email": "b@acme.com", "password": "wrong-password"})
    assert resp.status_code == 401


def test_me_requires_auth(client):
    resp = client.get("/auth/me")
    assert resp.status_code == 401
