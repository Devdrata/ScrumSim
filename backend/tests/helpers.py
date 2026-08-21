def signup_and_setup_project(client, email: str = "user@acme.com"):
    resp = client.post("/auth/signup", json={"org_name": "Acme", "email": email, "password": "password123"})
    body = resp.json()
    headers = {"Authorization": f"Bearer {body['access_token']}"}
    org_id = body["user"]["org_id"]

    team = client.post("/teams", json={"name": "Team A"}, headers=headers).json()
    project = client.post(f"/teams/{team['id']}/projects", json={"name": "Project A"}, headers=headers).json()
    return headers, org_id, project["id"]
