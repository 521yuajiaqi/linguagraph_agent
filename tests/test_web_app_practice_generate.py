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
