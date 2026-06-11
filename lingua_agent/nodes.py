from __future__ import annotations

import json
import re
from typing import Any

from lingua_agent.config import load_language_pair
from lingua_agent.llm import LLMClient
from lingua_agent.prompts import (
    build_evaluate_prompt,
    build_exercise_generation_prompt,
    build_plan_prompt,
    build_reflection_prompt,
)
from lingua_agent.resources import find_terminology_hits
from lingua_agent.state import TranslationAgentState
from lingua_agent.tools import (
    analyze_grammar,
    build_dashboard,
    build_exercise_blueprint,
    build_learner_profile,
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


llm = LLMClient()


def _parse_json_from_llm(text: str) -> dict[str, Any] | None:
    """从 LLM 原始输出中提取结构化 JSON。支持 markdown 代码块和裸 JSON。"""
    # 策略 1: ```json ... ``` 或 ``` ... ``` 代码块
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass

    # 策略 2: 文本中最外层的 { } 对
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pass

    return None


def _normalize_exercise_text(text: str) -> str:
    """Strip LLM formatting residue so the UI only renders final exercise text."""
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

    # If the model leaked extra explanation, keep the first substantial content line.
    for line in lines:
        if not re.match(r"^(关键词|teaching_points|keywords)\s*[:：]?", line, flags=re.IGNORECASE):
            return line
    return lines[0]



EXERCISE_BANK = {
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

SAFE_FALLBACK_BLUEPRINT = {
    "primary_focus": "accuracy",
    "target_level": "A2",
    "difficulty_band": {"floor": "A1", "target": "A2", "ceiling": "A2"},
    "syntax_load": "low",
    "terminology_load": "low",
    "teaching_intent": "safe fallback",
    "selection_reason": "safe_fallback",
    "avoid_overload_dimensions": [],
    "preferred_domain": "general",
}


def _default_reference(state: TranslationAgentState) -> str:
    source = state.get("source_text", "").strip()
    pair = state.get("language_pair", "zh_ru")
    references = {
        ("zh_ru", "智能体可以辅助翻译教学。"): "Интеллектуальный агент может помогать в обучении переводу.",
        ("ru_zh", "Интеллектуальный агент помогает обучению переводу."): "智能体有助于翻译教学。",
    }
    if (pair, source) in references:
        return references[(pair, source)]
    if pair == "zh_ru":
        return "Преподаватель университета разрабатывает набор интеллектуальных тренировочных заданий для изучающих перевод."
    return "高校教师正在设计一套面向翻译学习者的智能训练任务。"


def initialize_context(state: TranslationAgentState) -> TranslationAgentState:
    pair = state.get("language_pair") or f"{state.get('source_lang', 'zh')}_{state.get('target_lang', 'ru')}"
    pair_config = load_language_pair(pair)

    source_lang = state.get("source_lang") or pair_config["source_lang"]
    target_lang = state.get("target_lang") or pair_config["target_lang"]
    domain = state.get("domain") or pair_config.get("default_domain", "general")
    task_type = state.get("task_type") or ("evaluate_translation" if state.get("user_translation") else "generate_exercise")

    return {
        **state,
        "language_pair": pair,
        "source_lang": source_lang,
        "target_lang": target_lang,
        "direction": f"{source_lang}->{target_lang}",
        "domain": domain,
        "user_level": state.get("user_level", "B1"),
        "mode": state.get("mode", "student"),
        "task_type": task_type,
        "pair_config": pair_config,
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
        selected_exercise = selection["candidate"]
    else:
        system, user = build_llm_exercise_messages(config, state["domain"], blueprint)
        generated = llm.complete(system, user)
        parsed = _parse_json_from_llm(generated)
        validated = validate_generated_exercise_payload(parsed, blueprint)
        if validated is not None:
            source_text = _normalize_exercise_text(validated["source_text"])
            reference = _normalize_exercise_text(validated["reference_translation"])
            exercise_source = "LLM fallback"
            selected_exercise = {
                "source_text": source_text,
                "reference_translation": reference,
            }
        else:
            safe_selection = select_exercise_candidate(
                state["language_pair"],
                SAFE_FALLBACK_BLUEPRINT,
                previous_source,
            )
            if safe_selection is not None:
                source_text = safe_selection["candidate"]["source_text"]
                reference = safe_selection["candidate"]["reference_translation"]
                selected_exercise = safe_selection["candidate"]
            else:
                fallback = _pick_exercise(state["language_pair"], previous_source)
                source_text = fallback["source"]
                reference = fallback["reference"]
                selected_exercise = {
                    "source_text": source_text,
                    "reference_translation": reference,
                }
            exercise_source = "题库兜底"

    hints = generate_layered_hints(source_text, reference, config)
    diagnostics = diagnose_level(source_text, "", state["user_level"], config)
    difficulty_result = estimate_difficulty(source_text, state["user_level"])

    return {
        **state,
        "source_text": source_text,
        "reference_translation": reference,
        "exercise_blueprint": blueprint,
        "selected_exercise": selected_exercise,
        "diagnostics": diagnostics,
        "evaluation": {
            "hints": hints,
            "difficulty": difficulty_result,
        },
        "feedback": generated,
        "tool_trace": [
            {
                "tool": "出题画像工具",
                "result": f"{blueprint['primary_focus']} | {blueprint['selection_reason']}",
            },
            {"tool": "题库排序工具", "result": f"已使用{exercise_source}完成选题"},
            {"tool": "分层提示工具", "result": "已准备词汇、结构、语法和半句提示"},
        ],
    }


def _pick_exercise(language_pair: str, previous_source: str = "") -> dict[str, str]:
    bank = EXERCISE_BANK.get(language_pair) or EXERCISE_BANK["zh_ru"]
    previous_source = (previous_source or "").strip()
    if not previous_source:
        return bank[0]
    for index, exercise in enumerate(bank):
        if exercise["source"] == previous_source:
            return bank[(index + 1) % len(bank)]
    return bank[0]


def terminology_check(state: TranslationAgentState) -> TranslationAgentState:
    hits = find_terminology_hits(
        state["language_pair"],
        state["domain"],
        state.get("source_text", ""),
    )
    grammar = analyze_grammar(state.get("source_text", ""), state["pair_config"])
    vocabulary = build_vocabulary_cards(state.get("source_text", ""), hits, state["pair_config"])
    return {
        **state,
        "terminology_hits": hits,
        "grammar_analysis": grammar,
        "vocabulary_cards": vocabulary,
        "tool_trace": [
            *state.get("tool_trace", []),
            {"tool": "术语检查工具", "result": f"命中 {len(hits)} 个术语"},
            {"tool": "语法解析工具", "result": "已生成学生可读句法说明"},
            {"tool": "词汇搭配工具", "result": f"已生成 {len(vocabulary)} 张词汇卡"},
        ],
    }


def evaluate_translation(state: TranslationAgentState) -> TranslationAgentState:
    reference_translation = state.get("reference_translation") or _default_reference(state)
    state = {**state, "reference_translation": reference_translation}
    if not state.get("user_translation"):
        return {
            **state,
            "evaluation": {
                "score": None,
                "note": "未提供学生译文，已跳过译文评分。",
                "hints": generate_layered_hints(
                    state.get("source_text", ""),
                    state.get("reference_translation", ""),
                    state["pair_config"],
                ),
            },
        }

    dimensions = state["pair_config"].get("evaluation_dimensions", [])
    system, user = build_evaluate_prompt(
        display_name=state["pair_config"]["display_name"],
        user_level=state["user_level"],
        source_text=state.get("source_text", ""),
        user_translation=state.get("user_translation", ""),
        reference_translation=state.get("reference_translation", ""),
        dimensions=dimensions,
    )
    llm_output = llm.complete(system, user)
    parsed = _parse_json_from_llm(llm_output)

    if parsed and parsed.get("dimension_scores"):
        evaluation = validate_llm_evaluation(parsed, state.get("reference_translation", ""), state["pair_config"])
        eval_source = "LLM"
    else:
        evaluation = score_translation(
            state.get("source_text", ""),
            state.get("user_translation", ""),
            state.get("reference_translation", ""),
            state["pair_config"],
        )
        evaluation["review"] = llm_output
        eval_source = "规则引擎"

    diagnostics = diagnose_level(
        state.get("source_text", ""),
        state.get("user_translation", ""),
        state["user_level"],
        state["pair_config"],
    )

    return {
        **state,
        "diagnostics": diagnostics,
        "evaluation": evaluation,
        "tool_trace": [
            *state.get("tool_trace", []),
            {"tool": f"答案评估工具（{eval_source}驱动）", "result": f"评分 {evaluation.get('score', 'N/A')}"},
            {"tool": "能力诊断工具", "result": f"估计水平 {diagnostics.get('estimated_level')}"},
        ],
    }


def reflect_on_evaluation(state: TranslationAgentState) -> TranslationAgentState:
    """Self-Reflection 节点：LLM 复核自己的评估，检查误判、遗漏和评分不一致。"""
    evaluation = state.get("evaluation", {})
    if not evaluation or not evaluation.get("dimension_scores"):
        return state

    system, user = build_reflection_prompt(
        display_name=state["pair_config"]["display_name"],
        user_level=state["user_level"],
        source_text=state.get("source_text", ""),
        user_translation=state.get("user_translation", ""),
        reference_translation=state.get("reference_translation", ""),
        evaluation=evaluation,
    )
    reflection_output = llm.complete(system, user)
    parsed = _parse_json_from_llm(reflection_output)

    reflection = parsed if parsed else {"final_review": reflection_output}

    # 用复核结果修正 evaluation（内部 QA，不直接展示给学员）
    missed = reflection.get("missed_errors") or []
    if missed:
        existing_tags = list(evaluation.get("error_tags", []))
        existing_issues = list(evaluation.get("major_issues", []))
        evaluation = {
            **evaluation,
            "error_tags": existing_tags + [f"[复核] {e}" for e in missed],
            "major_issues": existing_issues + [f"[复核] {e}" for e in missed],
        }

    inconsistencies = reflection.get("score_inconsistencies") or []
    if inconsistencies:
        dim_scores = dict(evaluation.get("dimension_scores", {}))
        labels = evaluation.get("dimension_labels", {})
        for dim_key in list(dim_scores.keys()):
            label = labels.get(dim_key, dim_key)
            for inc_text in inconsistencies:
                if dim_key in inc_text.lower() or label in inc_text:
                    dim_scores[dim_key] = max(1, dim_scores[dim_key] - 1)
                    break
        if dim_scores:
            new_total = round(sum(dim_scores.values()) / len(dim_scores) * 20)
            evaluation = {
                **evaluation,
                "dimension_scores": dim_scores,
                "score": max(0, min(100, new_total)),
            }

    final_review = reflection.get("final_review", "")
    if final_review:
        existing_review = evaluation.get("review", "")
        evaluation = {
            **evaluation,
            "review": f"{existing_review}\n\n[复核意见] {final_review}".strip(),
        }

    return {
        **state,
        "evaluation": evaluation,
        "_reflection_debug": reflection,
    }


def synthesize_feedback(state: TranslationAgentState) -> TranslationAgentState:
    terminology = state.get("terminology_hits", [])
    terms = "\n".join(
        f"- {row.get('source_term')} -> {row.get('target_term')}：{row.get('note', '')}"
        for row in terminology
    ) or "- 暂未命中术语库。"

    if state.get("task_type") == "generate_exercise":
        report = (
            f"# {state['pair_config']['display_name']}翻译练习\n\n"
            f"难度：{state['user_level']}｜领域：{state['domain']}\n\n"
            f"## 原文\n{state.get('source_text', '')}\n\n"
            f"## 参考译文\n{state.get('reference_translation', '')}\n\n"
            f"## 术语提示\n{terms}\n\n"
            f"## 教学提示\n{state.get('feedback', '')}"
        )
    else:
        evaluation = state.get("evaluation", {})
        dimensions = evaluation.get("dimension_scores", {})
        dimension_text = "\n".join(f"- {name}：{score}/5" for name, score in dimensions.items()) or "- 暂无维度分。"
        tags = "、".join(evaluation.get("error_tags", [])) or "暂无"
        issues = "\n".join(f"- {item}" for item in evaluation.get("major_issues", [])) or "- 暂无。"
        report = (
            f"# {state['pair_config']['display_name']}译文评估报告\n\n"
            f"总分：{evaluation.get('score', 'N/A')}\n\n"
            f"## 维度评分\n{dimension_text}\n\n"
            f"## 原文\n{state.get('source_text', '')}\n\n"
            f"## 学生译文\n{state.get('user_translation', '')}\n\n"
            f"## 参考译文\n{state.get('reference_translation', '')}\n\n"
            f"## 错误标签\n{tags}\n\n"
            f"## 主要问题\n{issues}\n\n"
            f"## 修改建议\n{evaluation.get('revision_advice', '')}\n\n"
            f"## 术语检查\n{terms}\n\n"
            f"## 审校反馈\n{evaluation.get('review') or evaluation.get('note', '')}\n\n"
            f"## 本课总结\n{state.get('session_summary') or '完成本轮练习，查看下方推荐继续训练。'}"
        )

    return {**state, "report": report}


def plan_next_steps(state: TranslationAgentState) -> TranslationAgentState:
    mistake_record = create_mistake_record(state)
    review_plan = create_review_plan(mistake_record)

    # ---- 跨题错误追踪 ----
    error_history: list[dict[str, Any]] = list(state.get("error_history") or [])
    if mistake_record:
        error_history.append(mistake_record)
    error_history = error_history[-20:]  # 保留最近 20 条

    # 检测系统性错误（同一标签出现 >= 2 次）
    from collections import Counter
    tag_counter: Counter[str] = Counter()
    for err in error_history:
        for tag in err.get("error_types", []):
            tag_counter[tag] += 1
    systematic_errors = [tag for tag, count in tag_counter.items() if count >= 2]

    profile_seed = {
        **state,
        "mistake_record": mistake_record,
        "review_plan": review_plan,
    }
    learner_profile = build_learner_profile(profile_seed)

    # ---- LLM 生成个性化下一步 ----
    evaluation = state.get("evaluation", {})
    diagnostics = state.get("diagnostics", {})
    config = state["pair_config"]

    system, user = build_plan_prompt(
        display_name=config["display_name"],
        user_level=state["user_level"],
        evaluation=evaluation,
        diagnostics=diagnostics,
        error_history=error_history,
        systematic_errors=systematic_errors,
    )
    llm_output = llm.complete(system, user)
    parsed = _parse_json_from_llm(llm_output)

    if parsed and parsed.get("next_exercises"):
        next_exercises = parsed["next_exercises"]
        session_summary = parsed.get("summary", "")
        focus_areas = parsed.get("focus_areas", [])
        plan_source = "LLM"
    else:
        next_exercises = [
            {
                "type": "terminology",
                "focus": "术语复习",
                "description": "复习本次命中的核心术语，并造两个目标语例句。",
                "action": "vocab_review",
            },
            {
                "type": "revision",
                "focus": "重译修正",
                "description": "根据审校反馈重译原文，再对照参考译文修改。",
                "action": "focus_retry",
            },
        ]
        session_summary = ""
        focus_areas = diagnostics.get("weaknesses", [])[:2]
        plan_source = "规则"

    dashboard = build_dashboard(
        {
            **profile_seed,
            "learner_profile": learner_profile,
            "next_exercises": next_exercises,
        }
    )

    return {
        **state,
        "mistake_record": mistake_record,
        "review_plan": review_plan,
        "learner_profile": learner_profile,
        "dashboard": dashboard,
        "next_exercises": next_exercises,
        "error_history": error_history,
        "focus_areas": focus_areas,
        "session_summary": session_summary,
        "tool_trace": [
            *state.get("tool_trace", []),
            {
                "tool": "错题本与错误画像工具",
                "result": (
                    f"已记录错题（累计 {len(error_history)} 条，"
                    f"系统性问题：{', '.join(systematic_errors) if systematic_errors else '暂无'}）"
                ),
            },
            {"tool": "间隔复习工具", "result": f"已安排 {len(review_plan)} 个复习任务"},
            {"tool": f"学习策略工具（{plan_source}驱动）", "result": f"已更新下一步推荐"},
        ],
    }
