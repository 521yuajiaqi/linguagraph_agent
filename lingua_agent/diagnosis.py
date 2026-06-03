"""Diagnosis module: generates placement-test questions for new learners.

The diagnosis should be a light, direction-consistent placement test, not a
mixed-difficulty exam.
"""

from __future__ import annotations

import uuid
from typing import Any

from lingua_agent.config import load_language_pair
from lingua_agent.llm import LLMClient

llm = LLMClient()

DIAGNOSIS_DIMENSIONS = ["accuracy", "fluency", "terminology", "grammar"]


def _diagnosis_bank(language_pair: str) -> list[dict[str, Any]]:
    """Return a small, low-stakes diagnosis bank for the given direction."""
    banks = {
        "zh_ru": [
            {
                "type": "short_translate",
                "difficulty": "A1",
                "source_text": "我喜欢学习语言。",
                "reference_translation": "Мне нравится учить языки.",
            },
            {
                "type": "short_translate",
                "difficulty": "A1",
                "source_text": "学生每天都练习翻译。",
                "reference_translation": "Студенты каждый день практикуют перевод.",
            },
            {
                "type": "short_translate",
                "difficulty": "A2",
                "source_text": "翻译时要注意语序和基本语法。",
                "reference_translation": "При переводе нужно обращать внимание на порядок слов и базовую грамматику.",
            },
        ],
        "ru_zh": [
            {
                "type": "short_translate",
                "difficulty": "A1",
                "source_text": "Я студент.",
                "reference_translation": "我是学生。",
            },
            {
                "type": "short_translate",
                "difficulty": "A1",
                "source_text": "Студенты каждый день практикуют перевод.",
                "reference_translation": "学生们每天练习翻译。",
            },
            {
                "type": "short_translate",
                "difficulty": "A2",
                "source_text": "При переводе нужно обращать внимание на порядок слов и базовую грамматику.",
                "reference_translation": "翻译时要注意语序和基本语法。",
            },
        ],
    }
    return banks.get(language_pair, banks["zh_ru"])


def generate_diagnosis_questions(
    language_pair: str,
    question_count: int = 3,
) -> list[dict[str, Any]]:
    """Generate a small low-difficulty placement test."""
    pair_config = load_language_pair(language_pair)
    bank = _diagnosis_bank(language_pair)
    return _fallback_questions(language_pair, question_count, pair_config, bank)


def _fallback_questions(
    language_pair: str,
    count: int,
    pair_config: dict[str, Any],
    bank: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Generate basic diagnosis questions without LLM."""
    bank = bank or _diagnosis_bank(language_pair)
    result = []
    for i in range(min(count, len(bank))):
        q = dict(bank[i])
        q["id"] = str(uuid.uuid4())[:8]
        q.setdefault("hint", "先抓住句子核心意思，再翻译。")
        result.append(q)
    return result


def evaluate_diagnosis_answers(
    questions: list[dict[str, Any]],
    answers: dict[str, str],
    language_pair: str,
) -> dict[str, Any]:
    """Score a set of diagnosis answers and return level + dimension analysis.

    Uses lightweight heuristics for choice/blank questions and the LLM for
    translation questions. Returns the same shape as DiagnosisSubmitResponse.
    """
    pair_config = load_language_pair(language_pair)
    dimension_scores: dict[str, int] = {dim: 0 for dim in DIAGNOSIS_DIMENSIONS}
    question_scores: list[dict[str, Any]] = []
    total_possible = 0
    total_earned = 0

    for q in questions:
        qid = q["id"]
        user_answer = (answers.get(qid) or "").strip()
        qtype = q.get("type", "short_translate")
        ref = q.get("reference_translation", "")

        if qtype == "choice":
            correct = user_answer == ref
            score = 5 if correct else 0
            dimension_scores["accuracy"] += score
            total_possible += 5
            total_earned += score
            question_scores.append(
                {
                    "question_id": qid,
                    "type": qtype,
                    "correct": correct,
                    "score": score,
                }
            )

        elif qtype == "fill_blank":
            blank = q.get("blank_word", "")
            correct = user_answer.lower().strip() == blank.lower().strip()
            partial = not correct and len(user_answer) > 0 and (
                blank.lower() in user_answer.lower()
                or user_answer.lower() in blank.lower()
            )
            score = 5 if correct else (3 if partial else 0)
            dimension_scores["terminology"] += score
            total_possible += 5
            total_earned += score
            question_scores.append(
                {
                    "question_id": qid,
                    "type": qtype,
                    "correct": correct,
                    "partial": partial,
                    "score": score,
                }
            )

        elif qtype == "error_correction":
            # Check if the user corrected the key error
            error_sentence = q.get("error_sentence", "")
            if user_answer and user_answer != error_sentence:
                score = 4
                dimension_scores["grammar"] += score
            elif user_answer:
                score = 2
                dimension_scores["grammar"] += score
            else:
                score = 0
            total_possible += 5
            total_earned += score
            question_scores.append(
                {
                    "question_id": qid,
                    "type": qtype,
                    "score": score,
                }
            )

        else:  # short_translate
            if user_answer:
                # Use the LLM to score the short translation
                score = _quick_score(user_answer, ref, q.get("source_text", ""), pair_config)
                dimension_scores["accuracy"] += max(1, score)
                dimension_scores["fluency"] += max(1, score)
                total_possible += 10
                total_earned += score * 2
                question_scores.append(
                    {
                        "question_id": qid,
                        "type": qtype,
                        "score": score,
                    }
                )
            else:
                question_scores.append(
                    {
                        "question_id": qid,
                        "type": qtype,
                        "score": 0,
                    }
                )

    # Normalize dimension scores to 1-5 scale
    for dim in DIAGNOSIS_DIMENSIONS:
        if total_possible > 0:
            dimension_scores[dim] = max(
                1, min(5, round(dimension_scores[dim] / max(1, total_possible / len(DIAGNOSIS_DIMENSIONS)) * 5))
            )

    # Estimate CEFR level from total score percentage
    pct = total_earned / max(1, total_possible) * 100
    if pct >= 85:
        estimated_level = "B2"
    elif pct >= 65:
        estimated_level = "B1"
    elif pct >= 40:
        estimated_level = "A2"
    else:
        estimated_level = "A1"

    # Determine strengths and weaknesses from dimension scores
    sorted_dims = sorted(dimension_scores.items(), key=lambda x: x[1])
    strengths = [dim for dim, _score in sorted_dims[-2:]][::-1]
    weaknesses = [dim for dim, _score in sorted_dims[:2]]

    # Generate recommended path
    recommended_path = _build_recommended_path(estimated_level, weaknesses, pair_config)

    return {
        "estimated_level": estimated_level,
        "dimension_scores": {
            "accuracy": dimension_scores.get("accuracy", 3),
            "fluency": dimension_scores.get("fluency", 3),
            "terminology": dimension_scores.get("terminology", 3),
            "grammar": dimension_scores.get("grammar", 3),
            "strategy": 3,
        },
        "strengths": [DIM_LABELS.get(s, s) for s in strengths],
        "weaknesses": [DIM_LABELS.get(w, w) for w in weaknesses],
        "recommended_path": recommended_path,
        "learner_profile": {
            "level": estimated_level,
            "goal": f"提升{pair_config.get('display_name', '翻译')}准确度和自然度",
            "common_errors": [],
            "performance_strengths": [DIM_LABELS.get(s, s) for s in strengths],
            "performance_risks": [DIM_LABELS.get(w, w) for w in weaknesses],
            "weak_grammar": weaknesses,
            "familiar_terms": [],
        },
    }


DIM_LABELS = {
    "accuracy": "语义准确",
    "fluency": "表达流畅",
    "terminology": "术语一致",
    "grammar": "语法结构",
}


def _quick_score(
    user_answer: str, reference: str, source: str, pair_config: dict[str, Any]
) -> int:
    """Lightweight LLM-based scoring for a single short translation (1-5 scale)."""
    system = (
        "你是翻译评分专家。请对以下短句翻译进行快速评分（1-5分），只输出数字。"
    )
    user = (
        f"原文：{source}\n学生译文：{user_answer}\n参考译文：{reference}\n\n"
        f"评分标准：5=完美, 4=基本准确有小瑕疵, 3=意思对但表达不自然, 2=部分正确, 1=完全错误\n"
        f"只输出数字（1-5）："
    )
    output = llm.complete(system, user).strip()
    try:
        score = int(output)
        return max(1, min(5, score))
    except (ValueError, TypeError):
        # Fallback: simple token overlap
        user_words = set(user_answer.lower().split())
        ref_words = set(reference.lower().split())
        if not ref_words:
            return 3
        overlap = len(user_words & ref_words) / max(1, len(ref_words))
        if overlap > 0.7:
            return 5
        elif overlap > 0.4:
            return 4
        elif overlap > 0.2:
            return 3
        elif overlap > 0.05:
            return 2
        return 1


def _build_recommended_path(
    level: str, weaknesses: list[str], pair_config: dict[str, Any]
) -> list[str]:
    """Build a 3-step learning path based on diagnosis results."""
    direction = pair_config.get("display_name", "翻译")
    paths: dict[str, list[str]] = {
        "A1": [
            f"从{direction}基础词汇和短句开始",
            "每天完成 3-5 题短句翻译",
            "重点积累常用词汇搭配和基本句式",
        ],
        "A2": [
            f"先做 5 题{direction}短句训练建立信心",
            "每题提交后查看分层提示再重译",
            "关注格、体和支配关系等基础语法",
        ],
        "B1": [
            f"先做 3 题{direction}短句训练",
            "每题提交后重译一次，比较两次的进步",
            "针对" + (DIM_LABELS.get(weaknesses[0], weaknesses[0]) if weaknesses else "表达自然度") + "做变式复习",
        ],
        "B2": [
            f"从{direction}段落翻译开始",
            "关注文体得体性和翻译策略选择",
            "每次练习后写一句话总结自己的问题",
        ],
    }
    return paths.get(level, paths["B1"])
