from __future__ import annotations

import re
from collections import Counter
from datetime import date, timedelta
from typing import Any


RUSSIAN_RE = re.compile(r"[А-Яа-яЁё]")
CHINESE_RE = re.compile(r"[\u4e00-\u9fff]")
WORD_RE = re.compile(r"[A-Za-zА-Яа-яЁё-]+|[\u4e00-\u9fff]+")

ERROR_RULES = [
    ("格错误", ["обучение переводу", "помогать обучение", "для студент"]),
    ("动词体错误", ["буду помогать", "сделал делать"]),
    ("前置词搭配错误", ["в университетом", "на классе", "к перевод"]),
    ("支配关系错误", ["помогать обучение", "ждать автобус"]),
    ("词序错误", ["может интеллектуальный агент"]),
    ("中文直译痕迹", ["进行帮助", "做翻译教学"]),
    ("漏译", []),
    ("表达不自然", ["可以辅助", "осуществлять помощь"]),
]

LEVEL_ORDER = ["A1", "A2", "B1", "B2", "C1"]

EVALUATION_DIMENSIONS = [
    ("accuracy", "语义传达", "原文核心意思是否完整、准确进入译文"),
    ("fluency", "表达自然", "目标语是否自然顺畅，读起来不像硬译"),
    ("terminology", "术语精准", "关键词、术语和固定表达是否准确稳定"),
    ("grammar", "结构正确", "格、体、支配、词序和句法结构是否正确"),
    ("strategy", "策略运用", "语域、风格、文化转换和翻译策略是否恰当"),
]

def _tokenize(text: str) -> list[str]:
    raw_tokens = [token.lower() for token in WORD_RE.findall(text or "")]
    tokens: list[str] = []
    for token in raw_tokens:
        if _has_chinese(token) and len(token) > 4:
            tokens.extend(_segment_chinese(token))
        else:
            tokens.append(token)
    return [token for token in tokens if token]


def _segment_chinese(text: str) -> list[str]:
    dictionary = [
        "智能体",
        "翻译教学",
        "翻译",
        "教学",
        "学习者",
        "训练",
        "教师",
        "学生",
        "辅助",
        "可以",
        "设计",
    ]
    segments = [word for word in dictionary if word in text]
    if segments:
        return segments
    return [text[i : i + 2] for i in range(0, len(text), 2)]


def _has_russian(text: str) -> bool:
    return bool(RUSSIAN_RE.search(text or ""))


def _has_chinese(text: str) -> bool:
    return bool(CHINESE_RE.search(text or ""))


def estimate_difficulty(text: str, level: str) -> dict[str, Any]:
    tokens = _tokenize(text)
    sentence_count = max(1, len(re.findall(r"[。！？.!?]", text or "")) or 1)
    avg_len = round(len(tokens) / sentence_count, 1)
    russian = _has_russian(text)
    abstract_markers = sum(1 for word in tokens if word in {"智能体", "语法", "翻译", "обучение", "перевод", "разрабатывать"})
    clause_markers = sum(1 for word in tokens if word in {"который", "что", "если", "когда", "因为", "如果", "虽然"})
    complexity = len(tokens) + abstract_markers * 2 + clause_markers * 3

    if complexity <= 8:
        estimated = "A2"
    elif complexity <= 16:
        estimated = "B1"
    elif complexity <= 26:
        estimated = "B2"
    else:
        estimated = "C1"

    target_index = LEVEL_ORDER.index(level) if level in LEVEL_ORDER else 2
    estimated_index = LEVEL_ORDER.index(estimated)
    if estimated_index > target_index + 1:
        advice = "题目略难，建议先看结构提示再作答。"
    elif estimated_index < target_index - 1:
        advice = "题目偏容易，可以要求系统增加句长或语体要求。"
    else:
        advice = "难度基本匹配当前水平。"

    return {
        "estimated_level": estimated,
        "token_count": len(tokens),
        "average_sentence_length": avg_len,
        "grammar_load": "含从句或抽象表达" if clause_markers or abstract_markers > 1 else "单句核心结构",
        "target_level": level,
        "advice": advice,
        "language_signal": "ru" if russian else "zh" if _has_chinese(text) else "mixed",
    }


def generate_layered_hints(source_text: str, reference_translation: str, pair_config: dict[str, Any]) -> dict[str, str]:
    source_lang = pair_config.get("source_lang", "")
    target_lang = pair_config.get("target_lang", "")
    focus = pair_config.get("teaching_focus", [])
    tokens = _tokenize(source_text)
    keywords = "、".join(tokens[:4]) if source_lang == "zh" else ", ".join(tokens[:4])
    reference_head = (reference_translation or "").split()
    half_hint = " ".join(reference_head[: max(2, len(reference_head) // 2)]) if reference_head else "先完成主干，再处理修饰成分。"

    return {
        "vocabulary": f"先确认关键词：{keywords or '核心名词和动词'}。不要急着看完整答案。",
        "structure": "先找主干：谁做什么，再处理对象、目的和修饰语。",
        "grammar": f"重点注意：{focus[0] if focus else f'{source_lang}->{target_lang} 的语序和搭配'}。",
        "half_sentence": half_hint,
    }


def diagnose_level(source_text: str, user_translation: str, level: str, pair_config: dict[str, Any]) -> dict[str, Any]:
    evidence = " ".join([source_text or "", user_translation or ""])
    difficulty = estimate_difficulty(evidence, level)
    tokens = _tokenize(user_translation or evidence)
    has_output = bool((user_translation or "").strip())
    estimate = level

    if has_output and len(tokens) < 4 and level in {"B1", "B2", "C1"}:
        estimate = "A2+"
    elif has_output and len(tokens) >= 10 and difficulty["estimated_level"] in {"B1", "B2"}:
        estimate = f"{level}-"
    elif not has_output:
        estimate = level

    weaknesses = []
    for tag, patterns in ERROR_RULES:
        if any(pattern in (user_translation or source_text or "") for pattern in patterns):
            weaknesses.append(tag)
    if not weaknesses:
        weaknesses = ["搭配准确性", "目标语自然表达"]

    strengths = []
    if has_output:
        strengths.append("能够主动完成目标语产出")
    if len(tokens) >= 8:
        strengths.append("能处理完整句子信息")
    if not strengths:
        strengths.append("可以从短句理解和分层提示开始")

    direction = pair_config.get("display_name", "翻译")
    return {
        "estimated_level": estimate,
        "strengths": strengths,
        "weaknesses": weaknesses[:3],
        "recommended_path": [
            f"先做 3 题{direction}短句训练",
            "每题提交后重译一次",
            f"针对“{weaknesses[0]}”做变式复习",
        ],
        "difficulty": difficulty,
    }


def validate_llm_evaluation(
    llm_output: dict[str, Any],
    reference_translation: str,
    pair_config: dict[str, Any],
) -> dict[str, Any]:
    """校验并规范化 LLM 生成的评估结果。规则引擎只做格式校验和边界检查。"""
    dimensions = pair_config.get("evaluation_dimensions", [])

    raw_scores = llm_output.get("dimension_scores", {})
    validated_scores: dict[str, int] = {}
    for dim in dimensions:
        score = raw_scores.get(dim, 3)
        if not isinstance(score, (int, float)):
            score = 3
        validated_scores[dim] = max(1, min(5, round(score)))

    total = llm_output.get("score")
    if not isinstance(total, (int, float)):
        total = round(sum(validated_scores.values()) / max(1, len(validated_scores)) * 20)
    total = max(0, min(100, round(total)))

    dim_xp = llm_output.get("dimension_xp", {})
    if isinstance(dim_xp, dict):
        validated_xp = {}
        for dim in dimensions:
            xp_val = dim_xp.get(dim, 0)
            if not isinstance(xp_val, (int, float)):
                xp_val = 0
            validated_xp[dim] = max(0, min(30, int(xp_val)))
    else:
        validated_xp = {}

    return {
        "score": total,
        "dimension_scores": validated_scores,
        "dimension_labels": {key: label for key, label, _description in EVALUATION_DIMENSIONS},
        "dimension_descriptions": {key: description for key, _label, description in EVALUATION_DIMENSIONS},
        "error_tags": _normalize_list(llm_output.get("error_tags")),
        "major_issues": _normalize_list(llm_output.get("major_issues")),
        "revision_advice": str(llm_output.get("revision_advice", "")),
        "review": str(llm_output.get("review", "")),
        "recommended_translation": reference_translation,
        "acceptable_alternatives": _alternatives(reference_translation),
        "needs_retry": total < 85,
        "dimension_xp": validated_xp,
    }


def _normalize_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str) and value:
        return [value]
    return []


def score_translation(
    source_text: str,
    user_translation: str,
    reference_translation: str,
    pair_config: dict[str, Any],
) -> dict[str, Any]:
    if not user_translation.strip():
        return {
            "score": None,
            "dimension_scores": {},
            "error_tags": [],
            "major_issues": ["还没有提交译文。"],
            "revision_advice": "先尝试独立翻译，再请求词汇或结构提示。",
            "needs_retry": True,
        }

    user_tokens = set(_tokenize(user_translation))
    ref_tokens = set(_tokenize(reference_translation))
    source_tokens = set(_tokenize(source_text))
    overlap = len(user_tokens & ref_tokens)
    possible = max(1, len(ref_tokens))
    semantic_ratio = min(1.0, overlap / possible)

    tags = []
    for tag, patterns in ERROR_RULES:
        if any(pattern.lower() in user_translation.lower() for pattern in patterns):
            tags.append(tag)
    if ref_tokens and semantic_ratio < 0.25:
        tags.append("语义偏离")
    if source_tokens and len(user_tokens) < max(3, len(source_tokens) // 3):
        tags.append("漏译")
    if not tags:
        tags.append("表达可继续打磨")

    accuracy = max(2, min(5, round(2 + semantic_ratio * 3)))
    fluency = 3 if "表达不自然" in tags or "中文直译痕迹" in tags else 4
    terminology = 3 if "术语不一致" in tags else 4
    grammar = 3 if any(tag in tags for tag in ["格错误", "动词体错误", "前置词搭配错误", "支配关系错误"]) else 4
    completeness = 3 if "漏译" in tags else 4
    strategy_score = 3 if "语义偏离" in tags else 4
    strategy_final = min(strategy_score, fluency, completeness)
    dimension_scores = {
        "accuracy": accuracy,
        "fluency": fluency,
        "terminology": terminology,
        "grammar": grammar,
        "strategy": strategy_final,
    }
    total = round(sum(dimension_scores.values()) / (len(dimension_scores) * 5) * 100)

    return {
        "score": total,
        "dimension_scores": dimension_scores,
        "dimension_labels": {key: label for key, label, _description in EVALUATION_DIMENSIONS},
        "dimension_descriptions": {key: description for key, _label, description in EVALUATION_DIMENSIONS},
        "error_tags": list(dict.fromkeys(tags)),
        "major_issues": _issue_texts(tags),
        "revision_advice": _revision_advice(tags, pair_config),
        "recommended_translation": reference_translation,
        "acceptable_alternatives": _alternatives(reference_translation),
        "needs_retry": total < 85,
    }


def _issue_texts(tags: list[str]) -> list[str]:
    mapping = {
        "格错误": "名词格或动词支配关系需要优先修正。",
        "动词体错误": "动词体的选择和语境还不稳定。",
        "前置词搭配错误": "前置词和后接格的搭配需要检查。",
        "支配关系错误": "动词后接成分与目标语习惯不一致。",
        "中文直译痕迹": "译文保留了中文表达顺序，目标语不够自然。",
        "漏译": "原文部分信息没有进入译文。",
        "语义偏离": "译文与参考译文共享信息较少，需要重新确认原文意思。",
        "表达不自然": "意思基本可见，但目标语搭配不够自然。",
        "表达可继续打磨": "主要意思可见，下一步重点打磨自然度和语体。",
    }
    return [mapping.get(tag, tag) for tag in tags[:4]]


def _revision_advice(tags: list[str], pair_config: dict[str, Any]) -> str:
    focus = pair_config.get("teaching_focus", [])
    if "漏译" in tags or "语义偏离" in tags:
        return "先逐词核对原文信息，再重写主干句。"
    if any(tag in tags for tag in ["格错误", "前置词搭配错误", "支配关系错误"]):
        return "先标出动词和它支配的成分，再检查格和前置词。"
    if "中文直译痕迹" in tags:
        return "保留原意，但按目标语常用语序重组句子。"
    return f"继续关注{focus[0] if focus else '语义准确和表达自然'}。"


def _alternatives(reference_translation: str) -> list[str]:
    if not reference_translation:
        return []
    if _has_russian(reference_translation):
        return [reference_translation.replace("разрабатывает", "создает")]
    return [reference_translation.replace("智能", "智能化")]


def analyze_grammar(sentence: str, pair_config: dict[str, Any]) -> dict[str, Any]:
    tokens = _tokenize(sentence)
    if not sentence.strip():
        return {
            "spine": "暂无句子。先生成练习或输入原文。",
            "modifiers": [],
            "key_grammar": [],
            "translation_difficulty": [],
            "common_misreadings": [],
            "tokens": [],
        }

    if _has_russian(sentence):
        verbs = [token for token in tokens if token.endswith(("ть", "ет", "ют", "ал", "ла", "ли", "ает", "яет"))]
        preps = [token for token in tokens if token in {"в", "на", "к", "с", "для", "о", "об", "по"}]
        nouns = [token for token in tokens if token not in verbs and token not in preps]
        return {
            "spine": f"先找谓语 {verbs[0] if verbs else '核心动词'}，再确认动作发出者和对象。",
            "modifiers": ["前置词短语需要和后接格一起看。"] if preps else ["修饰成分较少，适合先练主干理解。"],
            "key_grammar": [
                "动词支配关系",
                "前置词后接格",
                "名词性数格一致",
            ],
            "translation_difficulty": ["俄语信息顺序进入汉语时需要重组。"],
            "common_misreadings": ["不要把每个俄语词按原顺序硬译成汉语。"],
            "tokens": [{"text": token, "role": _ru_role(token, verbs, preps, nouns)} for token in tokens],
        }

    return {
        "spine": "先确定主语、谓语和宾语，再决定俄语中需要的格和词序。",
        "modifiers": ["“面向/用于/为了”等结构通常需要转成 для 或目的结构。"],
        "key_grammar": pair_config.get("teaching_focus", ["汉俄语序转换", "俄语格和体的选择"])[:3],
        "translation_difficulty": ["汉语省略的信息在俄语中常需要补出性数格或前置词。"],
        "common_misreadings": ["不要把“可以”机械译成 можно，先判断句子实际语气。"],
        "tokens": [{"text": token, "role": _zh_role(token)} for token in tokens],
    }


def _ru_role(token: str, verbs: list[str], preps: list[str], nouns: list[str]) -> str:
    if token in verbs:
        return "谓语/动词"
    if token in preps:
        return "前置词"
    if token in nouns[:2]:
        return "核心名词"
    return "修饰或补足成分"


def _zh_role(token: str) -> str:
    if any(marker in token for marker in ["可以", "正在", "能够"]):
        return "谓语或情态"
    if any(marker in token for marker in ["智能体", "教师", "学生"]):
        return "主语/名词"
    if any(marker in token for marker in ["翻译", "教学", "训练"]):
        return "对象/主题"
    return "修饰或补足成分"


def build_vocabulary_cards(sentence: str, terminology_hits: list[dict[str, str]], pair_config: dict[str, Any]) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for row in terminology_hits:
        cards.append(
            {
                "term": row.get("source_term", ""),
                "translation": row.get("target_term", ""),
                "meaning": row.get("note", "") or "术语库命中词。",
                "collocations": [row.get("target_term", ""), f"{row.get('source_term', '')} + 相关动词"],
                "risk": "注意术语一致性，不要同一词多种译法混用。",
                "example": row.get("example", ""),
                "retrieval_prompt": f"不看答案，先回忆“{row.get('source_term', '')}”在本句中应如何表达。",
                "cloze": _cloze_sentence(sentence, row.get("source_term", "")),
                "production_task": f"用“{row.get('target_term', '')}”造一个和学习/翻译相关的目标语短句。",
                "memory_cue": _memory_cue(row.get("source_term", ""), row.get("target_term", "")),
                "review_interval": "10 分钟后复述，明天做一次填空，3 天后造句。",
            }
        )

    fallback_terms = _tokenize(sentence)[:5] or _default_vocab_terms(pair_config)
    for token in fallback_terms:
        if any(card["term"].lower() == token.lower() for card in cards):
            continue
        cards.append(
            {
                "term": token,
                "translation": _rough_translation(token),
                "meaning": "建议在句中记忆，不只背单个释义。",
                "collocations": _collocations(token),
                "risk": "检查它和动词、前置词或名词的搭配。",
                "example": sentence,
                "retrieval_prompt": f"遮住答案，先说出“{token}”在本句中的目标语表达。",
                "cloze": _cloze_sentence(sentence, token),
                "production_task": f"用“{_rough_translation(token)}”围绕本题主题造一个短句。",
                "memory_cue": _memory_cue(token, _rough_translation(token)),
                "review_interval": "现在回忆一次，课后 10 分钟再回忆，明天用它造句。",
            }
        )
        if len(cards) >= 6:
            break
    return cards


def _default_vocab_terms(pair_config: dict[str, Any]) -> list[str]:
    if pair_config.get("source_lang") == "ru":
        return ["перевод", "обучение", "задание", "студент", "ошибка"]
    return ["翻译", "学习者", "训练", "教师", "错误"]


def _cloze_sentence(sentence: str, token: str) -> str:
    if sentence and token and token in sentence:
        return sentence.replace(token, "____", 1)
    return "把该词放回原句语境中，先补空再核对答案。"


def _memory_cue(term: str, translation: str) -> str:
    if not term:
        return "把词义、搭配和原句一起记。"
    return f"线索：{term} -> {translation}；同时记一个常见搭配。"


def _rough_translation(token: str) -> str:
    lexicon = {
        "智能体": "интеллектуальный агент",
        "翻译": "перевод",
        "教学": "обучение",
        "学习者": "изучающий",
        "训练": "тренировка",
        "教师": "преподаватель",
        "错误": "ошибка",
        "перевод": "翻译",
        "обучение": "教学/学习",
        "задание": "任务/练习",
        "студент": "学生",
        "ошибка": "错误",
        "агент": "智能体/代理",
    }
    return lexicon.get(token, "结合上下文判断")


def _collocations(token: str) -> list[str]:
    if token in {"перевод", "翻译"}:
        return ["обучение переводу", "translation training", "翻译训练"]
    if token in {"обучение", "教学"}:
        return ["обучение чему?", "辅助教学", "教学任务"]
    return [f"{token} + 核心动词", f"{token} + 修饰成分"]


def create_mistake_record(state: dict[str, Any]) -> dict[str, Any]:
    evaluation = state.get("evaluation", {})
    tags = evaluation.get("error_tags") or []
    if not tags:
        return {}

    return {
        "source_text": state.get("source_text", ""),
        "student_answer": state.get("user_translation", ""),
        "recommended_answer": evaluation.get("recommended_translation") or state.get("reference_translation", ""),
        "error_types": tags,
        "reason": evaluation.get("major_issues", ["本题需要重看。"])[0],
        "related_points": (state.get("pair_config") or {}).get("teaching_focus", [])[:2],
        "review_count": 0,
        "last_result": "待复习" if evaluation.get("needs_retry") else "基本掌握",
    }


def create_review_plan(mistake_record: dict[str, Any], dashboard: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    today = date.today()
    plan = []
    if mistake_record:
        tags = mistake_record.get("error_types", ["错题"])
        for offset, mode in [(0, "原题重做"), (1, "变式练习"), (3, "反向翻译")]:
            plan.append(
                {
                    "due": (today + timedelta(days=offset)).isoformat(),
                    "mode": mode,
                    "focus": tags[0],
                    "task": _review_task(mode, mistake_record),
                }
            )
    else:
        plan.append(
            {
                "due": today.isoformat(),
                "mode": "轻量复习",
                "focus": "术语和搭配",
                "task": "复述本题核心词汇，并用其中一个词造句。",
            }
        )
    return plan


def _review_task(mode: str, mistake_record: dict[str, Any]) -> str:
    source = mistake_record.get("source_text", "")
    if mode == "原题重做":
        return f"不看答案重译：{source}"
    if mode == "变式练习":
        return f"保留同一语法点，替换主题后再译：{source}"
    return "看推荐译文，反向还原原文意思。"


def build_learner_profile(state: dict[str, Any]) -> dict[str, Any]:
    diagnostics = state.get("diagnostics", {})
    evaluation = state.get("evaluation", {})
    tags = evaluation.get("error_tags", [])
    dimensions = evaluation.get("dimension_scores", {})
    dimension_labels = evaluation.get("dimension_labels", {})
    tag_counts = Counter(tags)
    sorted_dimensions = sorted(dimensions.items(), key=lambda item: item[1])
    strengths = [f"{dimension_labels.get(name, name)} {score}/5" for name, score in sorted_dimensions[-2:]][::-1]
    risks = [f"{dimension_labels.get(name, name)} {score}/5" for name, score in sorted_dimensions[:2]]
    if tags:
        risks.extend(tags[:2])
    return {
        "level": diagnostics.get("estimated_level") or state.get("user_level", "B1"),
        "goal": f"提升{(state.get('pair_config') or {}).get('display_name', '翻译')}准确度和自然度",
        "feedback_preference": "标准批改",
        "common_errors": [{"tag": tag, "count": count} for tag, count in tag_counts.most_common(5)],
        "weak_grammar": diagnostics.get("weaknesses", [])[:3],
        "familiar_terms": [hit.get("source_term", "") for hit in state.get("terminology_hits", [])],
        "performance_strengths": strengths or diagnostics.get("strengths", [])[:2],
        "performance_risks": risks or diagnostics.get("weaknesses", [])[:3],
        "progress_note": "本次结果已作为学习画像更新依据。" if evaluation.get("score") is not None else "生成练习后提交译文即可更新画像。",
        "recent_activity": state.get("task_type", "generate_exercise"),
    }


def build_dashboard(state: dict[str, Any]) -> dict[str, Any]:
    evaluation = state.get("evaluation", {})
    profile = state.get("learner_profile", {})
    score = evaluation.get("score")
    due = state.get("review_plan", [])
    common_errors = profile.get("common_errors", [])
    return {
        "today_work": "1 个学习任务" if state.get("source_text") else "等待开始",
        "accuracy_trend": "本次可作为新的基线" if score is not None else "生成练习后提交译文即可更新",
        "current_score": score,
        "error_top": common_errors or [{"tag": item, "count": 1} for item in profile.get("weak_grammar", [])[:3]],
        "mastered_points": profile.get("familiar_terms", []) or ["主干识别"],
        "progress_strengths": profile.get("performance_strengths", []),
        "progress_risks": profile.get("performance_risks", []),
        "progress_note": profile.get("progress_note", ""),
        "review_due_count": len(due),
        "next_task": (state.get("next_exercises") or [{}])[0].get("description", "完成当前练习并重译一次"),
    }


# 5 等级 × 5 称号 × 5 维度 = RPG 进阶矩阵
_LEVEL_NAMES = ["A1", "A2", "B1", "B2", "C1"]
_XP_PER_LEVEL = 300
_RANK_NAMES: dict[int, list[str]] = {
    0: ["萌新译者", "初识译者", "学习译者", "见习译者", "突破译者"],   # A1
    1: ["入门译者", "成长译者", "磨砺译者", "自信译者", "精进译者"],   # A2
    2: ["进阶译者", "独立译者", "熟练译者", "成熟译者", "卓越译者"],   # B1
    3: ["高阶译者", "专业译者", "精英译者", "权威译者", "大师译者"],   # B2
    4: ["专家译者", "特级译者", "首席译者", "传奇译者", "宗师译者"],   # C1
}
_LEVEL_DESCRIPTIONS: dict[int, str] = {
    0: "建立翻译基础能力",
    1: "夯实基本功，接触更多语境",
    2: "胜任常规翻译任务",
    3: "处理复杂翻译场景",
    4: "已达专家水平，继续精进",
}


def compute_ability_rank(ability_xp: dict[str, int]) -> dict[str, Any]:
    """根据累计 XP 计算当前等级、称号和进阶状态。

    ability_xp: {"accuracy": int, "fluency": int, "terminology": int, "grammar": int, "strategy": int}
    每维上限 = 等级数 × 300 = 1500
    """
    dim_keys = [key for key, _label, _desc in EVALUATION_DIMENSIONS]
    dim_labels = {key: label for key, label, _desc in EVALUATION_DIMENSIONS}

    # 初始化缺失维度
    xp = {k: ability_xp.get(k, 0) for k in dim_keys}

    # 当前等级由最低维度分决定
    min_xp = min(xp.values())
    level_index = min(min_xp // _XP_PER_LEVEL, len(_LEVEL_NAMES) - 1)
    current_level = _LEVEL_NAMES[level_index]

    # 在当前等级内的进度：取该等级起始分到当前分的差值
    level_start = level_index * _XP_PER_LEVEL
    level_xp = min_xp - level_start  # 0-300
    rank = min(level_xp // 60 + 1, 5)  # 1-5
    current_title = _RANK_NAMES[level_index][rank - 1]

    # 下一称号
    if rank < 5:
        next_title = _RANK_NAMES[level_index][rank]
        progress_to_next = level_xp % 60
    else:
        # 当前等级已满，如果还有下一等级
        if level_index < len(_LEVEL_NAMES) - 1:
            next_title = _RANK_NAMES[level_index + 1][0]
        else:
            next_title = "已封顶"
        progress_to_next = _XP_PER_LEVEL - level_xp  # 距解锁下一等级

    # 是否可以晋升到下一等级
    next_level_threshold = (level_index + 1) * _XP_PER_LEVEL
    can_advance_level = (
        level_index < len(_LEVEL_NAMES) - 1
        and all(v >= next_level_threshold for v in xp.values())
    )

    # 各维度在当前等级内的进度 (0-300)
    per_dim_progress: dict[str, dict[str, Any]] = {}
    for k in dim_keys:
        dim_total = xp[k]
        dim_level_xp = dim_total - level_index * _XP_PER_LEVEL
        per_dim_progress[k] = {
            "total": dim_total,
            "current_level_xp": min(dim_level_xp, _XP_PER_LEVEL),
            "cap": _XP_PER_LEVEL,
            "label": dim_labels.get(k, k),
        }

    # 找出最短板（瓶颈维度）
    bottleneck_dim = min(xp, key=lambda k: xp[k])
    bottleneck_label = dim_labels.get(bottleneck_dim, bottleneck_dim)
    xp_needed = next_level_threshold - xp[bottleneck_dim]

    return {
        "current_level": current_level,
        "level_index": level_index,
        "current_rank": rank,
        "current_title": current_title,
        "next_title": next_title,
        "progress_to_next": progress_to_next,  # 距下一称号还需几分
        "can_advance_level": can_advance_level,
        "xp_needed_for_next_level": max(0, xp_needed),
        "bottleneck_dim": bottleneck_dim,
        "bottleneck_label": bottleneck_label,
        "per_dim_progress": per_dim_progress,
        "ability_xp": xp,
        "level_description": _LEVEL_DESCRIPTIONS.get(level_index, ""),
    }


def compute_ability_stats(
    ability_xp: dict[str, int] | None,
    progress_history: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """整合能力排名、进度和趋势统计。"""
    rank_info = compute_ability_rank(ability_xp or {})

    history = progress_history or []
    trend = "new"
    if len(history) >= 3:
        scores = [e.get("score", 0) for e in history if isinstance(e.get("score"), (int, float))]
        if len(scores) >= 3 and scores[-1] > scores[0]:
            trend = "improving"
        elif len(scores) >= 3 and scores[-1] < scores[0]:
            trend = "declining"
        else:
            trend = "stable"

    return {
        **rank_info,
        "total_exercises": len(history),
        "recent_trend": trend,
    }
