from __future__ import annotations

import json
import re
from typing import Any

from lingua_agent.config import load_language_pair
from lingua_agent.llm import LLMClient
from lingua_agent.resources import find_terminology_hits
from lingua_agent.state import TranslationAgentState
from lingua_agent.tools import (
    analyze_grammar,
    build_dashboard,
    build_exercise_blueprint,
    build_llm_exercise_messages,
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
    dim_spec = "\n".join(f'        "{d}": <1-5 分>,' for d in dimensions)

    system = (
        "你是具有教学意识的翻译审校专家。评估学生译文时请遵循以下原则：\n\n"
        "1. 灵活性原则：参考译文只是「一种可能的正确译法」，不是唯一标准。同一原文可以有多种地道表达，"
        "只要学生译文语义准确、语法正确、表达自然，就应给予高分，不应仅因与参考译文用词不同而扣分。\n"
        "2. 意义优先：先判断学生译文是否准确传达了原文的核心意思，再检查语法、用词、语体等细节。"
        "如果语义完全正确但表达方式与参考译文不同，这不属于错误。\n"
        "3. 错误分级：区分「真正的错误」（语法错误、语义偏差、用词不当）和「风格偏好」（更地道的说法、"
        "更简洁的表达），后者不应扣分，可以作为可选建议提供。\n"
        "4. 建议准确性：给学生的修改建议中，你提供的例句必须是语法正确、表达地道的目标语言句子。"
        "如果学生的译法已经正确，不要强行推荐另一种译法——没有问题的句子不需要「改进」。\n"
        "5. 鼓励为主：反馈应以帮助学生进步为目标，先肯定做得好的部分，再指出可以提升的地方。\n\n"
        "输出必须是严格的JSON格式，不要包含markdown代码块标记或其他文字。"
    )
    user = (
        f"语种方向：{state['pair_config']['display_name']}\n"
        f"学生水平：{state['user_level']}\n"
        f"原文：{state.get('source_text', '')}\n"
        f"学生译文：{state.get('user_translation', '')}\n"
        f"参考译文（仅作为参考，不是唯一正确答案）：{state.get('reference_translation', '')}\n\n"
        f"重要提醒：\n"
        f"- 如果学生译文语义正确、语法无误、表达自然，即使与参考译文不同，也应给出高分（85+）\n"
        f"- 只有在存在真实的语法错误、语义偏差或用词不当时，才标记 error_tags 和 major_issues\n"
        f"- revision_advice 只针对真正的问题给出建议；如果学生译文已经正确，revision_advice 可为空或写「译文已基本正确，无需修改」\n"
        f"- revision_advice 中给出的例句必须确保是地道、正确的目标语言表达，不要生成有语法错误的建议\n\n"
        f"dimension_xp 加分指导（每次练习给每个维度加 0-30 分）：\n"
        f"- 该维度表现优秀（无明显错误）：25-30 分\n"
        f"- 该维度表现良好（有小瑕疵但不影响理解）：15-24 分\n"
        f"- 该维度表现一般（存在明显错误）：5-14 分\n"
        f"- 该维度出现严重错误：0-4 分\n"
        f"- 学生水平越低，加分标准应相对宽松，以鼓励学习积极性\n\n"
        f"请按以下JSON格式输出评估结果：\n"
        f"{{\n"
        f'  "score": <0-100 总分，正确但表达不同也应给高分>,\n'
        f'  "dimension_scores": {{\n{dim_spec}\n'
        f"  }},\n"
        f'  "error_tags": ["<错误类型标签，无明显错误时为空数组>"],\n'
        f'  "major_issues": ["<具体问题描述，仅列出真正的问题，不要编造>"],\n'
        f'  "revision_advice": "<可执行的修改建议，仅针对真正存在的问题；学生译文已正确则说明无需修改>",\n'
        f'  "review": "<整体评语，先肯定优点，再指出1-2个核心改进方向>",\n'
        f'  "dimension_xp": {{\n'
        f'    "accuracy": <0-30>,\n'
        f'    "fluency": <0-30>,\n'
        f'    "terminology": <0-30>,\n'
        f'    "grammar": <0-30>,\n'
        f'    "strategy": <0-30>\n'
        f'  }}\n'
        f"}}"
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

    system = (
        "你是翻译教学的资深审校专家。现在需要你复核一份翻译评估结果。复核时请特别注意：\n\n"
        "1. 假阳性误判：评估是否把学生正确的译法（虽与参考译文不同但语义准确、语法正确、表达自然）误判为错误？\n"
        "2. 建议准确性：revision_advice 中给出的修改建议例句是否真的比学生的译文更好？"
        "如果建议的句子本身有语法错误或不自然，应标记为误判。\n"
        "3. 评分一致性：dimension_scores 与 major_issues 是否一致？"
        "如果 error_tags 和 major_issues 为空，总分不应过低（低于 80 分才需有明显错误支撑）。\n"
        "4. 遗漏检查：是否存在学生译文中真实存在、但未被标记的错误？\n\n"
        "注意：学生译文与参考译文用词不同但意思正确、表达地道的，不属于误判，不需要标记。"
    )
    user = (
        f"语种方向：{state['pair_config']['display_name']}\n"
        f"学生水平：{state['user_level']}\n"
        f"原文：{state.get('source_text', '')}\n"
        f"学生译文：{state.get('user_translation', '')}\n"
        f"参考译文：{state.get('reference_translation', '')}\n\n"
        f"当前评估结果：\n"
        f"  总分：{evaluation.get('score')}\n"
        f"  维度评分：{evaluation.get('dimension_scores')}\n"
        f"  错误标签：{evaluation.get('error_tags')}\n"
        f"  主要问题：{evaluation.get('major_issues')}\n"
        f"  修改建议：{evaluation.get('revision_advice')}\n"
        f"  审校评语：{evaluation.get('review')}\n\n"
        f"请复核以上评估，输出JSON：\n"
        f'{{"has_misjudgment": true/false,'
        f' "missed_errors": ["遗漏的错误"] or [],'
        f' "score_inconsistencies": ["评分与问题描述不一致之处"] or [],'
        f' "final_review": "复核后的总结评语"}}'
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

    system = (
        "你是翻译教学的学习策略专家。根据学生本轮评估结果和错误历史，"
        "设计 2-3 个最能提升学生水平的后续训练动作。"
        "输出必须是严格的JSON格式，不要包含markdown代码块标记或其他文字。"
    )
    history_summary = ""
    if error_history:
        recent_tags = [tag for err in error_history[-3:] for tag in err.get("error_types", [])]
        history_summary = (
            f"近期错误标签：{'、'.join(recent_tags[:8])}\n"
            f"系统性错误（重复出现）：{'、'.join(systematic_errors) if systematic_errors else '暂无'}\n"
        )

    user = (
        f"语种方向：{config['display_name']}\n"
        f"学生水平：{state['user_level']}\n"
        f"本轮评分：{evaluation.get('score', 'N/A')}\n"
        f"维度评分：{evaluation.get('dimension_scores', {})}\n"
        f"错误标签：{evaluation.get('error_tags', [])}\n"
        f"弱项：{diagnostics.get('weaknesses', [])}\n"
        f"强项：{diagnostics.get('strengths', [])}\n"
        f"{history_summary}\n"
        f"请设计 2-3 个后续训练动作，按以下JSON输出：\n"
        f'{{"summary": "本轮学习总结（2-3句话，鼓励性）",'
        f' "next_exercises": ['
        f'{{"type": "术语/语法/重译/弱项专练",'
        f' "focus": "训练焦点（如：格支配练习）",'
        f' "description": "具体操作说明",'
        f' "action": "regenerate/focus_retry/vocab_review"}}'
        f'],'
        f' "focus_areas": ["下一轮应重点训练的维度"]}}'
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
