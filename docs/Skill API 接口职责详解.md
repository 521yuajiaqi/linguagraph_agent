# Skill API 四接口职责详解

## 接口总览

| 接口 | 负责什么 | 用到的模块 |
|---|---|---|
| evaluate | 五维翻译评估 | prompts.py + llm.py + learning.py |
| generate | 翻译练习生成 | exercise_generation.py + prompts.py + llm.py + resources.py + learning.py |
| rank | RPG 等级计算 | learning.py |
| terminology | 术语检索词汇卡 | resources.py + learning.py |

---

## 一、evaluate — 五维翻译评估

**路径：** `POST /api/skill/evaluate`

**输入：** source_text, user_translation, reference_translation, language_pair, user_level

**处理流程：**

```
第1步：加载语言对配置
       → config.py load_language_pair()
       → 读取 configs/language_pairs/zh_ru.yaml

第2步：用户译文为空？
       → learning.py score_translation()
       → 返回 "还没有提交译文"

第3步：构建评估 prompt
       → prompts.py build_evaluate_prompt()
       → system prompt：5条评估原则 + 6条自我复核准则
       → user prompt：原文 + 学生译文 + 参考译文 + dimension_xp 加分指导

第4步：LLM 评估（核心）
       → llm.py LLMClient.complete()
       → 调 DeepSeek deepseek-chat 模型
       → 输出 JSON 含 score, dimension_scores, error_tags, major_issues, revision_advice, review, dimension_xp

第5步：解析 LLM 输出
       → skill_api.py _parse_json_from_llm()
       → 支持 markdown 代码块和裸 JSON 两种格式

第6步：校验评分
       → learning.py validate_llm_evaluation()
       → 维度分归一化到 1-5
       → 总分 0-100
       → dimension_xp 归一化到 0-30
       → 补上维度标签（语义传达/表达自然/术语精准/结构正确/策略运用）

第7步（兜底）：LLM 解析失败
       → learning.py score_translation() 规则引擎
       → 用 token 重叠率估算语义相似度
       → 用 ERROR_RULES 硬编码错误模式检测语法问题
       → 五维评分全部由规则计算

返回：完整 evaluation JSON
```

**涉及的语法/规则来源：**

| 组件 | 位置 | 干什么 |
|---|---|---|
| EVALUATION_DIMENSIONS | learning.py:26-32 | 五维定义（key + 中文标签 + 描述） |
| ERROR_RULES | learning.py:13-22 | 硬编码俄语错误模式：格错误、动词体错误、前置词搭配错误、支配关系错误、词序错误、中文直译痕迹、漏译、表达不自然 |
| 评分规则 | learning.py score_translation() | token 重叠算语义，错误标签映射到维度分，总分加权 |
| 格式校验 | learning.py validate_llm_evaluation() | 边界检查、分数截断、维度分归一化 |

---

## 二、generate — 翻译练习生成

**路径：** `POST /api/skill/generate`

**输入：** language_pair, user_level, domain, focus_areas, previous_source, learner_profile, error_history

**处理流程：**

```
第1步：出题画像
       → exercise_generation.py build_exercise_blueprint()
       → 根据 focus_areas / learner_profile / error_history 决定：
         · primary_focus：主要训练哪个维度（accuracy/fluency/terminology/grammar/strategy）
         · syntax_load：句法难度（low/medium/high）
         · terminology_load：术语负荷（low/medium/high）
         · difficulty_band：难度窗口

第2步：题库匹配（优先）
       → exercise_generation.py select_exercise_candidate()
       → 在 TAGGED_EXERCISE_BANK（7题）中按多维度打分排序：
         · 等级匹配 +4分
         · 训练焦点匹配 +6分
         · 句法负荷匹配 +2分
         · 术语负荷匹配 +2分
         · 领域匹配 +1分
         · 避免和上一题重复 -5分
       → 取最高分，<4 分算不匹配

第3步（题库没匹配上）：LLM 出题
       → prompts.py build_exercise_generation_prompt()
       → llm.py LLMClient.complete() 调 DeepSeek
       → exercise_generation.py validate_generated_exercise_payload() 校验格式

第4步（LLM 也失败）：安全兜底
       → skill_api.py 内部 _EXERCISE_BANK（8题）
       → 避开上一题，选下一题

第5步：生成分层提示
       → learning.py generate_layered_hints()
       → 四层提示：
         · vocabulary：提取关键词 token
         · structure：先找主干，再处理修饰
         · grammar：从语言对 YAML 的 teaching_focus 取
         · half_sentence：展示参考译文前半句

第6步：术语检索
       → resources.py find_terminology_hits()
       → 读 CSV：resources/terminology/{pair}/{domain}.csv → general.csv
       → 在原文中匹配术语

第7步：生成词汇卡
       → learning.py build_vocabulary_cards()
       → 每个术语生成：translation, collocations, example, cloze 填空, 
         production_task 造句, memory_cue 记忆线索, review_interval 间隔复习
       → 没有命中术语时，从 source_text 的 token 中取前 5 个词生成卡片

第8步：语法分析
       → learning.py analyze_grammar()
       → 俄语：识别动词（ть/ет/ют/ал 等词尾）、前置词（в/на/к/с/для）、名词
       → 汉语：识别主语/谓语/对象
       → 输出：句子主干、修饰成分、关键语法点、翻译难点、常见误读

第9步：难度评估
       → learning.py estimate_difficulty()
       → token 数 + 抽象标记 + 从句标记 → 复杂度分 → CEFR 估算

返回：完整练习包
```

**出题的三个数据源（按优先级）：**

| 优先级 | 来源 | 题数 | 位置 |
|---|---|---|---|
| 1 | TAGGED_EXERCISE_BANK（带标签的题库） | 中俄3题 + 俄中1题 | exercise_generation.py:64-113 |
| 2 | LLM 生成（DeepSeek） | 动态 | 调 LLM |
| 3 | _EXERCISE_BANK（基础题库） | 中俄4题 + 俄中4题 | skill_api.py:120-152 |

---

## 三、rank — RPG 能力等级

**路径：** `POST /api/skill/rank`

**输入：** accuracy, fluency, terminology, grammar, strategy（5 个 int）

**处理流程：**

```
第1步：取五维 XP 最低值
       → 最低维度决定整体等级（短板锁机制）

第2步：算当前等级和称号
       → min_xp / 300 → CEFR 等级索引
       → 等级内进度 / 60 → 称号（1-5）
       → 查 RANK_NAMES 矩阵取称号名

第3步：找瓶颈维度
       → 五维中 XP 最低的那个
       → 距下一等级还需多少 XP

第4步：各维度进度百分比
       → 每个维度在当前等级内的完成百分比

第5步：判断能否晋级
       → 五维全部 ≥ 下一等级阈值时允许晋级

返回：等级/称号/瓶颈/进度
```

**所有数据来源：**

| 组件 | 位置 | 内容 |
|---|---|---|
| XP_PER_LEVEL = 300 | learning.py:573 | 每级所需 XP |
| LEVEL_NAMES | learning.py:572 | A1/A2/B1/B2/C1 |
| RANK_NAMES | learning.py:574-580 | 5×5 = 25 阶称号矩阵 |
| LEVEL_DESCRIPTIONS | learning.py:581-587 | 每级描述 |
| 维度标签 | learning.py EVALUATION_DIMENSIONS | 五维中英文标签 |

---

## 四、terminology — 术语检索与词汇卡

**路径：** `POST /api/skill/terminology`

**输入：** language_pair, domain, source_text

**处理流程：**

```
第1步：加载语言对配置
       → config.py load_language_pair()

第2步：检索术语
       → resources.py find_terminology_hits()
       → 读 resources/terminology/zh_ru/general.csv
       → 在 source_text 中字符串匹配，命中的术语存入列表

第3步：生成词汇卡
       → learning.py build_vocabulary_cards()
       → 每个术语生成完整卡片
       → 额外从 source_text token 中取前几个词生成补充卡片

第4步：语法分析
       → learning.py analyze_grammar()
       → 分词 → 标注词性 → 语法难点 → 翻译陷阱

返回：术语命中列表 + 词汇卡列表 + 语法分析
```

**术语数据来源：**

| 文件 | 内容 |
|---|---|
| resources/terminology/zh_ru/general.csv | 中俄通用术语表 |
| resources/terminology/zh_ru/{domain}.csv | 领域专用术语（academic/business 等，待扩展） |
| resources/terminology/ru_zh/general.csv | 俄中通用术语表（待扩展） |

---

## 五、公共依赖一览

| 模块 | 被哪些接口用 | 职责 |
|---|---|---|
| config.py | evaluate, generate, terminology | 加载语言对 YAML 配置、读术语 CSV |
| llm.py | evaluate, generate | DeepSeek API 适配（langchain-openai） |
| prompts.py | evaluate, generate | 构建 LLM 的 system/user prompt |
| resources.py | generate, terminology | 术语库检索（CSV 字符串匹配） |
| learning.py | 全部四个 | 规则引擎 + RPG 系统 + 分层提示 + 词汇卡 + 语法分析 + 难度评估 |
| exercise_generation.py | generate | 出题画像 + 题库匹配 + LLM 出题校验 |
