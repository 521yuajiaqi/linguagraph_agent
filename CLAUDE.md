# LinguaGraph — 翻译学习智能体平台

FastAPI + Next.js 16 前后端分离的翻译教学平台，基于 LangGraph 多节点 Agent 实现诊断→练习→反馈→复习四步学习闭环。

## 技术栈

| 层 | 技术 |
|---|---|
| 后端框架 | FastAPI (Python 3.11) |
| Agent 引擎 | LangGraph (`lingua_agent/graph.py`) |
| LLM 适配 | langchain-openai → DeepSeek `deepseek-chat`（兼容 OpenAI API） |
| 前端框架 | Next.js 16 App Router + React 19 |
| 样式 | Tailwind CSS v4（`@theme inline` 在 `src/app/layout.css`） |
| 状态管理 | Zustand + localStorage persist |
| 图表 | Recharts |
| 动画 | Framer Motion |

## 项目结构

```
Agent/
├── web_app.py              # FastAPI 入口，所有 HTTP 端点
├── lingua_agent/           # 后端 Agent 核心
│   ├── graph.py            # LangGraph 状态图定义（7 节点工作流）
│   ├── nodes.py            # 节点实现（generate/evaluate/reflect/synthesize/plan）
│   ├── state.py            # TranslationAgentState TypedDict
│   ├── config.py           # YAML 语言对配置加载
│   ├── llm.py              # LLMClient — OpenAI-compatible 适配器
│   ├── diagnosis.py        # 诊断模块（选题生成 + 答题评分）
│   ├── resources.py        # 术语库检索
│   └── tools/
│       └── learning.py     # 规则引擎 + 能力统计 + RPG 等级系统
├── configs/language_pairs/ # 语言对 YAML 配置（zh_ru.yaml, ru_zh.yaml）
├── resources/              # 术语库等静态资源
├── frontend/               # Next.js 16 前端
│   └── src/
│       ├── app/
│       │   ├── layout.tsx           # 根布局（AppShell）
│       │   ├── (steps)/
│       │   │   ├── layout.tsx       # 步骤页共享布局（StepIndicator）
│       │   │   ├── diagnosis/       # 步骤 1：能力诊断
│       │   │   ├── practice/        # 步骤 2：翻译练习
│       │   │   ├── feedback/        # 步骤 3：译文反馈
│       │   │   └── review/          # 步骤 4：复习仪表盘
│       │   └── page.tsx             # 首页（重定向到 diagnosis）
│       ├── components/
│       │   ├── layout/              # AppShell, TopNav, Sidebar, StepIndicator
│       │   └── shared/             # LoadingSpinner, EmptyState, ErrorBoundary, ScoreBar, Tag
│       ├── lib/
│       │   ├── api/                 # API 客户端（client, session, diagnosis, practice, review）
│       │   ├── stores/              # Zustand stores（6 个）
│       │   └── utils/               # types.ts, constants.ts, formatters.ts
│       └── hooks/                   # useHintProgression, useKeyboardShortcuts
├── .sessions/               # 会话持久化 JSON 文件（自动创建）
└── md/                      # 设计文档
```

## 启动方式

**环境要求：** 后端必须使用 conda 环境 `nlp`（Python 3.11）。启动命令必须用 `& "C:\Users\Win11\anaconda3\envs\nlp\python.exe"`，不能依赖 `conda activate`（在 PowerShell 后台任务中不生效）。

```powershell
# 后端（端口 8000）
& "C:\Users\Win11\anaconda3\envs\nlp\python.exe" -m uvicorn web_app:app --host 127.0.0.1 --port 8000 --reload

# 前端（端口 3000）
cd frontend; npm run dev
```

**注意：** 不要用 `python web_app.py`，文件内没有 `if __name__ == "__main__"` 块，必须通过 uvicorn 启动。`--reload` 开启热重载。

## 后端架构

### LangGraph 工作流（7 节点）

```
initialize_context
    ↓ (按 task_type 分流)
generate_exercise ──→ terminology_check
evaluate_translation → reflect_on_evaluation → terminology_check
                                                   ↓
                                          synthesize_feedback
                                                   ↓
                                           plan_next_steps → END
```

- **initialize_context** — 解析语言对、方向、水平等上下文
- **generate_exercise** — 出题画像驱动的翻译练习生成：题库优先，LLM 受约束 fallback
- **evaluate_translation** — LLM 多维度评分 + 规则引擎 fallback（`score_translation`）
- **reflect_on_evaluation** — LLM 自我复核，内部修正误判、评分不一致（不对外暴露）
- **terminology_check** — 术语命中 + 语法解析 + 词汇卡生成
- **synthesize_feedback** — 整合为 Markdown 评估报告
- **plan_next_steps** — 错题记录 + 间隔复习 + LLM 推荐下一步训练

### API 端点（9 个）

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/run` | 原始 Agent 调用（旧接口） |
| POST | `/api/session/init` | 创建会话，初始化 ability_xp 归零 |
| GET | `/api/session/{id}` | 获取会话完整数据 |
| POST | `/api/diagnosis/start` | 生成 5 道诊断题 |
| POST | `/api/diagnosis/submit` | 提交答案，返回 CEFR 估算水平 |
| POST | `/api/practice/generate` | 生成练习，缓存到 session |
| POST | `/api/practice/evaluate` | 评估译文，累加 ability_xp |
| GET | `/api/review/dashboard` | 聚合仪表盘 + ability_stats |
| GET | `/api/review/mistakes` | 错题列表（支持 error_type/status 筛选） |
| POST | `/api/review/drill` | 生成弱项专练 |
| POST | `/api/review/vocabulary/rate` | SRS 词汇评分 |

### 会话持久化

会话以 JSON 文件存储在 `.sessions/{session_id}.json`，内存有 `_sessions_cache` 缓存。关键字段：
- `ability_xp` — 五维累计 XP，初始 `{"accuracy":0, "fluency":0, "terminology":0, "grammar":0, "strategy":0}`
- `progress_history` — 最近 60 条评测记录
- `mistakes` — 最近 50 条错题
- `_current_exercise` — 当前练习原文/参考译文

### 评测管道（关键数据流）

```
LLM evaluate → validate_llm_evaluation → reflect_on_evaluation (修正)
                                              ↓
                                    evaluation 含 dimension_xp
                                              ↓
                                    web_app 累加到 session["ability_xp"]
                                              ↓
                                    review_dashboard 返回 ability_stats
```

`dimension_xp` 必须经过 `validate_llm_evaluation` 透传——之前这里遗漏导致 XP 不累加，已修复（`learning.py:193`）。

## 五维 RPG 能力体系（核心设计）

借鉴《死亡搁浅》五维评价体系，25 阶称号成长路径。

### 五个评测维度

| 维度 key | 中文标签 | 对标 |
|---|---|---|
| accuracy | 语义传达 | 核心意思完整准确 |
| fluency | 表达自然 | 目标语自然流畅 |
| terminology | 术语精准 | 关键词/术语准确 |
| grammar | 结构正确 | 语法/句法正确 |
| strategy | 策略运用 | 语域/风格/文化转换 |

### 等级进阶（XP 制）

每维 300 XP 一级，维度全满（≥下一级阈值）才能解锁下一 CEFR 等级：

| 等级 | XP 范围 | 称号 Lv.1-5 |
|---|---|---|
| A1 | 0-300 | 萌新译者 → 突破译者 |
| A2 | 300-600 | 入门译者 → 精进译者 |
| B1 | 600-900 | 进阶译者 → 卓越译者 |
| B2 | 900-1200 | 高阶译者 → 大师译者 |
| C1 | 1200-1500 | 专家译者 → 宗师译者 |

每级内每 60 XP 晋升一级称号（1-5），最低维度分决定整体等级。

关键函数在 `lingua_agent/tools/learning.py`：
- `compute_ability_rank(ability_xp)` — 从 XP 计算等级/称号/瓶颈
- `compute_ability_stats(ability_xp, progress_history)` — 整合趋势统计

### 前端对应

- `types.ts` — `AbilityStats` 接口（含 `per_dim_progress`, `bottleneck_dim`, `xp_needed_for_next_level` 等）
- `AbilityCard.tsx` — 等级徽章 + 五维 XP 条 + 瓶颈提示 + 趋势
- `DIMENSION_LABELS` / `DIMENSION_ORDER` — 5 项（非 6 项）

## 前端约定

### 路由即页面

`src/app/(steps)/` 下的四个文件夹直接映射四步闭环。`layout.tsx` 渲染共享的 `StepIndicator`。

### Zustand Store 模式

6 个 store 均使用 `persist` middleware，key 以 `linguagraph.*` 命名空间：
- `session-store` — sessionId, languagePair, userLevel, domain, mode
- `step-store` — 当前步骤
- `diagnosis-store` — 题目列表、答案、报告
- `practice-store` — 当前练习、用户输入
- `feedback-store` — evaluation 结果
- `review-store` — progressHistory, reviewPlan

### 样式系统

Tailwind CSS v4 使用 CSS-first 配置（`@theme inline` in `layout.css`），**没有** `tailwind.config.ts`。自定义 CSS 变量：
- `--accent`, `--green`, `--amber`, `--purple`, `--teal`, `--danger`
- `--panel`, `--panel-soft`, `--line`, `--muted`

### 组件约定

- 共享组件在 `src/components/shared/`：LoadingSpinner, EmptyState, ErrorBoundary, ScoreBar, Tag
- 步骤专属组件在各步骤的 `_components/` 目录下
- 组件文件名用 PascalCase
- `"use client"` 指令在需要交互的组件顶部

### 已知陷阱

1. **Tailwind v4 不支持 `@apply`** 在组件 scoped styles 中——内联 `style` 或直接用 utility classes
2. **Next.js 16 App Router** 与旧版有 breaking changes——以 `node_modules/next/dist/docs/` 中的文档为准
3. **DIMENSION_ORDER 是 5 项不是 6 项**——之前从 6 合并到 5（style + cultural → strategy）
4. **前端 API 调用**都走 `src/lib/api/` 模块，不要直接在组件中 fetch
