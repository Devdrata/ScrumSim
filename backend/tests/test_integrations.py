import httpx
import pytest
import respx

from app.integrations import github_client, jira_client, slack_client
from app.integrations.exceptions import IntegrationError


@respx.mock
def test_github_test_connection_success():
    respx.get("https://api.github.com/repos/acme/repo").mock(
        return_value=httpx.Response(200, json={"full_name": "acme/repo", "private": False})
    )
    result = github_client.test_connection("tok", "acme/repo")
    assert result["full_name"] == "acme/repo"


@respx.mock
def test_github_test_connection_bad_token():
    respx.get("https://api.github.com/repos/acme/repo").mock(return_value=httpx.Response(401))
    with pytest.raises(IntegrationError):
        github_client.test_connection("bad", "acme/repo")


@respx.mock
def test_github_recent_commits_shapes_response():
    respx.get("https://api.github.com/repos/acme/repo/commits").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "sha": "abcdef1234567890",
                    "commit": {"message": "Fix bug\n\nlonger body", "author": {"name": "Dev", "date": "2026-01-01T00:00:00Z"}},
                    "author": {"login": "dev"},
                    "html_url": "https://github.com/acme/repo/commit/abcdef1",
                }
            ],
        )
    )
    commits = github_client.get_recent_commits("tok", "acme/repo")
    assert commits[0]["sha"] == "abcdef1"
    assert commits[0]["message"] == "Fix bug"
    assert commits[0]["author"] == "dev"


@respx.mock
def test_jira_test_connection_success():
    respx.get("https://acme.atlassian.net/rest/api/3/myself").mock(
        return_value=httpx.Response(200, json={"accountId": "1", "displayName": "A"})
    )
    result = jira_client.test_connection("https://acme.atlassian.net", "a@acme.com", "tok")
    assert result["display_name"] == "A"


@respx.mock
def test_jira_test_connection_bad_auth():
    respx.get("https://acme.atlassian.net/rest/api/3/myself").mock(return_value=httpx.Response(401))
    with pytest.raises(IntegrationError):
        jira_client.test_connection("https://acme.atlassian.net", "a@acme.com", "bad")


@respx.mock
def test_slack_test_connection_success():
    respx.post("https://slack.com/api/auth.test").mock(
        return_value=httpx.Response(200, json={"ok": True, "team": "Acme", "user": "scrumsim"})
    )
    result = slack_client.test_connection("xoxb-tok")
    assert result["team"] == "Acme"


@respx.mock
def test_slack_test_connection_failure():
    respx.post("https://slack.com/api/auth.test").mock(
        return_value=httpx.Response(200, json={"ok": False, "error": "invalid_auth"})
    )
    with pytest.raises(IntegrationError):
        slack_client.test_connection("bad-token")
