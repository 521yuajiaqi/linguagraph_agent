# Exercise Generation Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement weakness-driven translation exercise generation that picks a single pedagogical focus, keeps difficulty stable, prefers tagged bank selection, and uses constrained LLM fallback only when the bank cannot satisfy the blueprint.

**Architecture:** Add a new pure helper module for exercise blueprint construction, tagged candidate ranking, and fallback validation; keep `lingua_agent.nodes.generate_exercise` as the orchestration layer; and wire learner history from `web_app.py` into the generation request so the blueprint can use both explicit `focus_areas` and persistent learner risks.

**Tech Stack:** Python 3.11, FastAPI, LangGraph, pytest

**Workspace note:** `C:\Users\Win11\OneDrive\Code\Agent` is not currently a git repository. Each task includes a checkpoint step plus optional commit commands to use only if the user initializes git before execution.

---

### Task 1: Test Harness And Blueprint Schema

**Files:**
- Modify: `requirements.txt`
- Create: `tests/test_exercise_generation.py`
- Create: `lingua_agent/tools/exercise_generation.py`
- Modify: `lingua_agent/tools/__init__.py`
- Modify: `lingua_agent/state.py`

- [ ] **Step 1: Add pytest to the backend dependencies**

```text
fastapi
uvicorn[standard]
langgraph
langchain-openai
python-dotenv
PyYAML
pytest>=8.3,<9
```

- [ ] **Step 2: Install the updated requirements in the `nlp` environment**

Run:

```powershell
& "C:\Users\Win11\anaconda3\envs\nlp\python.exe" -m pip install -r requirements.txt
```

Expected: `Successfully installed` or `Requirement already satisfied` for `pytest`.

- [ ] **Step 3: Write the failing blueprint tests**

```python
from lingua_agent.tools.exercise_generation import build_exercise_blueprint


def _state(**overrides):
    state = {
        "language_pair": "zh_ru",
        "user_level": "B1",
        "domain": "general",
        "focus_areas": [],
        "learner_profile": {
            "performance_risks": [],
            "common_errors": [],
        },
        "error_history": [],
    }
    state.update(overrides)
    return state


def test_blueprint_prefers_explicit_focus_area():
    blueprint = build_exercise_blueprint(
        _state(
            focus_areas=["grammar"],
            learner_profile={"performance_risks": ["fluency"], "common_errors": []},
        )
    )

    assert blueprint["primary_focus"] == "grammar"
    assert blueprint["selection_reason"] == "explicit_focus_area"
    assert blueprint["target_level"] == "B1"


def test_blueprint_falls_back_to_learner_profile_risk():
    blueprint = build_exercise_blueprint(
        _state(
            learner_profile={
                "performance_risks": ["terminology", "grammar"],
                "common_errors": [],
            }
        )
    )

    assert blueprint["primary_focus"] == "terminology"
    assert blueprint["selection_reason"] == "learner_profile_risk"


def test_blueprint_reduces_load_after_repeated_errors():
    blueprint = build_exercise_blueprint(
        _state(
            focus_areas=["grammar"],
            error_history=[
                {"error_types": ["格错误"]},
                {"error_types": ["支配关系错误"]},
                {"error_types": ["格错误"]},
            ],
        )
    )

    assert blueprint["difficulty_band"]["target"] == "B1"
    assert blueprint["syntax_load"] == "medium"
    assert "terminology" in blueprint["avoid_overload_dimensions"]
```

- [ ] **Step 4: Run the focused test file to verify it fails before implementation**

Run:

```powershell
& "C:\Users\Win11\anaconda3\envs\nlp\python.exe" -m pytest tests\test_exercise_generation.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'lingua_agent.tools.exercise_generation'`.

- [ ] **Step 5: Implement the new blueprint module with narrow, testable types**

```python
from __future__ import annotations

from typing import Literal, TypedDict


FocusDimension = Literal["accuracy", "fluency", "terminology", "grammar", "strategy"]
LoadLevel = Literal["low", "medium", "high"]


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


LEVEL_ORDER = ["A1", "A2", "B1", "B2", "C1"]

FOCUS_INTENTS: dict[FocusDimension, str] = {
    "accuracy": "train complete transfer of all source information units",
    "fluency": "train natural target-language phrasing and collocation",
    "terminology": "train precise handling of domain terms and fixed expressions",
    "grammar": "train governance, word order, and clause-level grammar decisions",
    "strategy": "train restructuring and meaning-preserving reformulation",
}


def _normalize_focus(value: str | None) -> FocusDimension | None:
    valid = {"accuracy", "fluency", "terminology", "grammar", "strategy"}
    return value if value in valid else None


def _difficulty_band_for_level(level: str) -> DifficultyBand:
    index = LEVEL_ORDER.index(level) if level in LEVEL_ORDER else LEVEL_ORDER.index("B1")
    floor = LEVEL_ORDER[max(0, index - 1)]
    target = LEVEL_ORDER[index]
    ceiling = LEVEL_ORDER[min(len(LEVEL_ORDER) - 1, index)]
    return {"floor": floor, "target": target, "ceiling": ceiling}


def build_exercise_blueprint(state: dict) -> ExerciseBlueprint:
    focus_areas = state.get("focus_areas", []) or []
    learner_profile = state.get("learner_profile", {}) or {}
    performance_risks = learner_profile.get("performance_risks", []) or []
    recent_errors = state.get("error_history", []) or []

    primary_focus = _normalize_focus(focus_areas[0] if focus_areas else None)
    reason = "explicit_focus_area"

    if primary_focus is None:
        primary_focus = _normalize_focus(performance_risks[0] if performance_risks else None) or "accuracy"
        reason = "learner_profile_risk" if performance_risks else "default_accuracy"

    grammar_pressure = sum(
        1
        for item in recent_errors
        for error_type in item.get("error_types", [])
        if error_type in {"格错误", "支配关系错误", "前置词搭配错误", "动词体错误", "词序错误"}
    )

    syntax_load: LoadLevel = "medium" if primary_focus == "grammar" else "low"
    terminology_load: LoadLevel = "medium" if primary_focus == "terminology" else "low"
    avoid_overload_dimensions: list[str] = []

    if grammar_pressure >= 2:
        syntax_load = "medium"
        terminology_load = "low"
        avoid_overload_dimensions.append("terminology")

    return {
        "primary_focus": primary_focus,
        "target_level": state.get("user_level", "B1"),
        "difficulty_band": _difficulty_band_for_level(state.get("user_level", "B1")),
        "syntax_load": syntax_load,
        "terminology_load": terminology_load,
        "teaching_intent": FOCUS_INTENTS[primary_focus],
        "selection_reason": reason,
        "avoid_overload_dimensions": avoid_overload_dimensions,
        "preferred_domain": state.get("domain", "general"),
        "recent_error_tags": [
            error_type
            for item in recent_errors
            for error_type in item.get("error_types", [])
        ],
    }
```

- [ ] **Step 6: Export the helper and add state fields for later orchestration**

```python
# lingua_agent/tools/__init__.py
from lingua_agent.tools.exercise_generation import build_exercise_blueprint
```

```python
# lingua_agent/state.py
    exercise_blueprint: NotRequired[dict[str, Any]]
    selected_exercise: NotRequired[dict[str, Any]]
```

- [ ] **Step 7: Re-run the focused tests to verify the blueprint contract passes**

Run:

```powershell
& "C:\Users\Win11\anaconda3\envs\nlp\python.exe" -m pytest tests\test_exercise_generation.py -v
```

Expected: 3 passed.

- [ ] **Step 8: Save a checkpoint for the schema baseline**

Run:

```powershell
git rev-parse --show-toplevel
```

Expected in the current workspace: `fatal: not a git repository`.

If the user initializes git before execution, then run:

```powershell
git add requirements.txt tests\test_exercise_generation.py lingua_agent\tools\exercise_generation.py lingua_agent\tools\__init__.py lingua_agent\state.py
git commit -m "test: add exercise blueprint baseline"
```

### Task 2: Tagged Exercise Bank And Candidate Ranking

**Files:**
- Modify: `tests/test_exercise_generation.py`
- Modify: `lingua_agent/tools/exercise_generation.py`

- [ ] **Step 1: Extend the test file with candidate ranking expectations**

```python
from lingua_agent.tools.exercise_generation import (
    build_exercise_blueprint,
    select_exercise_candidate,
)


def test_select_exercise_candidate_prefers_focus_match():
    blueprint = build_exercise_blueprint(
        _state(focus_areas=["grammar"], user_level="B1")
    )
    bank = [
        {
            "source_text": "教师提醒学生注意语序和支配关系。",
            "reference_translation": "Преподаватель напоминает студентам обратить внимание на порядок слов и управление.",
            "language_pair": "zh_ru",
            "level": "B1",
            "focus_tags": ["grammar"],
            "syntax_load": "medium",
            "terminology_load": "low",
            "teaching_points": ["word_order", "governance"],
            "domain": "general",
        },
        {
            "source_text": "这个平台记录术语并生成词汇卡。",
            "reference_translation": "Эта платформа фиксирует термины и создает словарные карточки.",
            "language_pair": "zh_ru",
            "level": "B1",
            "focus_tags": ["terminology"],
            "syntax_load": "low",
            "terminology_load": "medium",
            "teaching_points": ["term_precision"],
            "domain": "general",
        },
    ]

    result = select_exercise_candidate("zh_ru", blueprint, previous_source="", bank=bank)

    assert result is not None
    assert result["candidate"]["focus_tags"] == ["grammar"]
    assert result["matched_focus"] is True


def test_select_exercise_candidate_avoids_repeating_previous_source():
    blueprint = build_exercise_blueprint(
        _state(focus_areas=["grammar"], user_level="B1")
    )
    bank = [
        {
            "source_text": "学生先分析主干，再处理从句。",
            "reference_translation": "Студент сначала анализирует основу, а затем обрабатывает придаточное предложение.",
            "language_pair": "zh_ru",
            "level": "B1",
            "focus_tags": ["grammar"],
            "syntax_load": "medium",
            "terminology_load": "low",
            "teaching_points": ["clause_structure"],
            "domain": "general",
        },
        {
            "source_text": "他们虽然时间很紧，还是完成了初稿。",
            "reference_translation": "Хотя у них было мало времени, они все же завершили черновик.",
            "language_pair": "zh_ru",
            "level": "B1",
            "focus_tags": ["grammar"],
            "syntax_load": "medium",
            "terminology_load": "low",
            "teaching_points": ["concessive_structure"],
            "domain": "general",
        },
    ]

    result = select_exercise_candidate(
        "zh_ru",
        blueprint,
        previous_source="学生先分析主干，再处理从句。",
        bank=bank,
    )

    assert result is not None
    assert result["candidate"]["source_text"] == "他们虽然时间很紧，还是完成了初稿。"
```

- [ ] **Step 2: Run the ranking tests and confirm the missing function failure**

Run:

```powershell
& "C:\Users\Win11\anaconda3\envs\nlp\python.exe" -m pytest tests\test_exercise_generation.py -v
```

Expected: FAIL with `ImportError` or `AttributeError` for `select_exercise_candidate`.

- [ ] **Step 3: Add tagged bank entries and deterministic ranking helpers**

```python
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


TAGGED_EXERCISE_BANK: dict[str, list[ExerciseCandidate]] = {
    "zh_ru": [
        {
            "source_text": "尽管天气不好，他们还是决定去公园散步。",
            "reference_translation": "Несмотря на плохую погоду, они всё же решили пойти в парк на прогулку.",
            "language_pair": "zh_ru",
            "level": "A2",
            "focus_tags": ["grammar", "accuracy"],
            "syntax_load": "medium",
            "terminology_load": "low",
            "teaching_points": ["concessive_structure", "main_clause_order"],
            "domain": "general",
        },
        {
            "source_text": "教师提醒学生注意语序和动词支配关系。",
            "reference_translation": "Преподаватель напоминает студентам обратить внимание на порядок слов и глагольное управление.",
            "language_pair": "zh_ru",
            "level": "B1",
            "focus_tags": ["grammar"],
            "syntax_load": "medium",
            "terminology_load": "low",
            "teaching_points": ["governance", "word_order"],
            "domain": "education",
        },
        {
            "source_text": "系统会记录关键词，并在复习时再次呈现这些术语。",
            "reference_translation": "Система фиксирует ключевые слова и снова предъявляет эти термины во время повторения.",
            "language_pair": "zh_ru",
            "level": "B1",
            "focus_tags": ["terminology"],
            "syntax_load": "low",
            "terminology_load": "medium",
            "teaching_points": ["term_precision", "review_language"],
            "domain": "education",
        },
    ],
    "ru_zh": [
        {
            "source_text": "Преподаватель объясняет, почему здесь нужен другой падеж.",
            "reference_translation": "教师解释为什么这里需要使用另一个格。",
            "language_pair": "ru_zh",
            "level": "B1",
            "focus_tags": ["grammar"],
            "syntax_load": "medium",
            "terminology_load": "low",
            "teaching_points": ["case_selection", "clause_linking"],
            "domain": "education",
        }
    ],
}


LOAD_SCORE = {"low": 0, "medium": 1, "high": 2}


def _score_candidate(candidate: ExerciseCandidate, blueprint: ExerciseBlueprint, previous_source: str) -> int:
    score = 0
    if candidate["level"] == blueprint["target_level"]:
        score += 4
    elif candidate["level"] in {
        blueprint["difficulty_band"]["floor"],
        blueprint["difficulty_band"]["ceiling"],
    }:
        score += 2

    if blueprint["primary_focus"] in candidate["focus_tags"]:
        score += 6

    if candidate["source_text"] == previous_source:
        score -= 5

    if candidate["domain"] == blueprint.get("preferred_domain"):
        score += 1

    if candidate["syntax_load"] == blueprint["syntax_load"]:
        score += 2
    if candidate["terminology_load"] == blueprint["terminology_load"]:
        score += 2

    for dimension in blueprint.get("avoid_overload_dimensions", []):
        if dimension == "terminology" and candidate["terminology_load"] == "high":
            score -= 3
        if dimension == "grammar" and candidate["syntax_load"] == "high":
            score -= 3

    return score


def select_exercise_candidate(
    language_pair: str,
    blueprint: ExerciseBlueprint,
    previous_source: str,
    bank: list[ExerciseCandidate] | None = None,
) -> ExerciseSelectionResult | None:
    candidates = bank or TAGGED_EXERCISE_BANK.get(language_pair, [])
    ranked: list[ExerciseSelectionResult] = []

    for candidate in candidates:
        if candidate["language_pair"] != language_pair:
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

    ranked.sort(key=lambda item: item["score"], reverse=True)
    return ranked[0] if ranked else None
```

- [ ] **Step 4: Re-run the ranking tests and confirm deterministic selection**

Run:

```powershell
& "C:\Users\Win11\anaconda3\envs\nlp\python.exe" -m pytest tests\test_exercise_generation.py -v
```

Expected: 5 passed.

- [ ] **Step 5: Save a checkpoint for bank tagging and ranking**

Run:

```powershell
git rev-parse --show-toplevel
```

Expected in the current workspace: `fatal: not a git repository`.

If the user initializes git before execution, then run:

```powershell
git add tests\test_exercise_generation.py lingua_agent\tools\exercise_generation.py
git commit -m "feat: rank tagged exercise candidates by blueprint"
```

### Task 3: Constrained LLM Fallback Validation

**Files:**
- Modify: `tests/test_exercise_generation.py`
- Modify: `lingua_agent/tools/exercise_generation.py`

- [ ] **Step 1: Add tests for fallback payload validation**

```python
from lingua_agent.tools.exercise_generation import (
    build_exercise_blueprint,
    validate_generated_exercise_payload,
)


def test_validate_generated_exercise_payload_accepts_clean_translation_pair():
    blueprint = build_exercise_blueprint(_state(focus_areas=["grammar"], user_level="B1"))
    payload = {
        "source_text": "教师提醒学生注意语序和动词支配关系。",
        "reference_translation": "Преподаватель напоминает студентам обратить внимание на порядок слов и глагольное управление.",
    }

    validated = validate_generated_exercise_payload(payload, blueprint)

    assert validated is not None
    assert validated["source_text"].startswith("教师提醒学生")


def test_validate_generated_exercise_payload_rejects_missing_reference_translation():
    blueprint = build_exercise_blueprint(_state(focus_areas=["grammar"], user_level="B1"))
    payload = {
        "source_text": "教师提醒学生注意语序和动词支配关系。",
        "reference_translation": "",
    }

    assert validate_generated_exercise_payload(payload, blueprint) is None


def test_validate_generated_exercise_payload_rejects_explanation_leak():
    blueprint = build_exercise_blueprint(_state(focus_areas=["grammar"], user_level="B1"))
    payload = {
        "source_text": "下面是一道练习：教师提醒学生注意语序和动词支配关系。",
        "reference_translation": "参考译文：Преподаватель напоминает студентам обратить внимание на порядок слов и глагольное управление.",
    }

    assert validate_generated_exercise_payload(payload, blueprint) is None
```

- [ ] **Step 2: Run the fallback validation tests and confirm the new helper is missing**

Run:

```powershell
& "C:\Users\Win11\anaconda3\envs\nlp\python.exe" -m pytest tests\test_exercise_generation.py -v
```

Expected: FAIL with `ImportError` or `AttributeError` for `validate_generated_exercise_payload`.

- [ ] **Step 3: Implement a constrained prompt builder and payload validator**

```python
from lingua_agent.tools.learning import estimate_difficulty


def build_llm_exercise_messages(
    pair_config: dict,
    domain: str,
    blueprint: ExerciseBlueprint,
) -> tuple[str, str]:
    system = (
        "你是翻译教学专家。"
        "你必须输出严格 JSON，不得输出解释、标题、代码块或额外说明。"
    )
    user = (
        f"语种方向：{pair_config['display_name']}\n"
        f"领域：{domain}\n"
        f"主训练维度：{blueprint['primary_focus']}\n"
        f"目标等级：{blueprint['target_level']}\n"
        f"难度窗口：{blueprint['difficulty_band']['floor']} - {blueprint['difficulty_band']['ceiling']}\n"
        f"句法负荷：{blueprint['syntax_load']}\n"
        f"术语负荷：{blueprint['terminology_load']}\n"
        f"教学意图：{blueprint['teaching_intent']}\n"
        '请输出 {"source_text": "...", "reference_translation": "..."}'
    )
    return system, user


def validate_generated_exercise_payload(
    payload: dict | None,
    blueprint: ExerciseBlueprint,
) -> dict[str, str] | None:
    if not payload:
        return None

    source_text = str(payload.get("source_text", "")).strip()
    reference_translation = str(payload.get("reference_translation", "")).strip()

    if not source_text or not reference_translation:
        return None

    forbidden_prefixes = ("下面是一道练习", "练习：", "source_text:", "原文：", "参考译文：")
    if source_text.startswith(forbidden_prefixes):
        return None
    if reference_translation.startswith(("参考译文：", "reference_translation:")):
        return None

    difficulty = estimate_difficulty(source_text, blueprint["target_level"])
    if difficulty["estimated_level"] not in {
        blueprint["difficulty_band"]["floor"],
        blueprint["difficulty_band"]["target"],
        blueprint["difficulty_band"]["ceiling"],
    }:
        return None

    return {
        "source_text": source_text,
        "reference_translation": reference_translation,
    }
```

- [ ] **Step 4: Re-run the focused tests and confirm fallback validation now passes**

Run:

```powershell
& "C:\Users\Win11\anaconda3\envs\nlp\python.exe" -m pytest tests\test_exercise_generation.py -v
```

Expected: 8 passed.

- [ ] **Step 5: Save a checkpoint for the constrained fallback layer**

Run:

```powershell
git rev-parse --show-toplevel
```

Expected in the current workspace: `fatal: not a git repository`.

If the user initializes git before execution, then run:

```powershell
git add tests\test_exercise_generation.py lingua_agent\tools\exercise_generation.py
git commit -m "feat: validate constrained exercise fallback payloads"
```

### Task 4: Node Orchestration And Session Signal Wiring

**Files:**
- Create: `tests/test_generate_exercise_node.py`
- Create: `tests/test_web_app_practice_generate.py`
- Modify: `lingua_agent/nodes.py`
- Modify: `lingua_agent/tools/__init__.py`
- Modify: `web_app.py`

- [ ] **Step 1: Write the node-level and endpoint-level failing tests**

```python
# tests/test_generate_exercise_node.py
from lingua_agent.nodes import generate_exercise, initialize_context


def _base_state(**overrides):
    state = initialize_context(
        {
            "language_pair": "zh_ru",
            "user_level": "B1",
            "domain": "education",
            "task_type": "generate_exercise",
            "focus_areas": ["grammar"],
            "learner_profile": {"performance_risks": ["grammar"], "common_errors": []},
            "error_history": [{"error_types": ["格错误"]}],
            "source_text": "",
        }
    )
    state.update(overrides)
    return state


def test_generate_exercise_prefers_ranked_bank_candidate(monkeypatch):
    from lingua_agent import nodes

    def fail_if_called(*args, **kwargs):
        raise AssertionError("LLM should not run when a ranked bank candidate exists")

    monkeypatch.setattr(nodes.llm, "complete", fail_if_called)

    result = generate_exercise(_base_state())

    assert result["exercise_blueprint"]["primary_focus"] == "grammar"
    assert result["selected_exercise"]["source_text"]
    assert any(item["tool"] == "出题画像工具" for item in result["tool_trace"])


def test_generate_exercise_falls_back_to_safe_bank_after_invalid_llm(monkeypatch):
    from lingua_agent import nodes

    monkeypatch.setattr(nodes, "select_exercise_candidate", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        nodes.llm,
        "complete",
        lambda *args, **kwargs: '{"source_text": "下面是一道练习：请翻译。", "reference_translation": ""}',
    )

    result = generate_exercise(_base_state())

    assert result["source_text"]
    assert result["reference_translation"]
    assert any("兜底" in item["result"] for item in result["tool_trace"])
```

```python
# tests/test_web_app_practice_generate.py
from web_app import PracticeGenerateRequest, practice_generate


class _FakeGraph:
    def __init__(self):
        self.calls = []

    def invoke(self, payload):
        self.calls.append(payload)
        return {
            "source_text": "教师提醒学生注意语序和动词支配关系。",
            "reference_translation": "Преподаватель напоминает студентам обратить внимание на порядок слов и глагольное управление.",
            "evaluation": {"hints": {}, "difficulty": {}},
            "diagnostics": {},
            "vocabulary_cards": [],
            "grammar_analysis": {},
        }


def test_practice_generate_passes_learner_signals(monkeypatch):
    import web_app

    fake_graph = _FakeGraph()
    session = {
        "language_pair": "zh_ru",
        "user_level": "B1",
        "domain": "education",
        "mode": "student",
        "learner_profile": {"performance_risks": ["grammar"], "common_errors": []},
        "mistakes": [{"error_types": ["格错误"], "reason": "支配关系不稳"}],
    }

    monkeypatch.setattr(web_app, "_load_session", lambda session_id: session)
    monkeypatch.setattr(web_app, "_save_session", lambda session_id, payload: None)
    monkeypatch.setattr(web_app, "get_graph", lambda: fake_graph)

    practice_generate(
        PracticeGenerateRequest(session_id="s1", focus_areas=["grammar"], domain="education")
    )

    sent = fake_graph.calls[0]
    assert sent["focus_areas"] == ["grammar"]
    assert sent["learner_profile"]["performance_risks"] == ["grammar"]
    assert sent["error_history"][0]["error_types"] == ["格错误"]
```

- [ ] **Step 2: Run the new tests and confirm the orchestration gaps**

Run:

```powershell
& "C:\Users\Win11\anaconda3\envs\nlp\python.exe" -m pytest tests\test_generate_exercise_node.py tests\test_web_app_practice_generate.py -v
```

Expected: FAIL because `generate_exercise` does not yet populate `exercise_blueprint` or `selected_exercise`, and `practice_generate` does not pass learner history into the graph request.

- [ ] **Step 3: Refactor `generate_exercise` into blueprint -> rank -> fallback orchestration**

```python
# lingua_agent/nodes.py
from lingua_agent.tools import (
    analyze_grammar,
    build_exercise_blueprint,
    build_llm_exercise_messages,
    build_vocabulary_cards,
    create_mistake_record,
    create_review_plan,
    diagnose_level,
    estimate_difficulty,
    generate_layered_hints,
    score_translation,
    select_exercise_candidate,
    validate_generated_exercise_payload,
    validate_llm_evaluation,
)


def _safe_bank_candidate(language_pair: str, previous_source: str = "") -> dict[str, str]:
    selection = select_exercise_candidate(
        language_pair,
        {
            "primary_focus": "accuracy",
            "target_level": "A2",
            "difficulty_band": {"floor": "A1", "target": "A2", "ceiling": "A2"},
            "syntax_load": "low",
            "terminology_load": "low",
            "teaching_intent": "safe fallback",
            "selection_reason": "safe_fallback",
            "avoid_overload_dimensions": [],
        },
        previous_source,
    )
    return selection["candidate"] if selection else {
        "source_text": "学生每天练习翻译。",
        "reference_translation": "Студенты каждый день практикуют перевод.",
    }


def generate_exercise(state: TranslationAgentState) -> TranslationAgentState:
    config = state["pair_config"]
    previous_source = state.get("source_text", "")
    blueprint = build_exercise_blueprint(state)
    selection = select_exercise_candidate(
        state["language_pair"],
        blueprint,
        previous_source,
    )

    generated = ""
    if selection is not None:
        source_text = selection["candidate"]["source_text"]
        reference = selection["candidate"]["reference_translation"]
        exercise_source = "题库"
        selection_result = selection["candidate"]
    else:
        system, user = build_llm_exercise_messages(config, state["domain"], blueprint)
        generated = llm.complete(system, user)
        parsed = _parse_json_from_llm(generated)
        validated = validate_generated_exercise_payload(parsed, blueprint)
        if validated is not None:
            source_text = _normalize_exercise_text(validated["source_text"])
            reference = _normalize_exercise_text(validated["reference_translation"])
            exercise_source = "LLM fallback"
            selection_result = validated
        else:
            safe_candidate = _safe_bank_candidate(state["language_pair"], previous_source)
            source_text = safe_candidate["source_text"]
            reference = safe_candidate["reference_translation"]
            exercise_source = "题库兜底"
            selection_result = safe_candidate

    hints = generate_layered_hints(source_text, reference, config)
    diagnostics = diagnose_level(source_text, "", state["user_level"], config)
    difficulty_result = estimate_difficulty(source_text, state["user_level"])

    return {
        **state,
        "source_text": source_text,
        "reference_translation": reference,
        "exercise_blueprint": blueprint,
        "selected_exercise": selection_result,
        "diagnostics": diagnostics,
        "evaluation": {
            "hints": hints,
            "difficulty": difficulty_result,
        },
        "feedback": generated,
        "tool_trace": [
            {"tool": "出题画像工具", "result": f"{blueprint['primary_focus']} | {blueprint['selection_reason']}"},
            {"tool": "题库排序工具", "result": f"已使用{exercise_source}完成选题"},
            {"tool": "分层提示工具", "result": "已准备词汇、结构、语法和半句提示"},
        ],
    }
```

- [ ] **Step 4: Pass learner profile and mistake history into the generation request**

```python
# web_app.py
agent_input = _build_agent_request(
    session,
    "generate_exercise",
    {
        "domain": payload.domain or session.get("domain", "general"),
        "focus_areas": payload.focus_areas or [],
        "source_text": current_exercise.get("source_text", ""),
        "learner_profile": session.get("learner_profile", {}),
        "error_history": session.get("mistakes", []),
    },
)
```

- [ ] **Step 5: Export the new helpers from `lingua_agent.tools`**

```python
# lingua_agent/tools/__init__.py
from lingua_agent.tools.exercise_generation import (
    build_exercise_blueprint,
    build_llm_exercise_messages,
    select_exercise_candidate,
    validate_generated_exercise_payload,
)

__all__ = [
    "analyze_grammar",
    "build_dashboard",
    "build_exercise_blueprint",
    "build_learner_profile",
    "build_llm_exercise_messages",
    "build_vocabulary_cards",
    "create_mistake_record",
    "create_review_plan",
    "diagnose_level",
    "estimate_difficulty",
    "generate_layered_hints",
    "score_translation",
    "select_exercise_candidate",
    "validate_generated_exercise_payload",
    "validate_llm_evaluation",
]
```

- [ ] **Step 6: Re-run the orchestration and request wiring tests**

Run:

```powershell
& "C:\Users\Win11\anaconda3\envs\nlp\python.exe" -m pytest tests\test_generate_exercise_node.py tests\test_web_app_practice_generate.py -v
```

Expected: 3 passed.

- [ ] **Step 7: Save a checkpoint for backend orchestration**

Run:

```powershell
git rev-parse --show-toplevel
```

Expected in the current workspace: `fatal: not a git repository`.

If the user initializes git before execution, then run:

```powershell
git add tests\test_generate_exercise_node.py tests\test_web_app_practice_generate.py lingua_agent\nodes.py lingua_agent\tools\__init__.py web_app.py
git commit -m "feat: orchestrate blueprint-driven exercise generation"
```

### Task 5: Documentation And Full Regression Pass

**Files:**
- Modify: `README.md`
- Modify: `CLAUDE.md`

- [ ] **Step 1: Update the architecture docs so the next engineer sees the new bank-first flow**

```markdown
## 后端架构

### 练习生成（新版）

`generate_exercise` 现在采用：

1. 构建 `ExerciseBlueprint`
2. 从带标签题库中按弱项和难度排序选题
3. 仅在题库无法满足时使用受约束的 LLM fallback
4. 对 fallback 输出做结构与难度校验

当前第一轮只覆盖翻译题，不扩展改错或填空题。
```

- [ ] **Step 2: Run the complete focused regression suite**

Run:

```powershell
& "C:\Users\Win11\anaconda3\envs\nlp\python.exe" -m pytest tests\test_exercise_generation.py tests\test_generate_exercise_node.py tests\test_web_app_practice_generate.py -v
```

Expected: all tests passed.

- [ ] **Step 3: Run a CLI smoke check against the bank-first path**

Run:

```powershell
& "C:\Users\Win11\anaconda3\envs\nlp\python.exe" main.py --pair zh_ru --level B1 --domain education --task generate_exercise
```

Expected: the command completes without a traceback and prints a generated exercise report.

- [ ] **Step 4: Save a final checkpoint for docs and regression completion**

Run:

```powershell
git rev-parse --show-toplevel
```

Expected in the current workspace: `fatal: not a git repository`.

If the user initializes git before execution, then run:

```powershell
git add README.md CLAUDE.md
git commit -m "docs: describe blueprint-driven exercise generation"
```
