# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

SandCoder — Web Coding Agent，面试项目。用户通过 Web 界面发送 Prompt + 文件，Agent（Pydantic AI + DeepSeek API）在 Docker 沙箱中自主执行代码、读写文件，返回结果。

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

## 设计文档

完整设计见 docs/design.md，需求见 docs/requirements.md。
