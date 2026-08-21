import uuid

from app.models.agent_run import AgentRun, AgentType
from tests.helpers import signup_and_setup_project


def test_unsupported_file_type_rejected(client):
    headers, _org_id, project_id = signup_and_setup_project(client)

    resp = client.post(
        f"/agents/srs-intake/run/{project_id}",
        files={"file": ("spec.docx", b"not really a docx", "application/octet-stream")},
        headers=headers,
    )
    assert resp.status_code == 400
    assert "Unsupported file type" in resp.json()["detail"]


def test_empty_document_rejected(client):
    headers, _org_id, project_id = signup_and_setup_project(client)

    resp = client.post(
        f"/agents/srs-intake/run/{project_id}",
        files={"file": ("spec.txt", b"   \n\n  ", "text/plain")},
        headers=headers,
    )
    assert resp.status_code == 400
    assert "No extractable text" in resp.json()["detail"]


def _create_srs_run(db_session, org_id: str, project_id: str) -> AgentRun:
    run = AgentRun(
        org_id=uuid.UUID(org_id),
        project_id=uuid.UUID(project_id),
        agent_type=AgentType.SRS_INTAKE,
        input_context={"source_filename": "spec.txt"},
        proposed_output={
            "summary": "Auth and dashboard",
            "items": [
                {
                    "level": 1,
                    "title": "User Authentication",
                    "description": "Let users sign in",
                    "required_skills": ["backend"],
                },
                {
                    "level": 2,
                    "title": "Login form",
                    "description": "Email/password login",
                    "story_points": 3,
                    "required_skills": ["react"],
                    "acceptance_criteria": "User can log in with valid credentials",
                },
                {
                    "level": 3,
                    "title": "Build login form component",
                    "description": "React form with validation",
                    "story_points": 2,
                    "required_skills": ["react"],
                    "acceptance_criteria": "Form validates email format",
                },
            ],
        },
    )
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)
    return run


def test_approving_srs_run_creates_epic_story_task_tree(client, db_session):
    headers, org_id, project_id = signup_and_setup_project(client)
    run = _create_srs_run(db_session, org_id, project_id)

    resp = client.post(f"/agents/runs/{run.id}/approve", headers=headers)
    assert resp.status_code == 200

    tree = client.get(f"/projects/{project_id}/backlog/tree", headers=headers).json()
    assert len(tree) == 1
    epic = tree[0]
    assert epic["item_type"] == "epic"
    assert epic["title"] == "User Authentication"
    assert len(epic["children"]) == 1

    story = epic["children"][0]
    assert story["item_type"] == "story"
    assert story["story_points"] == 3
    assert story["acceptance_criteria"] == "User can log in with valid credentials"
    assert len(story["children"]) == 1

    task = story["children"][0]
    assert task["item_type"] == "task"
    assert task["parent_id"] == story["id"]
    assert task["required_skills"] == ["react"]


def test_srs_intake_handles_multiple_siblings_and_new_epic(client, db_session):
    headers, org_id, project_id = signup_and_setup_project(client, email="order@acme.com")
    run = AgentRun(
        org_id=uuid.UUID(org_id),
        project_id=uuid.UUID(project_id),
        agent_type=AgentType.SRS_INTAKE,
        input_context={"source_filename": "spec.txt"},
        proposed_output={
            "summary": "test",
            "items": [
                {"level": 1, "title": "Epic A"},
                {"level": 2, "title": "Story A1"},
                {"level": 3, "title": "Task A1-1"},
                {"level": 3, "title": "Task A1-2"},
                {"level": 2, "title": "Story A2"},
                {"level": 1, "title": "Epic B"},
                {"level": 2, "title": "Story B1"},
            ],
        },
    )
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)

    resp = client.post(f"/agents/runs/{run.id}/approve", headers=headers)
    assert resp.status_code == 200

    tree = client.get(f"/projects/{project_id}/backlog/tree", headers=headers).json()
    assert [e["title"] for e in tree] == ["Epic A", "Epic B"]

    epic_a = tree[0]
    assert [s["title"] for s in epic_a["children"]] == ["Story A1", "Story A2"]
    story_a1 = epic_a["children"][0]
    assert [t["title"] for t in story_a1["children"]] == ["Task A1-1", "Task A1-2"]
    story_a2 = epic_a["children"][1]
    assert story_a2["children"] == []

    epic_b = tree[1]
    assert [s["title"] for s in epic_b["children"]] == ["Story B1"]
