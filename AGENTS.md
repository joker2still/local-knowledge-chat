# AGENTS.md

本文件为本仓库内的自动化 agent / coding assistant 提供项目规则。除非用户明确要求，优先遵守这里的约定，并尽量保持改动范围小。

## Project Context

- 项目名称：Local Knowledge Chat。
- 项目类型：本地 RAG 应用。
- 后端：FastAPI，入口为 `backend/app/main.py`。
- 前端：React + TypeScript + Vite，入口在 `frontend/src`。
- 向量库：Qdrant local mode，默认路径 `backend/data/qdrant`。
- 模型服务：Ollama，默认地址 `http://localhost:11434`。
- 当前文档上传支持 `.txt` 与 `.pdf`。

## Development Rules

- 不要无关重构，不要重排大段代码，不要修改与任务无关的 README、配置或锁文件。
- 保持现有分层：API 路由放在 `backend/app/api`，请求/响应模型放在 `backend/app/schemas`，业务逻辑放在 `backend/app/services`，配置和通用异常放在 `backend/app/core`。
- 后端错误应使用 `AppError` 或现有异常体系，让 `main.py` 中的异常处理器统一返回结构化错误。
- RAG 回答必须基于检索上下文；上下文不足时应明确表示不知道或需要先上传文档。
- 文档入库 payload 至少保留 `source`、`chunk_id`、`text`、`page_number`、`file_type`，避免破坏前端来源展示。
- 不要把用户上传文件、Qdrant 数据、模型缓存或环境密钥提交到仓库。
- 新增环境变量时，同步更新 `backend/.env.example`，并提供安全默认值。

## Commands

后端：

```bash
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload
```

前端：

```bash
cd frontend
npm install
npm run dev
```

Ollama：

```bash
ollama serve
ollama pull qwen2.5
ollama pull nomic-embed-text
```

常用检查：

```bash
curl http://127.0.0.1:8000/health
curl -X POST "http://127.0.0.1:8000/upload" -F "file=@sample.txt"
curl -X POST "http://127.0.0.1:8000/chat" -H "Content-Type: application/json" -d "{\"prompt\":\"What does the document say?\"}"
```

## Frontend Notes

- 前端默认开发地址是 `http://127.0.0.1:5173`；如果 Vite 只监听 IPv6，可尝试 `http://[::1]:5173/`。
- API 调用应保持与后端路径一致：`/health`、`/upload`、`/chat`。
- 变更 UI 时保持当前应用风格，优先做可用的工作界面，不新增无关营销页。

## Verification

- 后端变更至少验证导入、启动或相关 API。
- RAG 相关变更应覆盖上传、分块、embedding、检索、回答来源字段。
- 前端变更应运行构建或在浏览器中手动验证主要流程。
