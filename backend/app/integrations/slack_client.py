import httpx

from app.integrations.exceptions import IntegrationError

BASE_URL = "https://slack.com/api"


def _post(bot_token: str, path: str, json_body: dict) -> dict:
    try:
        resp = httpx.post(
            f"{BASE_URL}{path}",
            headers={"Authorization": f"Bearer {bot_token}"},
            json=json_body,
            timeout=10.0,
        )
    except httpx.HTTPError as exc:
        raise IntegrationError(f"Slack request failed: {exc}") from exc

    data = resp.json()
    if not data.get("ok"):
        raise IntegrationError(f"Slack API error: {data.get('error', 'unknown_error')}")
    return data


def test_connection(bot_token: str) -> dict:
    data = _post(bot_token, "/auth.test", {})
    return {"team": data.get("team"), "bot_user": data.get("user")}


def post_message(bot_token: str, channel: str, text: str) -> dict:
    data = _post(bot_token, "/chat.postMessage", {"channel": channel, "text": text})
    return {"ts": data.get("ts"), "channel": data.get("channel")}
