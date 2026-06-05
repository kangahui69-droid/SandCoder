# SandCoder 项目状态（截至 2026-06-05）

## 当前阶段
**设计阶段** — 需求分析完成，技术方案待定（等 Docker 安装后决定）

## 已完成的步骤
- [x] 读取面试题要求
- [x] 项目命名为 SandCoder
- [x] 确定技术栈方向：FastAPI + Pydantic AI + DeepSeek API + Docker 沙箱
- [x] 需求分析文档（见 docs/requirements.md）
- [x] 沙箱方案选型 — 确定用 Docker
- [x] Docker 安装步骤已给出

## 当前卡点
**Docker 未安装** — 用户正在安装 Docker Desktop（WSL2 + Docker Desktop）

## 下一步
Docker 安装完成后：
1. 继续 brainstorming 流程 → 确认技术方案
2. 给出设计文档
3. 开始编码实现

## 关键决策记录
| 决策 | 结果 |
|------|------|
| 项目名称 | SandCoder |
| AI 模型 | DeepSeek API（已有 Key） |
| Agent 框架 | Pydantic AI |
| Web 框架 | FastAPI |
| 沙箱方案 | Docker（面试官预期方案） |
| 前端 | 待定（Streamlit vs Gradio） |

## 项目路径
`E:\java\SandCoder\`

## 面试核心要求速查
1. Web Coding Agent，基于 Sandbox
2. Pydantic AI + DeepSeek API
3. 沙箱：Python 环境 + 命令行 + 文件读写
4. Web：Prompt + 文件上传 + Agent 多轮对话
5. 会话管理：多轮对话 + 历史切换
6. 提交：Git 仓库 + 代码 + 演示 + AI 沟通记录
