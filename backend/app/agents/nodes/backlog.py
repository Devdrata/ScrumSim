import uuid

from sqlalchemy.orm import Session

from app.agents import tools
from app.agents.graph import build_two_step_graph
from app.agents.output_schemas import BacklogPriorityDraft
from app.agents.state import AgentState
from app.llm.provider import get_chat_model

SYSTEM_PROMPT = (
    "You are ScrumSim's backlog prioritization agent. Given the current backlog, propose a "
    "new priority order (most important first) for items that are not yet 'done', weighing "
    "impact_score (higher = more important) and deadline (closer = more urgent). Return "
    "ordered_item_ids using only ids from the provided backlog, plus a short rationale."
)


def run(db: Session, project_id: uuid.UUID) -> dict:
    def gather(state: AgentState) -> AgentState:
        state["context"] = {"backlog": tools.gather_backlog(db, project_id)}
        return state

    def draft(state: AgentState) -> AgentState:
        model = get_chat_model().with_structured_output(BacklogPriorityDraft)
        result: BacklogPriorityDraft = model.invoke(
            [
                ("system", SYSTEM_PROMPT),
                ("human", f"Backlog:\n{state['context']['backlog']}"),
            ]
        )
        state["proposed_output"] = result.model_dump()
        return state

    graph = build_two_step_graph(gather, draft)
    final_state = graph.invoke({"project_id": str(project_id), "context": {}, "proposed_output": {}})
    return {"context": final_state["context"], "proposed_output": final_state["proposed_output"]}
