from __future__ import annotations

import json
import uuid
from collections import Counter
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from lingua_agent.diagnosis import evaluate_diagnosis_answers, generate_diagnosis_questions
from lingua_agent.graph import build_translation_graph
from lingua_agent.tools.learning import compute_ability_stats

# ---- Session Store ----
SESSIONS_DIR = Path(__file__).resolve().parent / ".sessions"
SESSIONS_DIR.mkdir(exist_ok=True)
_sessions_cache: dict[str, dict[str, Any]] = {}


def _session_path(session_id: str) -> Path:
    return SESSIONS_DIR / f"{session_id}.json"


def _load_session(session_id: str) -> dict[str, Any] | None:
    if session_id in _sessions_cache:
        return _sessions_cache[session_id]
    path = _session_path(session_id)
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            _sessions_cache[session_id] = data
            return data
        except (json.JSONDecodeError, OSError):
            return None
    return None


def _save_session(session_id: str, data: dict[str, Any]) -> None:
    _sessions_cache[session_id] = data
    try:
        with open(_session_path(session_id), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    except OSError:
        pass


class AgentRequest(BaseModel):
    language_pair: str = Field(default="zh_ru")
    task_type: Literal["generate_exercise", "evaluate_translation"] = "generate_exercise"
    user_level: str = Field(default="B1")
    domain: str = Field(default="general")
    mode: Literal["student", "teacher"] = "student"
    source_text: str = ""
    user_translation: str = ""
    reference_translation: str = ""
    focus_areas: list[str] = Field(default_factory=list)


@lru_cache(maxsize=1)
def get_graph():
    return build_translation_graph()


app = FastAPI(title="LinguaGraph")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.post("/api/run")
def run_agent(payload: AgentRequest):
    result = get_graph().invoke(payload.model_dump())
    return {
        "report": result.get("report", ""),
        "source_text": result.get("source_text", ""),
        "reference_translation": result.get("reference_translation", ""),
        "next_exercises": result.get("next_exercises", []),
        "terminology_hits": result.get("terminology_hits", []),
        "evaluation": result.get("evaluation", {}),
        "diagnostics": result.get("diagnostics", {}),
        "grammar_analysis": result.get("grammar_analysis", {}),
        "vocabulary_cards": result.get("vocabulary_cards", []),
        "mistake_record": result.get("mistake_record", {}),
        "learner_profile": result.get("learner_profile", {}),
        "review_plan": result.get("review_plan", []),
        "dashboard": result.get("dashboard", {}),
        "tool_trace": result.get("tool_trace", []),
        "focus_areas": result.get("focus_areas", []),
        "error_history": result.get("error_history", []),
        "session_summary": result.get("session_summary", ""),
    }


# ---- Session Endpoints ----

class SessionInitRequest(BaseModel):
    language_pair: str = "zh_ru"
    user_level: str = ""
    domain: str = "general"
    mode: Literal["student", "teacher"] = "student"


@app.post("/api/session/init")
def session_init(payload: SessionInitRequest):
    sid = uuid.uuid4().hex[:12]
    data: dict[str, Any] = {
        "session_id": sid,
        "language_pair": payload.language_pair,
        "user_level": payload.user_level or "",
        "domain": payload.domain,
        "mode": payload.mode,
        "created_at": None,  # set by JSON serialization
        "exercise_count": 0,
        "mistakes": [],
        "progress_history": [],
        "vocab_ratings": {},
        "ability_xp": {"accuracy": 0, "fluency": 0, "terminology": 0, "grammar": 0, "strategy": 0},
    }
    _save_session(sid, data)
    return {"session_id": sid, "learner_profile": None}


@app.get("/api/session/{session_id}")
def session_get(session_id: str):
    data = _load_session(session_id)
    if not data:
        raise HTTPException(status_code=404, detail="Session not found")
    return data


# ---- Diagnosis Endpoints ----

class DiagnosisStartRequest(BaseModel):
    session_id: str
    question_count: int = 3


class DiagnosisSubmitRequest(BaseModel):
    session_id: str
    answers: list[dict[str, str]]


@app.post("/api/diagnosis/start")
def diagnosis_start(payload: DiagnosisStartRequest):
    session = _load_session(payload.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    questions = generate_diagnosis_questions(
        session.get("language_pair", "zh_ru"),
        payload.question_count,
    )
    session["_diagnosis_questions"] = questions
    _save_session(payload.session_id, session)
    return {"questions": questions}


@app.post("/api/diagnosis/submit")
def diagnosis_submit(payload: DiagnosisSubmitRequest):
    session = _load_session(payload.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    questions = session.get("_diagnosis_questions", [])
    answers = {a["question_id"]: a["answer"] for a in payload.answers}
    results = evaluate_diagnosis_answers(
        questions, answers, session.get("language_pair", "zh_ru")
    )
    # Update session with diagnosis results
    session["user_level"] = results["estimated_level"]
    session["learner_profile"] = results["learner_profile"]
    _save_session(payload.session_id, session)
    return results


# ---- Practice Endpoints ----

class PracticeGenerateRequest(BaseModel):
    session_id: str
    focus_areas: list[str] = Field(default_factory=list)
    domain: str = ""


class PracticeEvaluateRequest(BaseModel):
    session_id: str
    exercise_id: str = ""
    user_translation: str


def _build_agent_request(
    session: dict[str, Any],
    task_type: Literal["generate_exercise", "evaluate_translation"],
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "language_pair": session.get("language_pair", "zh_ru"),
        "task_type": task_type,
        "user_level": session.get("user_level", "B1"),
        "domain": session.get("domain", "general"),
        "mode": session.get("mode", "student"),
        "source_text": "",
        "user_translation": "",
        "reference_translation": "",
        "focus_areas": [],
        **(extra or {}),
    }


@app.post("/api/practice/generate")
def practice_generate(payload: PracticeGenerateRequest):
    session = _load_session(payload.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    current_exercise = session.get("_current_exercise", {})
    agent_input = _build_agent_request(session, "generate_exercise", {
        "domain": payload.domain or session.get("domain", "general"),
        "focus_areas": payload.focus_areas or [],
        "source_text": current_exercise.get("source_text", ""),
        "learner_profile": session.get("learner_profile", {}),
        "error_history": session.get("mistakes", []),
    })
    result = get_graph().invoke(agent_input)

    exercise_id = uuid.uuid4().hex[:8]
    evaluation = result.get("evaluation", {})
    session["_current_exercise"] = {
        "exercise_id": exercise_id,
        "source_text": result.get("source_text", ""),
        "reference_translation": result.get("reference_translation", ""),
    }
    _save_session(payload.session_id, session)

    return {
        "exercise_id": exercise_id,
        "source_text": result.get("source_text", ""),
        "reference_translation": result.get("reference_translation", ""),
        "hints": evaluation.get("hints", {}),
        "vocabulary_cards": result.get("vocabulary_cards", []),
        "grammar_analysis": result.get("grammar_analysis", {}),
        "difficulty": evaluation.get("difficulty", {}),
        "diagnostics": result.get("diagnostics", {}),
        "exercise_blueprint": result.get("exercise_blueprint", {}),
        "selected_exercise": result.get("selected_exercise", {}),
    }


@app.post("/api/practice/evaluate")
def practice_evaluate(payload: PracticeEvaluateRequest):
    session = _load_session(payload.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    current = session.get("_current_exercise", {})
    source_text = current.get("source_text", "")
    reference = current.get("reference_translation", "")

    agent_input = _build_agent_request(session, "evaluate_translation", {
        "source_text": source_text,
        "user_translation": payload.user_translation,
        "reference_translation": reference,
    })
    result = get_graph().invoke(agent_input)

    evaluation = result.get("evaluation", {})
    score = evaluation.get("score")

    # Accumulate progress
    if score is not None:
        session["exercise_count"] = session.get("exercise_count", 0) + 1
        session["progress_history"] = session.get("progress_history", [])[-59:] + [{
            "key": f"{session.get('language_pair', 'zh_ru')}:{session.get('user_level', 'B1')}:{session.get('domain', 'general')}",
            "at": None,  # filled by serialization
            "score": score,
            "dimensions": evaluation.get("dimension_scores", {}),
            "tags": evaluation.get("error_tags", []),
            "source": source_text,
        }]

    # Accumulate ability XP
    dim_xp = evaluation.get("dimension_xp", {})
    if dim_xp and isinstance(dim_xp, dict):
        ability_xp = session.get("ability_xp", {})
        for dim_key in ["accuracy", "fluency", "terminology", "grammar", "strategy"]:
            xp_gain = max(0, min(30, int(dim_xp.get(dim_key, 0) or 0)))
            ability_xp[dim_key] = ability_xp.get(dim_key, 0) + xp_gain
        session["ability_xp"] = ability_xp

    mistake = result.get("mistake_record", {})
    if mistake and mistake.get("error_types"):
        session["mistakes"] = session.get("mistakes", [])[-49:] + [{
            "id": uuid.uuid4().hex[:8],
            "created_at": None,
            "source_text": mistake.get("source_text", ""),
            "student_answer": mistake.get("student_answer", ""),
            "recommended_answer": mistake.get("recommended_answer", ""),
            "error_types": mistake.get("error_types", []),
            "reason": mistake.get("reason", ""),
            "review_count": mistake.get("review_count", 0),
            "last_result": mistake.get("last_result", "待复习"),
        }]

    _save_session(payload.session_id, session)

    return {
        "evaluation": evaluation,
        "next_exercises": result.get("next_exercises", []),
        "focus_areas": result.get("focus_areas", []),
        "session_summary": result.get("session_summary", ""),
        "mistake_record": mistake,
        "vocabulary_cards": result.get("vocabulary_cards", []),
        "grammar_analysis": result.get("grammar_analysis", {}),
        "diagnostics": result.get("diagnostics", {}),
    }


# ---- Review Endpoints ----

@app.get("/api/review/dashboard")
def review_dashboard(session_id: str):
    session = _load_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    progress = session.get("progress_history", [])
    accuracy_trend = [
        {"date": r.get("at", ""), "score": r.get("score", 0)}
        for r in progress[-20:]
    ]

    # Error breakdown
    tag_counter: Counter[str] = Counter()
    for m in session.get("mistakes", []):
        for tag in m.get("error_types", []):
            tag_counter[tag] += 1
    error_breakdown = [
        {"tag": tag, "count": count}
        for tag, count in tag_counter.most_common(10)
    ]

    # Vocabulary status
    vocab_ratings = session.get("vocab_ratings", {})
    vocab_status = {"mastered": 0, "learning": 0, "new": 0}
    for r in vocab_ratings.values():
        rating = r.get("rating", "")
        if rating == "easy":
            vocab_status["mastered"] += 1
        elif rating in ("good", "hard"):
            vocab_status["learning"] += 1
        else:
            vocab_status["new"] += 1

    profile = session.get("learner_profile", {})

    return {
        "current_level": session.get("user_level", "B1"),
        "accuracy_trend": accuracy_trend,
        "error_breakdown": error_breakdown,
        "vocabulary_status": vocab_status,
        "review_due_count": len(session.get("review_plan", [])),
        "recommended_action": "继续完成今天的练习任务" if len(progress) < 5 else "查看错题本并完成专项训练",
        "dashboard": {
            "current_score": progress[-1]["score"] if progress else None,
            "accuracy_trend": "需要更多数据" if len(progress) < 3 else "趋势已更新",
            "review_due_count": len(session.get("review_plan", [])),
            "next_task": "完成今日练习" if len(progress) < 3 else "挑战弱项专练",
            "error_top": error_breakdown[:5],
            "progress_strengths": profile.get("performance_strengths", []),
            "progress_risks": profile.get("performance_risks", []),
        },
        "learner_profile": profile,
        "ability_stats": compute_ability_stats(
            session.get("ability_xp", {}),
            progress,
        ),
    }


@app.get("/api/review/mistakes")
def review_mistakes(
    session_id: str,
    error_type: str = "",
    status: str = "",
):
    session = _load_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    mistakes = session.get("mistakes", [])
    if error_type:
        mistakes = [
            m for m in mistakes
            if any(error_type.lower() in tag.lower() for tag in m.get("error_types", []))
        ]
    if status == "pending":
        mistakes = [m for m in mistakes if m.get("last_result") == "待复习"]
    elif status == "mastered":
        mistakes = [m for m in mistakes if m.get("last_result") == "基本掌握"]

    return {"mistakes": mistakes}


class ReviewDrillRequest(BaseModel):
    session_id: str
    error_types: list[str] = Field(default_factory=list)
    count: int = 3


@app.post("/api/review/drill")
def review_drill(payload: ReviewDrillRequest):
    session = _load_session(payload.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    drills = []
    for _ in range(min(payload.count, 5)):
        agent_input = _build_agent_request(session, "generate_exercise", {
            "focus_areas": payload.error_types or [],
        })
        result = get_graph().invoke(agent_input)
        evaluation = result.get("evaluation", {})
        drills.append({
            "id": uuid.uuid4().hex[:8],
            "source_text": result.get("source_text", ""),
            "reference_translation": result.get("reference_translation", ""),
            "focus": payload.error_types[0] if payload.error_types else "综合训练",
            "hints": evaluation.get("hints", {}),
        })

    return {"drills": drills}


class VocabRateRequest(BaseModel):
    session_id: str
    term: str
    rating: Literal["again", "hard", "good", "easy"]


@app.post("/api/review/vocabulary/rate")
def review_vocab_rate(payload: VocabRateRequest):
    session = _load_session(payload.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    minutes_map = {"again": 10, "hard": 60, "good": 1440, "easy": 4320}
    now_dt = datetime.now()
    next_review = now_dt + timedelta(minutes=minutes_map.get(payload.rating, 1440))

    vocab_ratings = session.get("vocab_ratings", {})
    vocab_ratings[payload.term] = {
        "rating": payload.rating,
        "at": now_dt.isoformat(),
        "nextReview": next_review.strftime("%m/%d %H:%M"),
    }
    session["vocab_ratings"] = vocab_ratings
    _save_session(payload.session_id, session)

    return {"next_review_at": next_review.isoformat()}
