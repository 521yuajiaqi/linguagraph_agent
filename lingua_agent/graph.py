from __future__ import annotations

from langgraph.graph import END, StateGraph

from lingua_agent.nodes import (
    evaluate_translation,
    generate_exercise,
    initialize_context,
    plan_next_steps,
    reflect_on_evaluation,
    synthesize_feedback,
    terminology_check,
)
from lingua_agent.state import TranslationAgentState


def _route_task(state: TranslationAgentState) -> str:
    return "evaluate_translation" if state.get("task_type") == "evaluate_translation" else "generate_exercise"


def build_translation_graph():
    graph = StateGraph(TranslationAgentState)

    graph.add_node("initialize_context", initialize_context)
    graph.add_node("generate_exercise", generate_exercise)
    graph.add_node("evaluate_translation", evaluate_translation)
    graph.add_node("reflect_on_evaluation", reflect_on_evaluation)
    graph.add_node("terminology_check", terminology_check)
    graph.add_node("synthesize_feedback", synthesize_feedback)
    graph.add_node("plan_next_steps", plan_next_steps)

    graph.set_entry_point("initialize_context")
    graph.add_conditional_edges(
        "initialize_context",
        _route_task,
        {
            "generate_exercise": "generate_exercise",
            "evaluate_translation": "evaluate_translation",
        },
    )
    graph.add_edge("generate_exercise", "terminology_check")
    graph.add_edge("evaluate_translation", "reflect_on_evaluation")
    graph.add_edge("reflect_on_evaluation", "terminology_check")
    graph.add_edge("terminology_check", "synthesize_feedback")
    graph.add_edge("synthesize_feedback", "plan_next_steps")
    graph.add_edge("plan_next_steps", END)

    return graph.compile()
