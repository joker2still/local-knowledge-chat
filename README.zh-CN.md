# 本地知识库聊天系统（Local Knowledge Chat）

## 1. 项目概述
本项目是一个最小可用的本地 RAG（检索增强生成）示例。
你可以上传 `.txt` 文档，系统会将文本切分并向量化后存入本地 Qdrant，再通过检索相关片段结合大模型生成答案。

## 2. 功能特性
- FastAPI 后端，按服务分层组织
- React + TypeScript + Vite 前端
- 支持 `.txt` 文档上传与分块
- 通过 Ollama 本地生成 embedding 与回答
- 使用 Qdrant 本地模式做向量检索
- 聊天结果返回答案与来源片段
- 已配置前后端开发环境 CORS

## 3. 技术栈
- 后端：FastAPI、Pydantic、Requests
- 向量库：Qdrant（`qdrant-client` 本地模式）
- 模型服务：Ollama
- 前端：React、TypeScript、Vite

## 4. 项目结构
```text
local-knowledge-chat/
  backend/
    app/
      main.py
      api/
        chat.py
        documents.py
      core/
        config.py
        logging_config.py
        exceptions.py
      schemas/
        chat.py
        documents.py
      services/
        llm_service.py
        embedding_service.py
        document_service.py
        vector_store.py
        rag_service.py
    data/
      raw/
      qdrant/
    .env.example
    requirements.txt
  frontend/
    src/
      App.tsx
      services/
        api.ts
      types.ts
    package.json
```

## 5. 后端启动
1. 创建并激活 Python 虚拟环境。
2. 安装依赖：
```bash
pip install -r backend/requirements.txt
```
3. （可选）根据 `backend/.env.example` 创建 `.env` 并调整配置。
4. 启动后端：
```bash
uvicorn backend.app.main:app --reload
```
默认地址：`http://127.0.0.1:8000`

## 6. 前端启动
1. 安装依赖：
```bash
cd frontend
npm install
```
2. 启动开发服务器：
```bash
npm run dev
```
默认地址：`http://127.0.0.1:5173`

## 7. 如何运行 Ollama
1. 启动 Ollama 服务：
```bash
ollama serve
```
2. 拉取所需模型：
```bash
ollama pull qwen2.5
ollama pull nomic-embed-text
```
3. 确认服务可访问：`http://localhost:11434`

## 8. 如何测试上传与聊天
1. 启动 Ollama、后端、前端。
2. 在前端上传 `.txt` 文件。
3. 在聊天框输入问题并发送。
4. 检查是否返回答案与来源片段。

## 9. API 使用示例
### 健康检查
```bash
curl http://127.0.0.1:8000/health
```

### 上传文档
```bash
curl -X POST "http://127.0.0.1:8000/upload" \
  -F "file=@sample.txt"
```

### 聊天问答
```bash
curl -X POST "http://127.0.0.1:8000/chat" \
  -H "Content-Type: application/json" \
  -d "{\"prompt\":\"文档中关于 FastAPI 是怎么说的？\"}"
```

示例响应：
```json
{
  "answer": "...",
  "sources": [
    {
      "source": "sample.txt",
      "chunk_id": "...",
      "score": 0.72,
      "preview": "..."
    }
  ]
}
```

## 10. 后续可改进方向
- 增加服务层与 API 层自动化测试
- 增强文件校验与安全检查
- 支持 PDF / Markdown 等更多文档格式
- 增加过滤检索与混合检索能力
- 提供 Docker Compose 一键本地启动
- 支持多轮对话上下文管理
