# SandCoder — 需求分析文档

## 项目背景

公司面试题，选题：**Web Coding Agent（基于 Sandbox）**

开卷考试，可使用 AI Coding 软件、搜索引擎等工具。

## 题目原文要求

### 核心要求
1. 用 Python 实现一个 Web 应用 + Sandbox 的 Web Coding Agent
2. 推荐使用 DeepSeek API
3. Agent 框架推荐 Pydantic AI
4. 需要上网查找合适的 sandbox 方案

### Sandbox 能力要求
- 包含 Python 环境
- 提供命令行，供 Agent 调试代码
- 支持 Agent 读写沙箱内的文件

### Web 交互功能
- 用户每次可以发送 Prompt + 文件（例如：让 AI 用 Python 处理 CSV 数据）
- Agent 可以自主多次调用工具来尝试解决问题，最后给出回答

### 会话管理
- 支持单会话内的多轮对话
- 支持历史会话切换

### 典型场景
用户让 AI 用 Python 帮自己处理 CSV 数据

## 提交要求
- 使用 Git 仓库完成工作，会审查工作风格和效率
- 需要提供：代码结果 + 效果演示 + 与 AI 沟通的作答过程

## 用户当前环境

| 项目 | 状态 |
|------|------|
| 操作系统 | Windows 11 Home China |
| Docker | 未安装 |
| Python | 已安装 |
| DeepSeek API Key | 有 |
| 项目路径 | E:\java\SandCoder\ |

## 待决策事项

1. **沙箱方案**：Docker vs 虚拟机 vs 其他方案（待用户了解后决定）
2. **前端框架**：Streamlit vs Gradio（后续确定）
