"""Prompt templates extracted from nodes.py and exercise_generation.py.

All prompt builders return (system: str, user: str) tuples so they can be
reused by both the LangGraph workflow (nodes.py) and the standalone Skill API
(skill_api.py).
"""

from __future__ import annotations

from typing import Any


# ── Translation Evaluation Prompt ──────────────────────────────────────────

def build_evaluate_prompt(
    display_name: str,
    user_level: str,
    source_text: str,
    user_translation: str,
    reference_translation: str,
    dimensions: list[str],
) -> tuple[str, str]:
    """Build (system, user) prompt pair for five-dimension translation evaluation.

    The system prompt embeds self-reflection instructions so that the LLM
    double-checks its own scores before returning — merging the old
    ``evaluate_translation`` + ``reflect_on_evaluation`` into one call.
    """
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
        "6. 自我复核：输出前请自查——\n"
        "   a) 学生译文是否有真实的语法错误、语义偏差或用词不当？如果没有，总分不应低于 85。\n"
        "   b) error_tags 是否每个都对应真实存在的错误？不要编造不存在的问题。\n"
        "   c) 评分与 error_tags 是否一致？如果有 error_tags 但给高分（90+），请重新检查。\n"
        "   d) revision_advice 中的建议例句是否语法正确？不要给出有语法错误的「改进建议」。\n\n"
        "输出必须是严格的JSON格式，不要包含markdown代码块标记或其他文字。"
    )

    user = (
        f"语种方向：{display_name}\n"
        f"学生水平：{user_level}\n"
        f"原文：{source_text}\n"
        f"学生译文：{user_translation}\n"
        f"参考译文（仅作为参考，不是唯一正确答案）：{reference_translation}\n\n"
        f"重要提醒：\n"
        f"- 如果学生译文语义正确、语法无误、表达自然，即使与参考译文不同，也应给出高分（85+）\n"
        f"- 只有在存在真实的语法错误、语义偏差或用词不当时，才标记 error_tags 和 major_issues\n"
        f"- revision_advice 只针对真正的问题给出建议；如果学生译文已经正确，"
        f"revision_advice 可为空或写「译文已基本正确，无需修改」\n"
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

    return system, user


# ── Standalone Reflection Prompt (used by LangGraph flow only) ────────────

def build_reflection_prompt(
    display_name: str,
    user_level: str,
    source_text: str,
    user_translation: str,
    reference_translation: str,
    evaluation: dict[str, Any],
) -> tuple[str, str]:
    """Build (system, user) prompt for evaluating an existing evaluation.

    Used by the ``reflect_on_evaluation`` node in the full LangGraph workflow.
    The Skill API skips this step because the evaluate prompt already embeds
    self-check instructions.
    """
    system = (
        "你是翻译教学的资深审校专家。现在需要你复核一份翻译评估结果。复核时请特别注意：\n\n"
        "1. 假阳性误判：评估是否把学生正确的译法（虽与参考译文不同但语义准确、语法正确、表达自然）"
        "误判为错误？\n"
        "2. 建议准确性：revision_advice 中给出的修改建议例句是否真的比学生的译文更好？"
        "如果建议的句子本身有语法错误或不自然，应标记为误判。\n"
        "3. 评分一致性：dimension_scores 与 major_issues 是否一致？"
        "如果 error_tags 和 major_issues 为空，总分不应过低（低于 80 分才需有明显错误支撑）。\n"
        "4. 遗漏检查：是否存在学生译文中真实存在、但未被标记的错误？\n\n"
        "注意：学生译文与参考译文用词不同但意思正确、表达地道的，不属于误判，不需要标记。"
    )
    user = (
        f"语种方向：{display_name}\n"
        f"学生水平：{user_level}\n"
        f"原文：{source_text}\n"
        f"学生译文：{user_translation}\n"
        f"参考译文：{reference_translation}\n\n"
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
    return system, user


# ── Next-Steps Planning Prompt ─────────────────────────────────────────────

def build_plan_prompt(
    display_name: str,
    user_level: str,
    evaluation: dict[str, Any],
    diagnostics: dict[str, Any],
    error_history: list[dict[str, Any]] | None = None,
    systematic_errors: list[str] | None = None,
) -> tuple[str, str]:
    """Build (system, user) prompt for generating personalized next-step plans."""
    system = (
        "你是翻译教学的学习策略专家。根据学生本轮评估结果和错误历史，"
        "设计 2-3 个最能提升学生水平的后续训练动作。"
        "输出必须是严格的JSON格式，不要包含markdown代码块标记或其他文字。"
    )

    history_summary = ""
    if error_history:
        recent_tags = [
            tag
            for err in error_history[-3:]
            for tag in err.get("error_types", [])
        ]
        systematic_list = systematic_errors or []
        history_summary = (
            f"近期错误标签：{'、'.join(recent_tags[:8])}\n"
            f"系统性错误（重复出现）：{'、'.join(systematic_list) if systematic_list else '暂无'}\n"
        )

    user = (
        f"语种方向：{display_name}\n"
        f"学生水平：{user_level}\n"
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
    return system, user


# ── Exercise Generation Prompt ─────────────────────────────────────────────

def build_exercise_generation_prompt(
    display_name: str,
    domain: str,
    blueprint: dict[str, Any],
    examples: list[dict[str, str]] | None = None,
) -> tuple[str, str]:
    """Build (system, user) prompt for LLM-generated translation exercises.

    If ``examples`` is provided, they are included as few-shot style references
    so the LLM produces exercises of similar difficulty and format.
    """
    target = blueprint["target_level"]

    # Level-specific constraints — give the LLM concrete word-count and
    # complexity targets so A1 exercises actually differ from C1.
    level_guide = {
        "A1": (
            "【词数】3-6 词，必须只用 1 个简单句。"
            "【词汇】限高频基础词：人称（я/ты/он）、家庭成员、天气、时间、数字、颜色、常见食物。"
            "【语法】只能用现在时、主谓宾或主系表基本语序。禁止任何从句、形动词、副动词、被动结构。"
            "【话题】自我介绍、问候、家庭、天气、日常物品。"
        ),
        "A2": (
            "【词数】6-10 词，可用 1 个并列结构（и/а/но 连接）。"
            "【词汇】日常高频词：购物、出行、爱好、饮食、服饰、简单情绪。"
            "【语法】可用简单过去时或将来时，不超过 1 个时态切换。禁止从句。"
            "【话题】周末计划、日常习惯、简单喜好、家庭介绍。"
        ),
        "B1": (
            "【词数】10-18 词，可含 1 个从句（что/чтобы/который/если/когда/потому что）。"
            "【词汇】开始涉及抽象词：观点、感受、计划、原因、结果。"
            "【语法】必须包含 1 个语法难点：运动动词（идти/ходить/ехать/ездить）、"
            "完成体/未完成体区分、动词支配关系（ждать+二格/四格）、带-ся 动词。"
            "【话题】学习经历、旅行见闻、职业规划、社会现象简述。"
        ),
        "B2": (
            "【词数】15-25 词，可含 1-2 个从句（允许嵌套一层）。"
            "【词汇】专业词汇适量：科技趋势、职场沟通、环境议题、经济常识。术语必须准确。"
            "【语法】必须使用以下至少 1 种高级结构：形动词短语（主动/被动）、副动词短语、"
            "被动结构（带-ся 或被动形动词短尾）、带 либо/нибудь 的不定代词。"
            "【话题】技术评论、职场分析、社会时评、专业领域概述。"
        ),
        "C1": (
            "【词数】20-40 词，可含多层嵌套（2-3 层从句）。"
            "【词汇】学术/专业/文化深度词汇，允许低频词和术语。需体现语用细微差异（正式/口语、褒贬）。"
            "【语法】必须混合使用以下至少 2 种：多重从句叠加、主动形动词、被动形动词、"
            "副动词、无人称句、不定式句、带语气词（же/ли/ведь/разве）的修辞结构。"
            "【话题】学术论述、专业分析、文化评论、哲学思辨、政策解读。"
        ),
    }

    system = (
        "你是翻译教学专家，精通 CEFR 等级标准。"
        "你必须输出严格 JSON，不得输出解释、标题、代码块或额外说明。"
    )

    example_text = ""
    if examples:
        parts = []
        for i, ex in enumerate(examples, 1):
            parts.append(
                f"样例{i}：\n"
                f"  原文：{ex.get('source_text', '')}\n"
                f"  参考译文：{ex.get('reference_translation', '')}"
            )
        example_text = (
            "\n【参考样例题】请按以下风格和难度出新题，不要照抄：\n"
            + "\n".join(parts)
            + "\n"
        )

    user = (
        f"请出一道{display_name}翻译练习题。\n\n"
        f"领域：{domain}\n"
        f"主训练维度：{blueprint['primary_focus']}\n"
        f"目标等级：{target}\n"
        f"句法负荷：{blueprint['syntax_load']}\n"
        f"术语负荷：{blueprint['terminology_load']}\n"
        f"教学意图：{blueprint['teaching_intent']}\n\n"
        f"【{target} 等级要求】{level_guide.get(target, level_guide['B1'])}\n"
        f"{example_text}"
        "要求：严格按照等级要求出题。原文和参考译文必须是你原创的，不要照抄样例题。"
        '输出 {{"source_text": "...", "reference_translation": "..."}}'
    )
    return system, user


# ── Lightweight Quick-Score Prompt (for diagnosis short sentences) ─────────

def build_quick_score_prompt(
    source_text: str,
    user_translation: str,
    reference_translation: str,
) -> tuple[str, str]:
    """Build a minimal prompt for quick 1-5 scoring of a short translation."""
    system = "你是翻译评分专家。请对以下短句翻译进行快速评分（1-5分），只输出数字。"
    user = (
        f"原文：{source_text}\n"
        f"学生译文：{user_translation}\n"
        f"参考译文：{reference_translation}\n\n"
        f"评分标准：5=完美, 4=基本准确有小瑕疵, 3=意思对但表达不自然, "
        f"2=部分正确, 1=完全错误\n"
        f"只输出数字（1-5）："
    )
    return system, user
