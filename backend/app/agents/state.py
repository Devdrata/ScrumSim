from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    """Shared state threaded through every agent's gather -> draft graph.

    Kept to plain JSON-serializable data (no DB session / HTTP clients) so the same
    state shape works for every agent type regardless of what it gathers.
    """

    project_id: str | None
    sprint_id: str | None
    context: dict[str, Any]
    proposed_output: dict[str, Any]
