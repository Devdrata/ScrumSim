import uuid

from sqlalchemy.orm import Session

from app.agents import tools
from app.agents.graph import build_two_step_graph
from app.agents.output_schemas import RetroDraft
from app.agents.state import AgentState
from app.llm.provider import get_chat_model

SYSTEM_PROMPT = (
    "You are ScrumSim's retrospective agent. Given a sprint's completion metrics, draft "
    "retro discussion points split into what went well, what went wrong, and suggested "
    "action items. Be specific and grounded in the metrics provided - do not invent numbers "
    "or facts not present in the data."
)


def run(db: Session, sprint_id: uuid.UUID) -> dict:
    def gather(state: AgentState) -> AgentState:
        state["context"] = {"metrics": tools.gather_sprint_metrics(db, sprint_id)}
        return state

    def draft(state: AgentState) -> AgentState:
        model = get_chat_model().with_structured_output(RetroDraft)
        result: RetroDraft = model.invoke(
            [
                ("system", SYSTEM_PROMPT),
                ("human", f"Sprint metrics:\n{state['context']['metrics']}"),
            ]
        )
        state["proposed_output"] = result.model_dump()
        return state

    graph = build_two_step_graph(gather, draft)
    final_state = graph.invoke({"sprint_id": str(sprint_id), "context": {}, "proposed_output": {}})
    return {"context": final_state["context"], "proposed_output": final_state["proposed_output"]}
