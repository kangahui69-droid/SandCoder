# SandCoder 设计文档

**日期**: 2026-06-05  
**项目**: SandCoder — Web Coding Agent  
**状态**: 设计完成

---

## 技术栈（已确认）

| 层 | 选型 |
|---|---|
| AI 模型 | DeepSeek API（已有 Key） |
| Agent 框架 | Pydantic AI |
| Web 后端 | FastAPI |
| 沙箱 | Docker（每会话一个容器） |
| 前端 | FastAPI + 原生 HTML/JS |
| 存储 | SQLite（会话 + 消息） |

---

## 项目目录结构（已确认）

```
SandCoder/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 入口 + 路由注册
│   ├── routes/
│   │   ├── chat.py           # /api/sessions/{id}/chat
│   │   ├── session.py        # /api/sessions CRUD
│   │   └── ws.py             # /api/sessions/{id}/ws WebSocket
│   ├── agent/
│   │   ├── agent.py          # Pydantic AI Agent 定义
│   │   └── tools.py          # execute_code / read_file / write_file / install_pkg
│   ├── sandbox/
│   │   ├── manager.py        # Docker 容器生命周期管理
│   │   └── executor.py       # docker exec 执行 + 超时控制
│   ├── db/
│   │   ├── database.py       # SQLite 连接管理
│   │   ├── models.py         # Session / Message 表结构
│   │   └── repository.py     # 增删改查
│   ├── templates/            # Jinja2 模板 (前端页面)
│   └── static/               # CSS / JS
├── sessions/                 # 沙箱工作目录 (运行时)
├── data.db                   # SQLite 数据库文件
├── Dockerfile.sandbox        # 沙箱镜像定义
├── requirements.txt
└── README.md
```

---

## API 路由设计（已确认）

```
POST   /api/sessions              # 创建新会话
GET    /api/sessions              # 获取会话列表
GET    /api/sessions/{id}         # 获取会话详情（含历史消息）
DELETE /api/sessions/{id}         # 删除会话

POST   /api/sessions/{id}/chat    # 发送消息（含可选文件上传）
WS     /api/sessions/{id}/ws      # 实时推送执行日志
```

---

## 会话管理 — SQLite（已确认）

```
data.db                # SQLite，sessions 表 + messages 表
sessions/
├── {session_id}/      # 每个会话的沙箱工作目录
│   └── workspace/
```

- **sessions 表**：session_id, container_id, created_at, last_active, status
- **messages 表**：id, session_id, role, content, type(text/code/file), created_at
- 容器空闲 30 分钟自动销毁，数据库保留历史可回看

---

## 前端（已确认）

**FastAPI + 原生 HTML/JS**

- FastAPI 直接返回 HTML 页面（Jinja2 模板）
- 前端用原生 JS + fetch 调用 API，不引入任何前端框架
- WebSocket 推送 Agent 执行日志（实时展示沙箱中的代码执行过程）
- 核心页面：聊天界面、文件上传、会话列表、代码执行结果展示

---

## Docker 沙箱管理（已确认）

**方案：每会话一个容器**

### 沙箱镜像 — Dockerfile.sandbox

```dockerfile
FROM python:3.12-slim

RUN pip install numpy pandas matplotlib scipy

RUN useradd -m sandbox
USER sandbox
WORKDIR /home/sandbox/workspace
```

### 运行时参数

- `--network none`：断网，防止外连攻击
- `--memory 256m --cpus 1`：限制资源，防止吃光宿主机
- 代码执行超时 30 秒自动 kill
- 非 root 用户运行（纵深防御）

### 生命周期

```
会话创建 → docker run 启动容器
会话期间 → Agent 在该容器中多次执行代码、读写文件
会话结束 → docker stop + docker rm 销毁容器
超时保护 → 会话空闲 30 分钟后自动销毁容器
```

### Agent 工具

1. `execute_code(code)` → docker exec 执行，带超时控制
2. `read_file(path)` → docker exec cat 读取文件
3. `write_file(path, content)` → docker exec 写入文件
4. `install_package(name)` → docker exec pip install 按需安装

---

## 系统架构（已确认）

```
浏览器 (HTML/JS)
  ↓ HTTP + WebSocket
FastAPI (Web 层)
  ├─ /api/sessions            CRUD
  ├─ /api/sessions/{id}/chat  发送消息
  └─ /api/sessions/{id}/ws    WebSocket 实时推送
  ↓ 调用
Pydantic AI Agent (Agent 层)
  ├─ 工具1: execute_code(code) → docker exec 执行
  ├─ 工具2: read_file(path) → docker exec cat
  ├─ 工具3: write_file(path, content) → docker exec 写入
  └─ 工具4: install_package(name) → docker exec pip install
  ↓ ↙
DeepSeek API (推理)  +  Docker 沙箱 (执行)  +  SQLite (存储)
```

**请求流程**:
1. 用户创建会话 → FastAPI 分配 session_id，启动 Docker 容器
2. 用户发送消息 + 文件 → FastAPI 将文件写入容器工作目录
3. Pydantic AI Agent 接管，调用 DeepSeek API 推理
4. Agent 自主调用工具（执行代码、读写文件）在沙箱中调试
5. 结果返回前端，消息存入 SQLite
6. 会话空闲 30 分钟 → 容器销毁，历史保留
