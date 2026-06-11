"""Skill API — lightweight FastAPI endpoints for Coze Skills.

Three atomic, stateless endpoints designed for Coze HTTP nodes (< 30s each).
Does NOT depend on LangGraph (graph.py, nodes.py, state.py).

Start:  python -m uvicorn skill_api:app --host 127.0.0.1 --port 8001 --reload
"""

from __future__ import annotations

import json
import re
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from lingua_agent.config import load_language_pair
from lingua_agent.llm import LLMClient
from lingua_agent.prompts import build_evaluate_prompt
from lingua_agent.resources import find_terminology_hits
from lingua_agent.tools.exercise_generation import (
    ExerciseBlueprint,
    build_exercise_blueprint,
    build_llm_exercise_messages,
    select_exercise_candidate,
    validate_generated_exercise_payload,
)
from lingua_agent.tools.learning import (
    EVALUATION_DIMENSIONS,
    analyze_grammar,
    build_vocabulary_cards,
    estimate_difficulty,
    generate_layered_hints,
    score_translation,
    validate_llm_evaluation,
)

# ── FastAPI App ────────────────────────────────────────────────────────────

app = FastAPI(title="LinguaGraph Skills API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

llm = LLMClient()


# ── Helpers ────────────────────────────────────────────────────────────────

def _parse_json_from_llm(text: str) -> dict[str, Any] | None:
    """Extract structured JSON from LLM output (markdown code block or raw)."""
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pass
    return None


def _normalize_exercise_text(text: str) -> str:
    """Strip LLM formatting residue from exercise text."""
    cleaned = (text or "").strip()
    if not cleaned:
        return ""
    cleaned = re.sub(r"```(?:json)?", "", cleaned, flags=re.IGNORECASE).replace("```", "")
    cleaned = re.sub(r'^\s*"(.*)"\s*$', r"\1", cleaned)
    cleaned = re.sub(
        r"^\s*(source_text|reference_translation|原文|参考译文)\s*[:：]\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = cleaned.strip(" \t\r\n\"'")
    cleaned = re.sub(r"\s+\n", "\n", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    lines = [line.strip(" \"'") for line in cleaned.splitlines() if line.strip()]
    if not lines:
        return ""
    for line in lines:
        if not re.match(r"^(关键词|teaching_points|keywords)\s*[:：]?", line, flags=re.IGNORECASE):
            return line
    return lines[0]


# ── Exercise Bank (replicated from nodes.py for independence) ─────────────

_EXERCISE_BANK = {
    "zh_ru": [
        {
            "source": "高校教师正在设计一套面向翻译学习者的智能训练任务。",
            "reference": "Преподаватель университета разрабатывает набор интеллектуальных тренировочных заданий для изучающих перевод.",
        },
        {
            "source": "学生需要先理解句子结构，再选择合适的俄语表达。",
            "reference": "Студенту нужно сначала понять структуру предложения, а затем выбрать подходящее русское выражение.",
        },
        {
            "source": "这个工具会记录常见错误，并安排下一次复习。",
            "reference": "Этот инструмент фиксирует типичные ошибки и планирует следующее повторение.",
        },
        {
            "source": "翻译训练不只是替换词语，还要注意语境和搭配。",
            "reference": "Тренировка перевода - это не только замена слов, но и учет контекста и сочетаемости.",
        },
    ],
    "ru_zh": [
        {
            "source": "Студенты сравнивают свой перевод с образцом и исправляют типичные ошибки.",
            "reference": "学生把自己的译文与范例进行比较，并改正常见错误。",
        },
        {
            "source": "Преподаватель объясняет, почему в этом предложении нужен другой падеж.",
            "reference": "教师解释为什么这个句子里需要使用另一个格。",
        },
        {
            "source": "Система предлагает короткое упражнение после каждой проверки перевода.",
            "reference": "系统在每次译文批改后提供一个简短练习。",
        },
        {
            "source": "Хороший перевод сохраняет смысл текста и звучит естественно.",
            "reference": "好的翻译既保留文本意思，又表达自然。",
        },
    ],
}


# ═══════════════════════════════════════════════════════════════════════════
#  Skill 1: Translation Evaluation
# ═══════════════════════════════════════════════════════════════════════════

class EvaluateRequest(BaseModel):
    source_text: str = Field(..., description="原文")
    user_translation: str = Field(..., description="学生译文（可为空）")
    reference_translation: str = Field(default="", description="参考译文")
    language_pair: str = Field(default="zh_ru", description="语种对，如 zh_ru")
    user_level: str = Field(default="B1", description="学生CEFR水平")


@app.post("/api/skill/evaluate")
def skill_evaluate(payload: EvaluateRequest):
    """Evaluate a student translation on five dimensions (1-5 each).

    Returns a full evaluation including dimension scores, error tags,
    revision advice, and dimension XP.  Designed for Coze HTTP nodes
    with a hard 30s timeout — falls back to rule engine if LLM is slow.
    """
    pair_config = load_language_pair(payload.language_pair)
    dimensions = pair_config.get("evaluation_dimensions", [])

    if not payload.user_translation.strip():
        return score_translation(
            payload.source_text,
            payload.user_translation,
            payload.reference_translation,
            pair_config,
        )

    # LLM evaluation (with embedded self-check from the enhanced prompt)
    system, user = build_evaluate_prompt(
        display_name=pair_config["display_name"],
        user_level=payload.user_level,
        source_text=payload.source_text,
        user_translation=payload.user_translation,
        reference_translation=payload.reference_translation,
        dimensions=dimensions,
    )
    llm_output = llm.complete(system, user)
    parsed = _parse_json_from_llm(llm_output)

    if parsed and parsed.get("dimension_scores"):
        evaluation = validate_llm_evaluation(
            parsed, payload.reference_translation, pair_config
        )
    else:
        evaluation = score_translation(
            payload.source_text,
            payload.user_translation,
            payload.reference_translation,
            pair_config,
        )
        evaluation["review"] = llm_output

    return evaluation


# ═══════════════════════════════════════════════════════════════════════════
#  Skill 2: Exercise Generation
# ═══════════════════════════════════════════════════════════════════════════

class GenerateRequest(BaseModel):
    language_pair: str = Field(default="zh_ru", description="语种对")
    user_level: str = Field(default="B1", description="学生CEFR水平")
    domain: str = Field(default="general", description="领域")
    focus_areas: list[str] = Field(default_factory=list, description="训练焦点维度")
    previous_source: str = Field(default="", description="上一题原文，避免重复")
    learner_profile: dict[str, Any] = Field(default_factory=dict)
    error_history: list[dict[str, Any]] = Field(default_factory=list)


@app.post("/api/skill/generate")
def skill_generate(payload: GenerateRequest):
    """Generate a translation exercise tailored to the learner.

    Strategy: exercise bank first → LLM fallback → bank safe fallback.
    Also returns layered hints, vocabulary cards, and grammar analysis.
    """
    pair_config = load_language_pair(payload.language_pair)

    # Build exercise blueprint from learner state
    blueprint = build_exercise_blueprint({
        "focus_areas": payload.focus_areas,
        "learner_profile": payload.learner_profile,
        "error_history": payload.error_history,
        "user_level": payload.user_level,
        "domain": payload.domain,
    })

    # Try tagged bank first, then selection
    selection = select_exercise_candidate(
        payload.language_pair,
        blueprint,
        payload.previous_source,
    )

    source_text: str
    reference_translation: str
    exercise_source: str

    if selection is not None:
        source_text = selection["candidate"]["source_text"]
        reference_translation = selection["candidate"]["reference_translation"]
        exercise_source = "bank"
    else:
        # LLM fallback
        system, user = build_llm_exercise_messages(pair_config, payload.domain, blueprint)
        generated = llm.complete(system, user)
        parsed = _parse_json_from_llm(generated)
        validated = validate_generated_exercise_payload(parsed, blueprint)
        if validated is not None:
            source_text = _normalize_exercise_text(validated["source_text"])
            reference_translation = _normalize_exercise_text(validated["reference_translation"])
            exercise_source = "llm"
        else:
            # Safe fallback: bank with lowest difficulty
            bank = _EXERCISE_BANK.get(payload.language_pair, _EXERCISE_BANK["zh_ru"])
            prev = payload.previous_source.strip()
            if prev:
                for idx, ex in enumerate(bank):
                    if ex["source"] == prev:
                        fallback = bank[(idx + 1) % len(bank)]
                        break
                else:
                    fallback = bank[0]
            else:
                fallback = bank[0]
            source_text = fallback["source"]
            reference_translation = fallback["reference"]
            exercise_source = "bank_safe_fallback"

    # Generate hints, vocab cards, and grammar analysis
    hints = generate_layered_hints(source_text, reference_translation, pair_config)
    vocabulary_cards = build_vocabulary_cards(
        source_text,
        find_terminology_hits(payload.language_pair, payload.domain, source_text),
        pair_config,
    )
    grammar_analysis = analyze_grammar(source_text, pair_config)
    difficulty = estimate_difficulty(source_text, payload.user_level)

    return {
        "source_text": source_text,
        "reference_translation": reference_translation,
        "exercise_source": exercise_source,
        "hints": hints,
        "vocabulary_cards": vocabulary_cards,
        "grammar_analysis": grammar_analysis,
        "difficulty": difficulty,
        "blueprint": {
            "primary_focus": blueprint["primary_focus"],
            "target_level": blueprint["target_level"],
            "teaching_intent": blueprint["teaching_intent"],
        },
    }


# ═══════════════════════════════════════════════════════════════════════════
#  Skill 3: Terminology & Vocabulary Cards
# ═══════════════════════════════════════════════════════════════════════════

class TerminologyRequest(BaseModel):
    language_pair: str = Field(default="zh_ru", description="语种对")
    domain: str = Field(default="general", description="领域")
    source_text: str = Field(..., description="需要检索术语的原文")


@app.post("/api/skill/terminology")
def skill_terminology(payload: TerminologyRequest):
    """Look up terminology hits in CSV databases and generate vocabulary cards.

    Pure rule-engine, no LLM — always completes in < 1s.
    """
    pair_config = load_language_pair(payload.language_pair)
    hits = find_terminology_hits(payload.language_pair, payload.domain, payload.source_text)
    cards = build_vocabulary_cards(payload.source_text, hits, pair_config)
    grammar = analyze_grammar(payload.source_text, pair_config)

    return {
        "terminology_hits": hits,
        "hit_count": len(hits),
        "vocabulary_cards": cards,
        "grammar_analysis": grammar,
    }


# ═══════════════════════════════════════════════════════════════════════════
#  Health Check
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/api/skill/health")
def health_check():
    return {"status": "ok", "service": "LinguaGraph Skills API"}
