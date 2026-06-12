# Railway 部署清单

## 部署文件

Railway 部署只需要以下文件，其他不需要上传：

```
linguagraph_agent/
├── prompts.py              ← prompt 模板
├── llm.py                  ← LLM 客户端
├── config.py               ← 语言对配置加载
├── resources.py            ← 术语库检索
├── tools/
│   ├── __init__.py
│   ├── learning.py         ← 规则引擎 + RPG 系统
│   └── exercise_generation.py  ← 出题蓝图 + 选题
skill_api.py                ← Skill API 入口（4 端点）
requirements.txt            ← 依赖
configs/
└── language_pairs/
    ├── zh_ru.yaml
    └── ru_zh.yaml
resources/
└── terminology/
    └── zh_ru/
        └── general.csv
```

不需要的文件（Railway 不部署）：
- web_app.py、main.py、run_web.py（旧版应用）
- nodes.py、graph.py、state.py（LangGraph 工作流）
- frontend/（Next.js 前端）
- tests/、md/、.sessions/

## 环境变量（Railway 里配）

| 变量名 | 值 | 必填 |
|---|---|---|
| OPENAI_API_KEY | 你的 DeepSeek API Key | ✅ |
| OPENAI_BASE_URL | https://api.deepseek.com | ✅ |
| LINGUAGRAPH_MODEL | deepseek-chat | 否 |

## 启动命令

```
python -m uvicorn skill_api:app --host 0.0.0.0 --port $PORT
```

## Railway 操作步骤

1. 把 `plan-b` 分支 push 到 GitHub
2. 打开 railway.app → New Project → Deploy from GitHub repo
3. 选 linguagraph_agent 仓库 → 选 plan-b 分支
4. Settings → Variables → 添加上面的环境变量
5. Settings → Build & Deploy → Start Command 填上面的命令
6. Deploy → 等 2 分钟 → 拿到域名类似 `linguagraph.up.railway.app`

## 部署后验证

```bash
# 健康检查
curl https://你的域名/api/skill/health

# 测评估
curl -X POST https://你的域名/api/skill/evaluate \
  -H "Content-Type: application/json" \
  -d '{"source_text":"你好","user_translation":"Привет","language_pair":"zh_ru","user_level":"A1"}'

# 测出题
curl -X POST https://你的域名/api/skill/generate \
  -H "Content-Type: application/json" \
  -d '{"language_pair":"zh_ru","user_level":"B1"}'

# 测等级
curl -X POST https://你的域名/api/skill/rank \
  -H "Content-Type: application/json" \
  -d '{"accuracy":150,"fluency":200,"terminology":100,"grammar":80,"strategy":180}'
```

## 后续修改

代码改了之后：
```bash
git add -A
git commit -m "你的改动说明"
git push origin plan-b
```
Railway 会自动重新部署。

## 域名更换

拿到 Railway 域名后，Coze 四个工作流的 HTTP 节点 URL 替换为：
- `https://你的域名/api/skill/evaluate`
- `https://你的域名/api/skill/generate`
- `https://你的域名/api/skill/rank`
- `https://你的域名/api/skill/terminology`
