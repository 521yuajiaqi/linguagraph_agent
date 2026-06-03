# LinguaGraph

基于 **LangGraph** + Next.js 16 + FastAPI 的智能翻译教学平台，支持中俄/俄中翻译的练习生成、批改反馈、能力诊断与复习管理。借鉴《死亡搁浅》五维 RPG 评价体系，25 阶称号成长路径。

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | Next.js 16 App Router, React 19, Zustand, Tailwind CSS v4, Recharts, Framer Motion |
| 后端 | FastAPI (Python 3.11), LangGraph, langchain-openai |
| LLM | OpenAI 兼容接口 (DeepSeek `deepseek-chat`) |

## 项目结构

```
LinguaGraph/
├── web_app.py              # FastAPI 应用入口 (API 路由定义)
├── run_web.py              # uvicorn 启动脚本
├── main.py                 # CLI 入口 (命令行测试用)
├── requirements.txt        # Python 依赖
├── openai.env              # LLM API 配置模板
│
├── lingua_agent/           # Agent 核心
│   ├── graph.py            # LangGraph 工作流定义
│   ├── nodes.py            # 7 个图节点实现
│   ├── state.py            # AgentState 类型定义
│   ├── llm.py              # LLM 客户端 (OpenAI 兼容)
│   ├── config.py           # 配置加载
│   ├── diagnosis.py        # 诊断模块（选题生成 + 答题评分）
│   ├── resources.py        # 术语/提示词资源
│   └── tools/              # Agent 工具集
│       └── learning.py     # 规则引擎 + 能力统计 + RPG 等级系统
│
├── configs/language_pairs/ # 语种配置 (YAML)
│   ├── zh_ru.yaml
│   └── ru_zh.yaml
│
├── resources/terminology/  # 术语库 (CSV)
│   └── zh_ru/general.csv
│
├── tests/                  # 后端测试
│
├── md/                     # 设计文档
│
└── frontend/               # Next.js 前端
    ├── next.config.ts      # API 代理配置
    └── src/
        ├── app/            # App Router 页面
        │   ├── (steps)/    # 学习闭环步骤
        │   │   ├── diagnosis/  # 步骤 1：能力诊断
        │   │   ├── practice/   # 步骤 2：翻译练习
        │   │   ├── feedback/   # 步骤 3：译文反馈
        │   │   └── review/     # 步骤 4：复习仪表盘
        │   ├── layout.tsx
        │   └── layout.css      # Tailwind v4 主题配置
        ├── components/     # 共享 + 步骤专属组件
        └── lib/
            ├── api/        # API 客户端模块
            ├── stores/     # Zustand 状态管理（6 个 store）
            └── utils/      # 类型定义 & 工具函数
```

## 快速启动

### 环境要求

- **后端**: Python 3.11（推荐 conda 环境 `nlp`）
- **前端**: Node.js 20+

### 1. 后端

```powershell
# 安装依赖 (首次)
pip install -r requirements.txt

# 启动后端 (端口 8000)
python run_web.py
# 或直接:
python -m uvicorn web_app:app --host 127.0.0.1 --port 8000 --reload
```

### 2. 前端

```powershell
cd frontend
npm install    # 首次
npm run dev    # 启动开发服务器 (端口 3000)
```

### 3. 配置 LLM

复制 `openai.env` 为 `.env`，编辑填入你的 API Key：

```ini
OPENAI_API_KEY="sk-xxxxxxxx"
OPENAI_BASE_URL="https://api.deepseek.com"
LINGUAGRAPH_MODEL="deepseek-chat"
```

变量名遵循 langchain-openai 标准命名，支持任意 OpenAI 兼容 API。

### 4. 访问

浏览器打开 `http://localhost:3000`，前端通过 Next.js rewrites 将 `/api/*` 代理到后端 `http://127.0.0.1:8000`。

## LangGraph 工作流（7 节点）

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
- **evaluate_translation** — LLM 多维度评分 + 规则引擎 fallback
- **reflect_on_evaluation** — LLM 自我复核，内部修正误判、评分不一致
- **terminology_check** — 术语命中 + 语法解析 + 词汇卡生成
- **synthesize_feedback** — 整合为 Markdown 评估报告
- **plan_next_steps** — 错题记录 + 间隔复习 + LLM 推荐下一步训练

## 五维 RPG 能力体系

借鉴《死亡搁浅》五维评价体系，25 阶称号成长路径。

| 维度 key | 中文标签 | 对标 |
|---|---|---|
| accuracy | 语义传达 | 核心意思完整准确 |
| fluency | 表达自然 | 目标语自然流畅 |
| terminology | 术语精准 | 关键词/术语准确 |
| grammar | 结构正确 | 语法/句法正确 |
| strategy | 策略运用 | 语域/风格/文化转换 |

### 等级进阶（XP 制）

每维 300 XP 一级，维度全满才能解锁下一 CEFR 等级：

| 等级 | XP 范围 | 称号 (Lv.1-5) |
|---|---|---|
| A1 | 0-300 | 萌新译者 → 突破译者 |
| A2 | 300-600 | 入门译者 → 精进译者 |
| B1 | 600-900 | 进阶译者 → 卓越译者 |
| B2 | 900-1200 | 高阶译者 → 大师译者 |
| C1 | 1200-1500 | 专家译者 → 宗师译者 |

关键逻辑在 `lingua_agent/tools/learning.py`：
- `compute_ability_rank(ability_xp)` — 从 XP 计算等级/称号/瓶颈
- `compute_ability_stats(ability_xp, progress_history)` — 整合趋势统计

## API 端点

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/run` | 通用 Agent 调用（兼容旧版） |
| POST | `/api/session/init` | 创建学习会话 |
| GET | `/api/session/{id}` | 获取会话状态 |
| POST | `/api/diagnosis/start` | 生成 5 道诊断题 |
| POST | `/api/diagnosis/submit` | 提交诊断答案，估算 CEFR 水平 |
| POST | `/api/practice/generate` | 生成翻译练习 |
| POST | `/api/practice/evaluate` | 评估译文，累加 ability_xp |
| GET | `/api/review/dashboard` | 复习仪表盘 + ability_stats |
| GET | `/api/review/mistakes` | 错题列表（支持筛选） |
| POST | `/api/review/drill` | 生成弱项专练 |
| POST | `/api/review/vocabulary/rate` | SRS 词汇评分 |

## 运行测试

```bash
pytest tests/ -v
```

## CLI 测试

```bash
# 生成一题中译俄
python main.py --pair zh_ru --level B1 --domain general --task generate_exercise

# 评估一条学生译文
python main.py --pair zh_ru --level B1 --source "智能体可以辅助翻译教学。" --translation "Интеллектуальный агент может помогать обучение переводу."
```

## License

MIT
