"""
CIAS-X Workflow

LangGraph-based workflow for the CIAS-X AI Scientist system.
Topology: planner -> executor -> analyst (loop until budget exhausted)
"""

import logging
from typing import Dict, Any

from langgraph.graph import StateGraph, END

from src.cias_x.state import AgentState
from src.cias_x.planner import CIASPlannerAgent
from src.cias_x.executor import CIASExecutorAgent
from src.cias_x.analyst import CIASAnalystAgent

logger = logging.getLogger(__name__)


def create_cias_workflow(
    planner: CIASPlannerAgent,
    executor: CIASExecutorAgent,
    analyst: CIASAnalystAgent
):
    """
    Create the CIAS-X workflow graph.

    Topology:
        planner -> executor -> analyst
             ^                    |
             |____________________|
                  (if budget > 0)
    """
    logger.info("Creating CIAS-X workflow graph")

    # Create graph
    workflow = StateGraph(AgentState)

    # Define node functions
    def planner_node(state: AgentState) -> Dict[str, Any]:
        return planner(state)

    async def executor_node(state: AgentState) -> Dict[str, Any]:
        return await executor(state)

    def analyst_node(state: AgentState) -> Dict[str, Any]:
        return analyst(state)

    # Add nodes
    workflow.add_node("planner", planner_node)
    workflow.add_node("executor", executor_node)
    workflow.add_node("analyst", analyst_node)

    # Set entry point
    workflow.set_entry_point("planner")

    # Define edges
    workflow.add_edge("planner", "executor")
    workflow.add_edge("executor", "analyst")

    # Conditional edge from analyst
    def should_continue(state: AgentState) -> str:
        """Determine whether to continue the loop."""
        if state.get("status") == "end":
            return "end"
        if state.get("budget_remaining", 0) <= 0 or state.get("token_remaining", 0) <= 0:
            return "end"
        return "planner"

    workflow.add_conditional_edges(
        "analyst",
        should_continue,
        {
            "planner": "planner",
            "end": END
        }
    )

    # Compile and return
    compiled = workflow.compile()
    logger.info("CIAS-X workflow compiled successfully")
    return compiled
