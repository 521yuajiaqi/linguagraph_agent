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
    pick_few_shot_examples,
    select_exercise_candidate,
    validate_generated_exercise_payload,
)
from lingua_agent.tools.learning import (
    EVALUATION_DIMENSIONS,
    analyze_grammar,
    build_vocabulary_cards,
    compute_ability_rank,
    estimate_difficulty,
    generate_layered_hints,
    score_translation,
    validate_llm_evaluation,
)

# ── Helpers ────────────────────────────────────────────────────────────────

# Coze bot may pass Chinese names; normalize to code format
_LANG_ALIASES = {
    "中俄": "zh_ru", "zh-ru": "zh_ru", "汉俄": "zh_ru",
    "俄中": "ru_zh", "ru-zh": "ru_zh", "俄汉": "ru_zh",
}
_DOMAIN_ALIASES = {
    "通用": "general", "日常": "general", "生活": "general", "都行": "general",
    "科技": "technology", "技术": "technology", "科学": "technology", "ai": "technology",
    "教育": "education", "学习": "education", "学校": "education", "教学": "education",
    "商务": "business", "商业": "business", "贸易": "business", "公司": "business", "职场": "business",
    "学术": "academic", "论文": "academic", "研究": "academic", "理论": "academic",
}

def _normalize_pair(raw: str) -> str:
    return _LANG_ALIASES.get(raw.strip(), raw.strip())

def _normalize_domain(raw: str) -> str:
    return _DOMAIN_ALIASES.get(raw.strip(), raw.strip().lower())


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

_FALLBACK_CACHE: dict[str, list[dict[str, str]]] = {}


def _load_fallback_bank(language_pair: str) -> list[dict[str, str]]:
    """Load basic (source, reference) pairs from the exercise JSON for safe fallback."""
    if language_pair in _FALLBACK_CACHE:
        return _FALLBACK_CACHE[language_pair]

    import json
    from pathlib import Path

    json_path = Path(__file__).resolve().parent / "resources" / "exercises" / f"{language_pair}.json"
    if not json_path.exists():
        fallback = [{"source": "翻译练习", "reference": "Упражнение по переводу"}]
        _FALLBACK_CACHE[language_pair] = fallback
        return fallback

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    pairs = [
        {"source": item["source_text"], "reference": item["reference_translation"]}
        for item in data
    ]
    _FALLBACK_CACHE[language_pair] = pairs
    return pairs


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
    pair = _normalize_pair(payload.language_pair)
    pair_config = load_language_pair(pair)
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

def _coerce_list(raw: Any) -> list:
    """Coerce a JSON string or comma-separated string to list."""
    if raw is None:
        return []
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str):
        s = raw.strip()
        if not s or s == "[]":
            return []
        if s.startswith("["):
            try:
                val = json.loads(s)
                return val if isinstance(val, list) else [str(val)]
            except (json.JSONDecodeError, TypeError):
                pass
        # "grammar,accuracy" → ["grammar","accuracy"]
        return [x.strip() for x in s.split(",") if x.strip()]
    return [str(raw)]

def _coerce_dict(raw: Any) -> dict:
    """Coerce a JSON string to dict."""
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        s = raw.strip()
        if not s or s == "{}":
            return {}
        try:
            val = json.loads(s)
            return val if isinstance(val, dict) else {}
        except (json.JSONDecodeError, TypeError):
            return {}
    return {}

# Simple in-memory cache: avoid repeated LLM calls for same level/domain
from functools import lru_cache
from datetime import datetime, timedelta

_EXERCISE_CACHE: dict[str, tuple[dict, datetime]] = {}
_CACHE_TTL = timedelta(minutes=3)

def _normalize_level(raw: str) -> str:
    """Normalize user_level to standard CEFR code."""
    level_map = {
        "入门": "A1", "初级": "A2", "中级": "B1",
        "中高级": "B2", "高级": "C1",
        "a1": "A1", "a2": "A2", "b1": "B1", "b2": "B2", "c1": "C1",
    }
    return level_map.get(raw.strip(), raw.strip().upper())


class GenerateRequest(BaseModel):
    language_pair: str = Field(default="zh_ru", description="语种对")
    user_level: str = Field(default="B1", description="学生CEFR水平")
    domain: str = Field(default="general", description="领域")
    focus_areas_raw: Any = Field(default=None, alias="focus_areas")
    previous_source: str = Field(default="", description="上一题原文，避免重复")
    learner_profile_raw: Any = Field(default=None, alias="learner_profile")
    error_history_raw: Any = Field(default=None, alias="error_history")

    @property
    def focus_areas(self) -> list[str]:
        return _coerce_list(self.focus_areas_raw)

    @property
    def learner_profile(self) -> dict:
        return _coerce_dict(self.learner_profile_raw)

    @property
    def error_history(self) -> list[dict]:
        raw = _coerce_list(self.error_history_raw)
        return [_coerce_dict(item) for item in raw]

    def model_post_init(self, __context):
        self.user_level = _normalize_level(self.user_level)


@app.post("/api/skill/generate")
def skill_generate(payload: GenerateRequest):
    """Generate a translation exercise tailored to the learner.

    Strategy: LLM with few-shot bank examples (primary) → bank candidate (fallback).
    """
    pair = _normalize_pair(payload.language_pair)
    domain = _normalize_domain(payload.domain)
    print(f"[generate] pair={pair} domain={domain} level={payload.user_level} focus={payload.focus_areas}", flush=True)
    pair_config = load_language_pair(pair)

    # Build exercise blueprint from learner state
    blueprint = build_exercise_blueprint({
        "focus_areas": payload.focus_areas,
        "learner_profile": payload.learner_profile,
        "error_history": payload.error_history,
        "user_level": payload.user_level,
        "domain": domain,
    })

    source_text: str
    reference_translation: str
    exercise_source: str

    # ── Cache check: same level+domain within 3min returns cached exercise ──
    cache_key = f"{pair}|{domain}|{payload.user_level}|{blueprint['primary_focus']}"
    now = datetime.now()
    if cache_key in _EXERCISE_CACHE:
        cached_data, cached_time = _EXERCISE_CACHE[cache_key]
        if now - cached_time < _CACHE_TTL and cached_data.get("source_text"):
            print(f"[generate] cache HIT key={cache_key} text={cached_data['source_text'][:40]}", flush=True)
            source_text = cached_data["source_text"]
            reference_translation = cached_data["reference_translation"]
            exercise_source = "cache"
        else:
            del _EXERCISE_CACHE[cache_key]
            cached_data = None
    else:
        cached_data = None

    if cached_data is None:
        # ── Primary: LLM with 1 few-shot bank example (2 was too slow) ──
        examples = pick_few_shot_examples(
            pair, blueprint, payload.previous_source, count=1,
        )
        system, user = build_llm_exercise_messages(pair_config, domain, blueprint, examples)
        generated = llm.complete(system, user)
    parsed = _parse_json_from_llm(generated)
    validated = validate_generated_exercise_payload(parsed, blueprint)
    if validated is not None:
        source_text = _normalize_exercise_text(validated["source_text"])
        reference_translation = _normalize_exercise_text(validated["reference_translation"])
        exercise_source = "llm"
        # Cache for 3 minutes
        _EXERCISE_CACHE[cache_key] = (
            {"source_text": source_text, "reference_translation": reference_translation},
            now,
        )
    else:
        # ── Fallback: bank candidate ──
        selection = select_exercise_candidate(
            pair, blueprint, payload.previous_source,
        )
        if selection is not None:
            source_text = selection["candidate"]["source_text"]
            reference_translation = selection["candidate"]["reference_translation"]
            exercise_source = "bank"
        else:
            # ── Last resort: any bank entry ──
            bank = _load_fallback_bank(pair)
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

    print(f"[generate] source={exercise_source} text={source_text[:60]}... ref={reference_translation[:40]}...", flush=True)

    # Generate hints, vocab cards, and grammar analysis
    hints = generate_layered_hints(source_text, reference_translation, pair_config)
    vocabulary_cards = build_vocabulary_cards(
        source_text,
        find_terminology_hits(pair, domain, source_text),
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
    pair = _normalize_pair(payload.language_pair)
    domain = _normalize_domain(payload.domain)
    pair_config = load_language_pair(pair)
    hits = find_terminology_hits(pair, domain, payload.source_text)
    cards = build_vocabulary_cards(payload.source_text, hits, pair_config)
    grammar = analyze_grammar(payload.source_text, pair_config)

    return {
        "terminology_hits": hits,
        "hit_count": len(hits),
        "vocabulary_cards": cards,
        "grammar_analysis": grammar,
    }


# ═══════════════════════════════════════════════════════════════════════════
#  Skill 4: RPG Ability Rank
# ═══════════════════════════════════════════════════════════════════════════

class RankRequest(BaseModel):
    accuracy: int = Field(default=0, ge=0, le=9999)
    fluency: int = Field(default=0, ge=0, le=9999)
    terminology: int = Field(default=0, ge=0, le=9999)
    grammar: int = Field(default=0, ge=0, le=9999)
    strategy: int = Field(default=0, ge=0, le=9999)


@app.post("/api/skill/rank")
def skill_rank(payload: RankRequest):
    """Compute translator rank, title, and bottleneck from five-dimension XP.

    Pure computation, no LLM — always < 10ms.
    """
    ability_xp = {
        "accuracy": payload.accuracy,
        "fluency": payload.fluency,
        "terminology": payload.terminology,
        "grammar": payload.grammar,
        "strategy": payload.strategy,
    }
    return compute_ability_rank(ability_xp)


# ═══════════════════════════════════════════════════════════════════════════
#  Health Check
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/api/skill/health")
def health_check():
    return {"status": "ok", "service": "LinguaGraph Skills API"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("skill_api:app", host="127.0.0.1", port=8001, reload=True)
