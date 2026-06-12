from __future__ import annotations

from typing import Any, Literal, Mapping, TypedDict

from lingua_agent.prompts import build_exercise_generation_prompt
from lingua_agent.state import TranslationAgentState


FocusDimension = Literal["accuracy", "fluency", "terminology", "grammar", "strategy"]
LoadLevel = Literal["low", "medium", "high"]

LEVEL_ORDER = ["A1", "A2", "B1", "B2", "C1"]
GRAMMAR_ERROR_TYPES = {"格错误", "支配关系错误", "前置词搭配错误", "动词体错误", "词序错误"}


class DifficultyBand(TypedDict):
    floor: str
    target: str
    ceiling: str


class ExerciseBlueprint(TypedDict, total=False):
    primary_focus: FocusDimension
    target_level: str
    difficulty_band: DifficultyBand
    syntax_load: LoadLevel
    terminology_load: LoadLevel
    teaching_intent: str
    selection_reason: str
    avoid_overload_dimensions: list[str]
    preferred_domain: str
    recent_error_tags: list[str]


class ExerciseCandidate(TypedDict):
    source_text: str
    reference_translation: str
    language_pair: str
    level: str
    focus_tags: list[FocusDimension]
    syntax_load: LoadLevel
    terminology_load: LoadLevel
    teaching_points: list[str]
    domain: str


class ExerciseSelectionResult(TypedDict):
    candidate: ExerciseCandidate
    score: int
    matched_focus: bool
    matched_level: bool
    match_reason: str


FOCUS_INTENTS: dict[FocusDimension, str] = {
    "accuracy": "train complete transfer of all source information units",
    "fluency": "train natural target-language phrasing and collocation",
    "terminology": "train precise handling of domain terms and fixed expressions",
    "grammar": "train governance, word order, and clause-level grammar decisions",
    "strategy": "train restructuring and meaning-preserving reformulation",
}

LOAD_SCORE = {"low": 0, "medium": 1, "high": 2}

_EXERCISE_CACHE: dict[str, list[ExerciseCandidate]] = {}


def _load_exercise_bank(language_pair: str) -> list[ExerciseCandidate]:
    """Load tagged exercise bank from JSON file with in-memory cache."""
    if language_pair in _EXERCISE_CACHE:
        return _EXERCISE_CACHE[language_pair]

    import json
    from pathlib import Path

    json_path = Path(__file__).resolve().parents[2] / "resources" / "exercises" / f"{language_pair}.json"
    if not json_path.exists():
        _EXERCISE_CACHE[language_pair] = []
        return []

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    candidates: list[ExerciseCandidate] = []
    valid_focus_tags = {"accuracy", "fluency", "terminology", "grammar", "strategy"}
    for item in data:
        candidates.append({
            "source_text": str(item.get("source_text", "")),
            "reference_translation": str(item.get("reference_translation", "")),
            "language_pair": str(item.get("language_pair", language_pair)),
            "level": str(item.get("level", "B1")),
            "focus_tags": [t for t in item.get("focus_tags", []) if t in valid_focus_tags],
            "syntax_load": str(item.get("syntax_load", "low")),
            "terminology_load": str(item.get("terminology_load", "low")),
            "teaching_points": [str(p) for p in item.get("teaching_points", [])],
            "domain": str(item.get("domain", "general")),
        })

    _EXERCISE_CACHE[language_pair] = candidates
    return candidates


def _normalize_focus(value: str | None) -> FocusDimension | None:
    valid = {"accuracy", "fluency", "terminology", "grammar", "strategy"}
    return value if value in valid else None


def _difficulty_band_for_level(level: str) -> DifficultyBand:
    index = LEVEL_ORDER.index(level) if level in LEVEL_ORDER else LEVEL_ORDER.index("B1")
    floor = LEVEL_ORDER[max(0, index - 1)]
    target = LEVEL_ORDER[index]
    ceiling = LEVEL_ORDER[index]
    return {"floor": floor, "target": target, "ceiling": ceiling}


def _score_candidate(candidate: ExerciseCandidate, blueprint: ExerciseBlueprint, previous_source: str) -> int:
    score = 0
    if candidate["level"] == blueprint["target_level"]:
        score += 6
    elif candidate["level"] in {blueprint["difficulty_band"]["floor"], blueprint["difficulty_band"]["ceiling"]}:
        score += 3
    else:
        # Severe penalty for level mismatch (prevents A1 exercise for C1 user)
        candidate_idx = LEVEL_ORDER.index(candidate["level"]) if candidate["level"] in LEVEL_ORDER else 2
        blueprint_idx = LEVEL_ORDER.index(blueprint["target_level"]) if blueprint["target_level"] in LEVEL_ORDER else 2
        level_gap = abs(candidate_idx - blueprint_idx)
        score -= level_gap * 4

    if blueprint["primary_focus"] in candidate["focus_tags"]:
        score += 6

    if candidate["domain"] == blueprint.get("preferred_domain"):
        score += 1

    if candidate["syntax_load"] == blueprint["syntax_load"]:
        score += 2
    else:
        score -= LOAD_SCORE[candidate["syntax_load"]]

    if candidate["terminology_load"] == blueprint["terminology_load"]:
        score += 2
    else:
        score -= LOAD_SCORE[candidate["terminology_load"]]

    if candidate["source_text"] == previous_source:
        score -= 5

    if "terminology" in blueprint.get("avoid_overload_dimensions", []) and candidate["terminology_load"] == "high":
        score -= 3
    if "grammar" in blueprint.get("avoid_overload_dimensions", []) and candidate["syntax_load"] == "high":
        score -= 3

    return score


def select_exercise_candidate(
    language_pair: str,
    blueprint: ExerciseBlueprint,
    previous_source: str,
    bank: list[ExerciseCandidate] | None = None,
) -> ExerciseSelectionResult | None:
    candidates = _load_exercise_bank(language_pair) if bank is None else bank
    ranked: list[ExerciseSelectionResult] = []

    for candidate in candidates:
        if candidate["language_pair"] != language_pair:
            continue
        if previous_source and candidate["source_text"] == previous_source:
            continue
        score = _score_candidate(candidate, blueprint, previous_source)
        if score < 4:
            continue
        ranked.append(
            {
                "candidate": candidate,
                "score": score,
                "matched_focus": blueprint["primary_focus"] in candidate["focus_tags"],
                "matched_level": candidate["level"] == blueprint["target_level"],
                "match_reason": blueprint["selection_reason"],
            }
        )

    ranked.sort(key=lambda item: (item["score"], item["matched_focus"], item["matched_level"]), reverse=True)
    return ranked[0] if ranked else None


def build_llm_exercise_messages(
    pair_config: Mapping[str, Any],
    domain: str,
    blueprint: ExerciseBlueprint,
) -> tuple[str, str]:
    return build_exercise_generation_prompt(
        display_name=pair_config["display_name"],
        domain=domain,
        blueprint=blueprint,
    )


def validate_generated_exercise_payload(
    payload: Mapping[str, Any] | None,
    blueprint: ExerciseBlueprint,
) -> dict[str, str] | None:
    if not payload:
        return None

    source_text_value = payload.get("source_text")
    reference_translation_value = payload.get("reference_translation")
    if not isinstance(source_text_value, str) or not isinstance(reference_translation_value, str):
        return None

    source_text = source_text_value.strip()
    reference_translation = reference_translation_value.strip()

    if not source_text or not reference_translation:
        return None

    forbidden_prefixes = ("下面是一道练习", "练习：", "source_text:", "原文：", "参考译文：")
    if source_text.startswith(forbidden_prefixes):
        return None
    if reference_translation.startswith(("参考译文：", "reference_translation:")):
        return None

    if any(marker in source_text for marker in ("JSON", "json", "代码块")):
        return None
    if any(marker in reference_translation for marker in ("JSON", "json", "代码块")):
        return None

    if blueprint["primary_focus"] == "grammar" and len(source_text) < 4:
        return None

    return {
        "source_text": source_text,
        "reference_translation": reference_translation,
    }


def build_exercise_blueprint(state: Mapping[str, Any] | TranslationAgentState) -> ExerciseBlueprint:
    focus_areas = state.get("focus_areas", []) or []
    learner_profile = state.get("learner_profile", {}) or {}
    performance_risks = learner_profile.get("performance_risks", []) or []
    recent_errors = state.get("error_history", []) or []

    primary_focus = _normalize_focus(focus_areas[0] if focus_areas else None)
    selection_reason = "explicit_focus_area"

    if primary_focus is None:
        primary_focus = _normalize_focus(performance_risks[0] if performance_risks else None) or "accuracy"
        selection_reason = "learner_profile_risk" if performance_risks else "default_accuracy"

    recent_error_tags = [
        str(error_type)
        for item in recent_errors
        for error_type in item.get("error_types", [])
    ]
    grammar_pressure = sum(1 for error_type in recent_error_tags if error_type in GRAMMAR_ERROR_TYPES)

    syntax_load: LoadLevel = "medium" if primary_focus == "grammar" else "low"
    terminology_load: LoadLevel = "medium" if primary_focus == "terminology" else "low"
    avoid_overload_dimensions: list[str] = []

    if grammar_pressure >= 2:
        syntax_load = "medium"
        terminology_load = "low"
        avoid_overload_dimensions.append("terminology")

    user_level = state.get("user_level", "B1")
    return {
        "primary_focus": primary_focus,
        "target_level": user_level,
        "difficulty_band": _difficulty_band_for_level(user_level),
        "syntax_load": syntax_load,
        "terminology_load": terminology_load,
        "teaching_intent": FOCUS_INTENTS[primary_focus],
        "selection_reason": selection_reason,
        "avoid_overload_dimensions": avoid_overload_dimensions,
        "preferred_domain": state.get("domain", "general"),
        "recent_error_tags": recent_error_tags,
    }
