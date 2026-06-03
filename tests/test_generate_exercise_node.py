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
