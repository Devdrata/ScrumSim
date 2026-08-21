from datetime import datetime

import httpx

from app.integrations.exceptions import IntegrationError

BASE_URL = "https://api.github.com"


def _headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _request(token: str, method: str, path: str, **kwargs) -> httpx.Response:
    try:
        resp = httpx.request(method, f"{BASE_URL}{path}", headers=_headers(token), timeout=10.0, **kwargs)
    except httpx.HTTPError as exc:
        raise IntegrationError(f"GitHub request failed: {exc}") from exc

    if resp.status_code == 401:
        raise IntegrationError("GitHub token is invalid or expired")
    if resp.status_code == 404:
        raise IntegrationError("GitHub repo not found or token lacks access")
    if resp.status_code >= 400:
        raise IntegrationError(f"GitHub API error {resp.status_code}: {resp.text[:200]}")
    return resp


def test_connection(token: str, repo: str) -> dict:
    """repo is 'owner/name'. Returns basic repo metadata on success."""
    resp = _request(token, "GET", f"/repos/{repo}")
    data = resp.json()
    return {"full_name": data.get("full_name"), "private": data.get("private")}


def get_recent_commits(token: str, repo: str, since: datetime | None = None, limit: int = 20) -> list[dict]:
    params: dict = {"per_page": limit}
    if since is not None:
        params["since"] = since.isoformat()
    resp = _request(token, "GET", f"/repos/{repo}/commits", params=params)
    return [
        {
            "sha": item["sha"][:7],
            "message": item["commit"]["message"].splitlines()[0],
            "author": (item.get("author") or {}).get("login") or item["commit"]["author"]["name"],
            "url": item["html_url"],
            "date": item["commit"]["author"]["date"],
        }
        for item in resp.json()
    ]


def get_recent_pull_requests(token: str, repo: str, limit: int = 20) -> list[dict]:
    resp = _request(token, "GET", f"/repos/{repo}/pulls", params={"state": "all", "per_page": limit})
    return [
        {
            "number": item["number"],
            "title": item["title"],
            "state": item["state"],
            "url": item["html_url"],
            "updated_at": item["updated_at"],
        }
        for item in resp.json()
    ]
