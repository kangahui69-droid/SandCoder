# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

SandCoder — Web Coding Agent，面试项目。用户通过 Web 界面发送 Prompt + 文件，Agent（Pydantic AI + DeepSeek API）在 Docker 沙箱中自主执行代码、读写文件，返回结果。

## 常用命令

```bash
# 安装依赖
.venv/Scripts/pip install -r requirements.txt

# 启动服务（必须先设置 DEEPSEEK_API_KEY）
.venv/Scripts/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# 构建沙箱 Docker 镜像（启动时会自动构建，也可手动执行）
docker build -f Dockerfile.sandbox -t sandcoder-sandbox:latest .

# 运行全部测试
.venv/Scripts/python -m pytest tests/ -v

# 运行单个测试文件
.venv/Scripts/python -m pytest tests/test_session_naming.py -v

# 运行单个测试类
.venv/Scripts/python -m pytest tests/test_session_naming.py::TestSessionNaming -v
```

所有命令必须在项目根目录 `E:\java\SandCoder\` 下执行。

## 环境配置

- API Key 通过 `.env` 文件设置（`DEEPSEEK_API_KEY=sk-xxx`），启动时 `load_dotenv()` 自动加载
- `.env` 已在 `.gitignore` 中，不会提交到 GitHub
- Docker Desktop 必须运行，沙箱容器依赖它
- **`starlette<1.0.0`** — FastAPI 0.115.6 不兼容 Starlette 1.x（移除了 `on_startup` 参数）

## 技术栈

- **AI**: DeepSeek API + Pydantic AI Agent 框架
- **后端**: FastAPI
- **前端**: 原生 HTML/JS（Jinja2 模板），不引入前端框架
- **存储**: SQLite（sessions 表 + messages 表）
- **沙箱**: Docker，每会话一个容器

## 架构

```
浏览器 (HTML/JS)
  ↓ HTTP + WebSocket
FastAPI (routes/)
  ↓
Pydantic AI Agent (agent/)
  ├─ execute_code → sandbox/executor.py → docker exec
  ├─ read_file   → docker exec cat
  ├─ write_file  → docker exec 写入
  └─ install_pkg → docker exec pip install
  ↓ ↙
DeepSeek API  +  Docker 沙箱  +  SQLite
```

分层目录见 docs/design.md。

## 启动流程

`app/main.py` lifespan 按顺序执行：
1. `load_dotenv()` — 加载 `.env`
2. `init_db()` — 创建 SQLite 表 + 迁移
3. `_startup_checks()` — 检查 Docker 可用性 + API Key 是否设置（warning 不阻塞）
4. `build_image()` — 构建沙箱 Docker 镜像（缓存命中则秒过）
5. `init_executor()` — 初始化 ThreadPoolExecutor（4 workers）
6. yield → 服务就绪
7. Shutdown: 停止所有容器 → 关闭 executor

Agent 是惰性初始化的 — 首次聊天请求时才创建 Pydantic AI Agent 实例。

## API 路由

```
POST   /api/sessions              # 创建会话
GET    /api/sessions              # 会话列表
GET    /api/sessions/{id}         # 会话详情（含历史消息）
DELETE /api/sessions/{id}         # 删除会话
POST   /api/sessions/{id}/chat    # 发送消息（含可选文件上传）
WS     /api/sessions/{id}/ws      # 实时推送执行日志
```

## 沙箱

- 镜像: `python:3.12-slim` + numpy/pandas/matplotlib/scipy
- 运行时: `--network none --memory 256m --cpus 1`，非 root 用户
- 代码执行超时 30s，会话空闲 30 分钟自动销毁容器
- 每个会话一个独立容器，workspace 挂载到 `sessions/{session_id}/`

## 关键实现细节

- **ContextVar 隔离**: `tools.py` 用 `ContextVar` 存储当前 container_id，保证并发请求互不干扰
- **同步 Docker SDK**: executor 操作通过 `ThreadPoolExecutor` 在异步上下文中以线程方式运行
- **文件安全**: `executor.py` 的 `_safe_path()` 拒绝绝对路径和路径遍历，所有文件操作限制在 `/home/sandbox/workspace/`
- **会话自动命名**: 首条用户消息触发，截取前 40 字符（按词边界）；已手动改名则跳过
- **DB_PATH**: `database.py` 中 `os.path.dirname` 三次回到项目根目录，必须从项目根目录启动

## 设计文档

完整设计见 docs/design.md，需求见 docs/requirements.md。
