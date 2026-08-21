import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.agents import tools
from app.agents.graph import build_two_step_graph
from app.agents.output_schemas import StandupDraft
from app.agents.state import AgentState
from app.llm.provider import get_chat_model

SYSTEM_PROMPT = (
    "You are ScrumSim's standup agent. Given recent GitHub commits/PRs and Jira issue "
    "activity for a project, write a concise standup summary (2-4 sentences) covering what "
    "progress was made. List any blockers you can reasonably infer (e.g. PRs open a long "
    "time, issues stuck in the same status). If an integration has no data available, say so "
    "plainly rather than inventing activity."
)


def run(db: Session, project_id: uuid.UUID, github_creds: dict | None, jira_creds: dict | None) -> dict:
    since = datetime.now(timezone.utc) - timedelta(days=1)

    def gather(state: AgentState) -> AgentState:
        state["context"] = {
            "github": tools.gather_recent_github_activity(github_creds, since),
            "jira": tools.gather_recent_jira_activity(jira_creds),
        }
        return state

    def draft(state: AgentState) -> AgentState:
        model = get_chat_model().with_structured_output(StandupDraft)
        result: StandupDraft = model.invoke(
            [
                ("system", SYSTEM_PROMPT),
                ("human", f"Recent activity:\n{state['context']}"),
            ]
        )
        state["proposed_output"] = result.model_dump()
        return state

    graph = build_two_step_graph(gather, draft)
    final_state = graph.invoke({"project_id": str(project_id), "context": {}, "proposed_output": {}})
    return {"context": final_state["context"], "proposed_output": final_state["proposed_output"]}
