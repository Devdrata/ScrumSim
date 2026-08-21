import httpx

from app.integrations.exceptions import IntegrationError


def _request(site_url: str, email: str, api_token: str, method: str, path: str, **kwargs) -> httpx.Response:
    base_url = site_url.rstrip("/")
    try:
        resp = httpx.request(
            method,
            f"{base_url}{path}",
            auth=(email, api_token),
            headers={"Accept": "application/json"},
            timeout=10.0,
            **kwargs,
        )
    except httpx.HTTPError as exc:
        raise IntegrationError(f"Jira request failed: {exc}") from exc

    if resp.status_code == 401:
        raise IntegrationError("Jira email/API token is invalid")
    if resp.status_code == 404:
        raise IntegrationError("Jira site or project not found")
    if resp.status_code >= 400:
        raise IntegrationError(f"Jira API error {resp.status_code}: {resp.text[:200]}")
    return resp


def test_connection(site_url: str, email: str, api_token: str) -> dict:
    resp = _request(site_url, email, api_token, "GET", "/rest/api/3/myself")
    data = resp.json()
    return {"account_id": data.get("accountId"), "display_name": data.get("displayName")}


def get_recent_issues(site_url: str, email: str, api_token: str, project_key: str, limit: int = 20) -> list[dict]:
    resp = _request(
        site_url,
        email,
        api_token,
        "GET",
        "/rest/api/3/search",
        params={
            "jql": f"project = {project_key} ORDER BY updated DESC",
            "maxResults": limit,
            "fields": "summary,status,updated,assignee",
        },
    )
    issues = resp.json().get("issues", [])
    return [
        {
            "key": issue["key"],
            "summary": issue["fields"]["summary"],
            "status": issue["fields"]["status"]["name"],
            "assignee": (issue["fields"].get("assignee") or {}).get("displayName"),
            "updated": issue["fields"]["updated"],
        }
        for issue in issues
    ]
