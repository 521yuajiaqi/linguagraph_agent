from lingua_agent.tools.exercise_generation import (
    build_exercise_blueprint,
    build_llm_exercise_messages,
    select_exercise_candidate,
    validate_generated_exercise_payload,
)


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


def test_select_exercise_candidate_prefers_focus_match():
    blueprint = build_exercise_blueprint(_state(focus_areas=["grammar"], user_level="B1"))
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
            "reference_translation": "Эта платформа фиксирует термины и создаёт словарные карточки.",
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
    blueprint = build_exercise_blueprint(_state(focus_areas=["grammar"], user_level="B1"))
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


def test_select_exercise_candidate_respects_explicit_empty_bank():
    blueprint = build_exercise_blueprint(_state(focus_areas=["grammar"], user_level="B1"))

    result = select_exercise_candidate("zh_ru", blueprint, previous_source="", bank=[])

    assert result is None


def test_select_exercise_candidate_prefers_terminology_match():
    blueprint = build_exercise_blueprint(
        _state(focus_areas=["terminology"], user_level="B1", domain="general")
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
            "source_text": "这个平台记录术语并生成词汇卡。",
            "reference_translation": "Эта платформа фиксирует термины и создаёт словарные карточки.",
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
    assert result["candidate"]["focus_tags"] == ["terminology"]


def test_blueprint_handles_unknown_focus_and_level():
    blueprint = build_exercise_blueprint(
        _state(focus_areas=["not-a-real-focus"], user_level="X9")
    )

    assert blueprint["primary_focus"] == "accuracy"
    assert blueprint["target_level"] == "X9"
    assert blueprint["difficulty_band"]["target"] == "B1"


def test_select_exercise_candidate_uses_score_then_focus_then_level():
    blueprint = build_exercise_blueprint(_state(focus_areas=["grammar"], user_level="B1"))
    bank = [
        {
            "source_text": "教师提醒学生注意语序和支配关系。",
            "reference_translation": "Преподаватель напоминает студентам обратить внимание на порядок слов и управление.",
            "language_pair": "zh_ru",
            "level": "A2",
            "focus_tags": ["grammar"],
            "syntax_load": "medium",
            "terminology_load": "low",
            "teaching_points": ["word_order", "governance"],
            "domain": "general",
        },
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
    ]

    result = select_exercise_candidate("zh_ru", blueprint, previous_source="", bank=bank)

    assert result is not None
    assert result["candidate"]["level"] == "B1"


def test_build_llm_exercise_messages_embeds_blueprint_constraints():
    blueprint = build_exercise_blueprint(_state(focus_areas=["grammar"], user_level="B1"))
    system, user = build_llm_exercise_messages(
        {"display_name": "中译俄"},
        "education",
        blueprint,
    )

    assert "严格 JSON" in system
    assert "主训练维度：grammar" in user
    assert "句法负荷：medium" in user
    assert "教学意图" in user


def test_validate_generated_exercise_payload_accepts_clean_payload():
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
        "reference_translation": "参考译文：Преподаватель напоминает студентам обратить внимание на порядок слов и глагольное управление。",
    }

    assert validate_generated_exercise_payload(payload, blueprint) is None


def test_validate_generated_exercise_payload_rejects_non_string_fields():
    blueprint = build_exercise_blueprint(_state(focus_areas=["grammar"], user_level="B1"))
    payload = {
        "source_text": ["教师提醒学生注意语序和动词支配关系。"],
        "reference_translation": {"text": "Преподаватель напоминает студентам обратить внимание на порядок слов и глагольное управление."},
    }

    assert validate_generated_exercise_payload(payload, blueprint) is None
