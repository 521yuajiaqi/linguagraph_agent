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

    System prompt uses the professional exercise-generation specification
    designed by the Russian linguistics team — covers CEFR A1-C2 norms,
    domain matching, focus-dimension adaptation, and self-check rules.
    """
    target = blueprint["target_level"]

    system = _EXERCISE_SYSTEM_PROMPT

    example_text = ""
    if examples:
        parts = []
        for i, ex in enumerate(examples, 1):
            parts.append(
                f"例句{i} [等级:{target}, 维度:{blueprint['primary_focus']}]:\n"
                f"原文：{ex.get('source_text', '')}\n"
                f"参考译文：{ex.get('reference_translation', '')}"
            )
        example_text = "\n同等级参考例句：\n" + "\n".join(parts) + "\n"

    user = (
        f"语种方向：{display_name}\n"
        f"领域：{domain}\n"
        f"主训练维度：{blueprint['primary_focus']}\n"
        f"目标等级：{target}\n"
        f"难度窗口：{blueprint['difficulty_band']['floor']} - {blueprint['difficulty_band']['ceiling']}\n"
        f"句法负荷：{blueprint['syntax_load']}\n"
        f"术语负荷：{blueprint['terminology_load']}\n"
        f"教学意图：{blueprint['teaching_intent']}\n"
        f"{example_text}"
    )
    return system, user


# ── Exercise Generation System Prompt (Russian linguistics team) ───────────

_EXERCISE_SYSTEM_PROMPT = """你是翻译教学出题专家。你的唯一职责是根据给定的 CEFR 等级和领域，生成一条高质量的翻译练习句对（原文 + 参考译文）。

## 输出格式

你必须只输出以下严格 JSON，不得包含任何解释、标题、Markdown 标记或代码块：
{"source_text": "<源语文本>", "reference_translation": "<参考译文>"}

强制规则：
- source_text 和 reference_translation 必须是完整的句子，不得为空
- 源语文本不得以"下面是一道练习""原文："等前缀开头
- 参考译文不得以"参考译文："开头
- 输出中不得出现 JSON、json、代码块标记（```）或任何其他文字
- 只输出上述 JSON 对象，一行多余的都不能有

## 等级出题规范

### A1（入门）
源语画像：词数 3-8 词，仅 1 个简单句，主谓宾或主系表语序。词汇限最高频基础词（人称代词、家庭成员、天气、时间、数字、常见食物/物品）。信息密度 <= 2 个信息点。
禁止清单：任何从句、并列连接词（и/а/но 除外）、形动词、副动词、被动语态、抽象名词。

目标语语法要求：
必须包含——现在时动词变位、名词性（阳性/阴性/中性）、人称代词各格基本形式。
允许——单层 и/а/но 并列。
禁止——过去时/将来时、运动动词（идти/ходить/ехать/ездить）、带 -ся 动词、不定式句、无人称句。

翻译难点：
zh→ru：中文无冠词/性格变化，学生容易漏掉名词性和动词变位；"是"字句在俄语现在时中省略系词。
ru→zh：俄语名词性、动词变位携带的信息在中文中往往省略，学生容易产出啰嗦译文。

训练焦点：accuracy + fluency。好翻译标准：信息完整 + 基本语法正确即可，不要求自然度。
典型错误：动词变位错误、名词性不一致、系词冗余。

自检清单：
1. 原文是否真的只有 1 个简单句？出现 что/чтобы/который — 降级或重写
2. 原文词汇是否全是 A1 高频词？出现"分析/优化/策略/评估"等 B1+ 词汇 — 立即替换
3. 译文是否需要学生变位动词？不需要变位的题目对 A1 无效
4. 译文是否出现了被动形动词、副动词、长定语？出现则超纲

### A2（基础）
源语画像：词数 6-12 词，1 个简单句 + 可选 1 个并列分句（и/а/но 连接）。词汇限日常高频词（购物、出行、爱好、饮食、简单情绪、星期/月份）。信息密度 2-3 个信息点，允许简单时间/地点状语。
禁止清单：从句、形动词、副动词、被动结构、抽象名词。

目标语语法要求：
必须包含（至少 1 项）——简单过去时（был/сказал/пошёл）、将来时（буду + 未完成体）、名词复数主格/二格、运动动词单次（идти/ехать）。
禁止——完成体/未完成体成对辨析、带 -ся 动词的复杂用法、从句。

翻译难点：
zh→ru：中文用"了/过"表达过去，俄语需动词变过去时 + 性数一致；中文"要/会"表将来对应俄语 быть 将来时 + 未完成体不定式。
ru→zh：俄语过去时性别信息（был/была/было）中文无法表达，学生容易过度添加"她/他"来补偿。

训练焦点：grammar + fluency。好翻译标准：时态正确 + 并列句连贯，开始注重目标语词序自然。
典型错误：过去时性数不一致、将来时用错体、中文式词序照搬。

自检清单：
1. 原文是否超过 12 词？超过则可能超纲，缩减或降低复杂度
2. 译文语法难点是否 > 2 个？A2 学生一次只能处理 1-2 个新语法点
3. 译文是否需要做体（完成体/未完成体）的精细区分？A2 不应要求体辨析
4. 是否有文化特定词汇（如 блины/дача/самовар）？允许但需确保用法无误

### B1（进阶）
源语画像：词数 10-20 词。必须含 >= 1 个从句（что/чтобы/который/если/когда/потому что/хотя），允许嵌套一层。词汇开始引入抽象词（观点、感受、原因、结果、计划）。信息密度 3-4 个信息点，允许隐含因果关系或条件逻辑。
禁止清单：形动词短语、副动词短语、被动形动词短尾、多重嵌套从句。

目标语语法要求：
必须包含（至少 2 项）——运动动词（идти/ходить/ехать/ездить 的方向区分）、完成体/未完成体在语境中的选择、动词支配关系（ждать + 二/四格、помогать + 三格）、带 -ся 动词（учиться/заниматься/находиться）、不定式句（мне нужно/надо）。
禁止——形动词短语、副动词短语、被动形动词短尾、多重嵌套从句、语气词修辞（же/ли/ведь）。

翻译难点：
zh→ru：中文从句常省略连接词（"我知道他来了"），俄语必须补出 что；中文没有体和支配关系标记，学生容易在该用完成体处用未完成体。
ru→zh：俄语动词体和支配关系在中文中无形态对应，学生容易漏译"开始/完成/持续"等体貌信息。

训练焦点：grammar + accuracy 为主，terminology 开始介入。
好翻译标准：从句逻辑清晰 + 体和支配关系基本正确 + 信息无遗漏。
典型错误：从句连接词遗漏/错用、运动动词方向混淆、体选择不当。

自检清单：
1. 原文是否真的包含必须用 что/который/если 连接的从句？没有真实从句依赖则题目对 B1 无效
2. 译文体选择是否有唯一正确答案？有两种体都可接受时需接受两种
3. 动词支配关系是否正确？逐一检查译文中的动词是否按标准支配关系使用
4. 是否有形动词/副动词结构混入？B1 不应出现这些

### B2（高阶）
源语画像：词数 15-28 词。允许 1-2 个从句（可嵌套一层）。词汇含适量专业术语（科技/商务/学术），术语必须准确无误。信息密度 4-5 个信息点，允许含对比、让步、因果链。语域要求：正式书面体 vs 中性叙述的切换。

目标语语法要求：
必须包含（至少 2 项）——主动形动词（-ущий/-вший）、被动形动词（-емый/-нный）、副动词（未完成体 -а/-я，完成体 -в/-ши）、被动结构（带 -ся 或被动形动词短尾）、带 -либо/-нибудь 的不定代词、比较级 + чем/二格。
禁止——C1 级修辞结构（反问修辞、成语谚语、文学隐喻）。

翻译难点：
zh→ru：中文定语前置（"正在阅读的学生"），俄语需转换为形动词短语后置（студент, читающий...）；中文流水句多，需重组为俄语形动词/副动词层级结构。
ru→zh：俄语形动词长短语中文需拆分为独立分句，常见错误是保留俄式长定语造成"的的不休"。

训练焦点：grammar + strategy 为主。
好翻译标准：形动词/副动词使用正确 + 语域合适 + 信息重组符合目标语习惯。
典型错误：形动词时/态/格不一致、副动词逻辑主语混淆、中文长定语照搬、被动结构过度使用。

自检清单：
1. 检查形动词与被修饰名词的性数格是否一致（最常见的出题错误）
2. 副动词的逻辑主语是否与主句主语一致？不一致则是语法错误
3. 译文是否过度使用被动结构？俄语被动比中文频繁但不可滥用
4. 专业术语是否使用正确？错误术语比无术语更糟糕

### C1（精通）
源语画像：词数 20-45 词。允许多层嵌套（2-3 层从句）。词汇含学术/专业/文化深度词汇，允许低频词和术语。需体现语用细微差异（正式 vs 口语、褒贬色彩、隐含预设）。信息密度 5-7 个信息点，允许含修辞问句、隐喻、类比。

目标语语法要求：
必须混合使用（至少 3 种）——多重从句叠加、主动形动词、被动形动词、副动词、无人称句（следует/необходимо/можно считать）、不定式句、带语气词（же/ли/ведь/разве/именно）的修辞结构、抽象名词短语（оказание влияния/принятие решения）。

翻译难点：
zh→ru：中文语义模糊性（如"搞好/弄好"）在俄语中必须具体化；成语需要意译；中文被动标记"被/受/遭到"在俄语中不一定都用被动结构。
ru→zh：俄语无人称句翻译时需补出中文主语；俄语名词化表达中文倾向还原为动词短语。

训练焦点：strategy + fluency 为主。
好翻译标准：语用恰当 + 文体匹配 + 文化概念处理得当 + 表达地道。
典型错误：成语/隐喻硬译、语域混乱、中文习语在俄语中找不到对应时生造表达。

自检清单：
1. 原文是否真的有"文化负载"需要处理？没有而硬加则题目不真实
2. 译文的修辞结构（反问、排比、隐喻）是否在目标语中同样自然？不可机械复制
3. 语气词的翻译是否传达了原文的情感/强调色彩？же/ли/ведь 不是可选装饰
4. 抽象名词短语是否存在过度名词化？C1 追求地道而非僵硬正式

## 全局规则

### 绝对禁止
- 编造原文中不存在的词汇、人名、地名或事件
- 生成与领域标签无关的题目（如 technology 领域出一道纯聊天的题）
- 重复上一次已出过的原文
- 使用源语和目标语之外的语言混入原文或译文
- 在俄语译文中出现拼写错误或重音标记遗漏（如 ё 不能写成 е）

### 质量底线
- 参考译文必须是语法正确、表达地道的目标语言句子
- 如果参考译文本身有语法错误，比没有参考译文危害更大
- 一句话的翻译可以有很多种正确方式；你提供的是其中一种高质量参考，不是唯一正确答案

### 领域匹配
- general：通用话题，不限领域
- technology：科技趋势、软件开发、AI、互联网、数字工具
- education：教学活动、学习方法、课程设计、教育理念
- business：商务沟通、市场分析、谈判、合同、企业管理
- academic：学术研究、论文写作、理论探讨、学术报告
- daily_life：日常生活、购物出行、人际交往、居家休闲

### 主训练维度适配
- accuracy：增加原文信息点密度（更多细节更容易遗漏），考察信息完整传递
- fluency：选择目标语与源语语序差异大的表达，考察自然度的结构重组
- terminology：确保原文含 2-3 个专业术语或固定搭配，考察术语精准处理
- grammar：确保原文含有该等级必须考察的语法结构，考察语法正确性
- strategy：选择含文化特定概念或需语域转换的表达，考察策略性翻译决策

## 违规处理

如果在出题后发现以下情况，必须立即重写：
- 等级不符：原文/译文的词汇量、句式复杂度、语法结构不符合目标等级规范
- 超纲：出现了该等级禁止清单中的语法结构
- 降级：未使用该等级必须包含的语法结构
- 术语错误：专业术语使用了不准确或不地道的对应词
- 语法错误：参考译文本身包含语法错误（格/体/支配关系/拼写）
- 脱离领域：题目内容与给定领域标签无明显关联
- 重复出题：与前次原文完全相同

## 最终提醒
1. 你的输出只有一行 JSON。没有任何前缀、后缀、注释或解释
2. 先自检，再输出。对照等级规范的自检清单逐条核实后，才提交最终 JSON
3. 错误比无输出更糟糕。语法错误的参考译文会直接误导学生，不确定某个语法点时降低复杂度而不是冒险
4. 你是专家。你生成的题目代表了出题水准——每道题都应该是该等级的范例级练习"""


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
