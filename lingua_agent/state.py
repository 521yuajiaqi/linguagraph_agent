from __future__ import annotations

from typing import Any, Literal, NotRequired, TypedDict


TaskType = Literal["generate_exercise", "evaluate_translation"]


class TranslationAgentState(TypedDict, total=False):
    """Shared state passed through the LangGraph workflow.

    The state is intentionally language-pair neutral. Chinese-Russian support is
    provided by config and resources, not by hard-coded graph logic.
    """

    source_lang: str
    target_lang: str
    language_pair: str
    direction: str
    domain: str
    user_level: str
    mode: Literal["student", "teacher"]
    task_type: TaskType

    source_text: str
    user_translation: str
    reference_translation: str

    pair_config: dict[str, Any]
    terminology_hits: list[dict[str, str]]
    evaluation: dict[str, Any]
    diagnostics: dict[str, Any]
    grammar_analysis: dict[str, Any]
    vocabulary_cards: list[dict[str, Any]]
    mistake_record: dict[str, Any]
    learner_profile: dict[str, Any]
    review_plan: list[dict[str, Any]]
    dashboard: dict[str, Any]
    tool_trace: list[dict[str, str]]
    feedback: str
    next_exercises: list[dict[str, str]]
    report: str

    messages: NotRequired[list[dict[str, str]]]
    focus_areas: NotRequired[list[str]]
    error_history: NotRequired[list[dict[str, Any]]]
    session_summary: NotRequired[str]
    exercise_blueprint: NotRequired[dict[str, Any]]
    selected_exercise: NotRequired[dict[str, Any]]
