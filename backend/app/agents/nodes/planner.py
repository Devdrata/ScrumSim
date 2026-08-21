import uuid

from sqlalchemy.orm import Session

from app.agents import tools
from app.agents.graph import build_two_step_graph
from app.agents.output_schemas import SprintPlanDraft
from app.agents.state import AgentState
from app.llm.provider import get_chat_model

SYSTEM_PROMPT = (
    "You are ScrumSim's sprint planning agent. Given the current backlog (a tree of epics, "
    "stories, and tasks) for a project, recommend which backlog items (that are not already "
    "'done') should go into the next sprint, in priority order, with a short rationale for each. "
    "Favor items with closer deadlines and higher impact_score. Only use backlog_item_id values "
    "that appear in the provided backlog - never invent items. Try to keep the total story_points "
    "of recommended items within the sprint's capacity_points if it is set, using recent team "
    "velocity as a guide if capacity is not set. For each recommended item, also propose an "
    "assignee_user_id: pick the team member whose declared_skills or demonstrated_skills best "
    "match the item's required_skills, preferring demonstrated (actually completed) experience "
    "over merely declared skills when both are available. Only use ids from the provided team "
    "member list, and leave assignee_user_id null if no member is a reasonable fit.\n\n"
    "Balance the load across the team - this is as important as the skill match itself. Each "
    "team member's current_sprint_points shows what they're already carrying in this sprint from "
    "earlier planning. As you assign items down the list, keep a running mental tally of the "
    "story_points you've personally added to each candidate's current_sprint_points so far in "
    "*this* set of recommendations, and treat that running total the same way: when two or more "
    "members are a reasonably close skill match for an item, assign it to whichever of them has "
    "the lower combined total (existing current_sprint_points plus what you've already given them "
    "in this response), not whoever happened to be the single best match. Only stack multiple "
    "items on the same person when they are genuinely the sole reasonable skill fit - a mediocre "
    "match on an idle teammate beats a perfect match on someone already overloaded."
)


def run(db: Session, org_id: uuid.UUID, project_id: uuid.UUID, sprint_id: uuid.UUID) -> dict:
    def gather(state: AgentState) -> AgentState:
        state["context"] = {
            "backlog": tools.gather_backlog(db, project_id),
            "team_members": tools.gather_org_members(db, org_id, sprint_id),
            "sprint_capacity": tools.gather_sprint_capacity(db, sprint_id),
            "recent_velocity": tools.gather_velocity(db, project_id),
        }
        return state

    def draft(state: AgentState) -> AgentState:
        model = get_chat_model().with_structured_output(SprintPlanDraft)
        result: SprintPlanDraft = model.invoke(
            [
                ("system", SYSTEM_PROMPT),
                (
                    "human",
                    f"Backlog:\n{state['context']['backlog']}\n\n"
                    f"Team members:\n{state['context']['team_members']}\n\n"
                    f"Sprint capacity:\n{state['context']['sprint_capacity']}\n\n"
                    f"Recent velocity (avg story points/sprint):\n{state['context']['recent_velocity']}",
                ),
            ]
        )
        state["proposed_output"] = result.model_dump()
        return state

    graph = build_two_step_graph(gather, draft)
    final_state = graph.invoke({"project_id": str(project_id), "context": {}, "proposed_output": {}})
    return {"context": final_state["context"], "proposed_output": final_state["proposed_output"]}
