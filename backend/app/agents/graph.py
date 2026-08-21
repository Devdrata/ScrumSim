from typing import Callable

from langgraph.graph import END, StateGraph

from app.agents.state import AgentState

NodeFn = Callable[[AgentState], AgentState]


def build_two_step_graph(gather_fn: NodeFn, draft_fn: NodeFn):
    """Every agent follows the same shape: gather real data, then draft a proposal.

    A dedicated StateGraph per agent type (rather than one shared graph with a router)
    keeps each agent's data-gathering and prompting independently readable, while still
    giving every agent the same LangGraph-managed state/execution model - e.g. a future
    'notify' node (post to Slack after approval) slots in the same way for any agent.
    """
    graph = StateGraph(AgentState)
    graph.add_node("gather", gather_fn)
    graph.add_node("draft", draft_fn)
    graph.set_entry_point("gather")
    graph.add_edge("gather", "draft")
    graph.add_edge("draft", END)
    return graph.compile()
