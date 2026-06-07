# SandCoder 代码评审问题清单

**评审日期**: 2026-06-07
**总体评分**: 7/10（良好偏上）

---

## 严重 — 安全相关

### 1. `install_package` 以 root 身份运行
- **文件**: `app/sandbox/executor.py:80`
- **问题**: `docker exec --user root pip install` 以 root 权限安装包，绕过了沙箱的非 root 用户隔离
- **修复**: 改为 `--user sandbox` + `pip install --user`

### 2. 无任何认证机制
- **文件**: `app/main.py`
- **问题**: API 完全开放，无速率限制，可被恶意利用消耗资源
- **修复**: 添加 API Key 中间件 + 速率限制

### 3. `package_name` 未经验证
- **文件**: `app/sandbox/executor.py:76-83`
- **问题**: 包名直传 subprocess，未做格式校验
- **修复**: 添加正则校验 `^[a-zA-Z0-9_.-]+$`

---

## 中等 — 质量/可靠性

### 4. 测试覆盖不平衡
- **文件**: `tests/`
- **问题**: 15 个测试全部覆盖会话命名，核心流程（聊天、Agent、沙箱、WebSocket）零测试
- **修复**: 补充核心流程集成测试

### 5. Docker 交互方式不一致
- **文件**: `app/sandbox/manager.py` vs `app/sandbox/executor.py`
- **问题**: manager.py 用 Docker SDK，executor.py 用 subprocess，双轨制
- **修复**: 统一用 Docker SDK

### 6. System Prompt 未告知沙箱限制
- **文件**: `app/agent/agent.py:11-25`
- **问题**: 未说明无网络、pip 才可安装包等约束，Agent 可能做无效尝试
- **修复**: 在 SYSTEM_PROMPT 中补充沙箱能力边界

### 7. 会话历史无分页
- **文件**: `app/db/repository.py:get_messages()`
- **问题**: 返回全部消息，长对话消耗内存和 token
- **修复**: 添加 limit/offset 参数或最近 N 条限制

---

## 轻微 — 细节优化

### 8. `load_dotenv()` 在模块顶层执行
- **文件**: `app/main.py:8`
- **问题**: 其他模块可能先于 main.py 导入，导致环境变量缺失
- **修复**: 测试中也加载 .env，保持一致性

### 9. `DB_PATH` 依赖工作目录
- **文件**: `app/db/database.py:4`
- **问题**: 强制从项目根目录启动，不够灵活
- **修复**: 支持 `SANDCODER_DB_PATH` 环境变量覆盖

### 10. 缺 `.dockerignore`
- **文件**: 项目根目录
- **问题**: Docker 构建上下文包含 .venv/、sessions/、.git/ 等无用文件
- **修复**: 创建 `.dockerignore`

### 11. 前端无超时处理
- **文件**: `app/templates/chat.html:sendMessage()`
- **问题**: fetch 无超时设置，网络中断时体验差
- **修复**: 添加 AbortController + 30s 超时

### 12. `RenameRequest` 无长度校验
- **文件**: `app/routes/session.py:40-41`
- **问题**: name 字段无 min_length/max_length，可提交 10KB 超长名称
- **修复**: 添加 Field(min_length=1, max_length=200)

---

## 改进优先级

| # | 条目 | 工作量 | 价值 |
|---|------|--------|------|
| 1 | 修复 pip install root 执行 | 5 min | 🔴 安全 |
| 2 | 补充核心流程集成测试 | 2 h | 🟡 质量 |
| 3 | 统一用 Docker SDK | 1 h | 🟡 一致性 |
| 4 | 前端 fetch 加超时 | 15 min | 🟢 体验 |
| 5 | 创建 .dockerignore | 5 min | 🟢 效率 |
| 6 | RenameRequest 加长度限制 | 2 min | 🟢 健壮 |
| 7 | System Prompt 补充沙箱限制 | 5 min | 🟢 效率 |
| 8 | DB_PATH 支持环境变量 | 10 min | 🟢 可移植 |
| 9 | 添加认证中间件 | 30 min | 🟡 安全 |
| 10 | 会话历史分页 | 20 min | 🟢 可扩展 |
| 11 | 包名校验 | 2 min | 🟡 安全 |
| 12 | load_dotenv 测试一致性 | 5 min | 🟢 健壮 |
