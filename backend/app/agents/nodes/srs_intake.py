from app.agents.graph import build_two_step_graph
from app.agents.output_schemas import SRSIngestDraft
from app.agents.state import AgentState
from app.llm.provider import get_chat_model

SYSTEM_PROMPT = (
    "You are ScrumSim's Scrum Master agent. A senior developer has uploaded a Software "
    "Requirements Specification (SRS) document. Respond with a single JSON object with a "
    "`summary` string and a single FLAT `items` array - never nested. Every element of `items` is a plain "
    "object with a `level` field: 1 for a top-level epic, 2 for a story, 3 for a task. There is no "
    "nesting: stories are never placed inside an epic's object, tasks are never placed inside a "
    "story's object - every item is just another entry in the same flat `items` array, and which "
    "epic/story it belongs to is implied only by walking the array in order (a level-2 item "
    "belongs to the nearest level-1 item before it; a level-3 item belongs to the nearest level-2 "
    "item before it). Emit items in exactly this walk order: an epic, then all of its stories one "
    "after another, and for each story its tasks immediately after that story. Never use ids or "
    "cross-references. Write clear titles and short descriptions drawn from the document. Estimate "
    "story_points (small integers) for level 2 and level 3 items where you can judge complexity - "
    "leave null for level 1. Always set required_skills to a list (short lowercase tags like "
    "'backend', 'react', 'design'; empty list if none apply) and acceptance_criteria to a string "
    "(empty string if not applicable) on every item. Do not invent requirements not grounded in "
    "the document.\n\n"
    "Example call for a two-sentence input document about a login page and a settings page, "
    "showing the required flat shape (note items is ONE flat array, not nested):\n"
    '{"summary": "Login and settings", "items": ['
    '{"level": 1, "title": "Login", "description": "", "story_points": null, '
    '"required_skills": [], "acceptance_criteria": ""}, '
    '{"level": 2, "title": "Login form", "description": "", "story_points": 3, '
    '"required_skills": ["react"], "acceptance_criteria": "User can submit credentials"}, '
    '{"level": 3, "title": "Validate email field", "description": "", "story_points": 1, '
    '"required_skills": ["react"], "acceptance_criteria": "Rejects malformed emails"}, '
    '{"level": 1, "title": "Settings", "description": "", "story_points": null, '
    '"required_skills": [], "acceptance_criteria": ""}'
    "]}"
)


def run(srs_text: str) -> dict:
    def gather(state: AgentState) -> AgentState:
        state["context"] = {"srs_text": srs_text}
        return state

    def draft(state: AgentState) -> AgentState:
        # json_mode rather than the (default) function_calling method: this payload is large and
        # deeply-bracketed enough that Groq's strict tool-call argument validator unreliably
        # rejects otherwise-sensible generations. json_mode has the model stream plain JSON text
        # that we validate ourselves, sidestepping that provider-side strict-schema layer.
        model = get_chat_model().with_structured_output(SRSIngestDraft, method="json_mode")
        result: SRSIngestDraft = model.invoke(
            [
                ("system", SYSTEM_PROMPT),
                ("human", f"SRS document:\n{state['context']['srs_text']}"),
            ]
        )
        state["proposed_output"] = result.model_dump()
        return state

    graph = build_two_step_graph(gather, draft)
    final_state = graph.invoke({"project_id": None, "context": {}, "proposed_output": {}})
    return {"context": final_state["context"], "proposed_output": final_state["proposed_output"]}
