# SandCoder — Web Coding Agent

A web-based coding agent that autonomously writes and executes Python code in isolated Docker sandboxes. Users chat with an AI that can read/write files, install packages, and debug code — all within a secure container.

## Architecture

```
Browser (HTML/JS)
  |  HTTP + WebSocket
  v
FastAPI
  |-> POST /api/sessions             Session CRUD
  |-> POST /api/sessions/{id}/chat   Chat + file upload
  |-> WS  /api/sessions/{id}/ws      Real-time execution logs
  |
  v
Pydantic AI Agent (DeepSeek)
  |-> execute_code()     docker exec python
  |-> read_file()        docker exec cat
  |-> write_file()       docker exec tee
  |-> install_package()  docker exec pip install
  |
  v
Docker Sandbox (per session)
  - Network disabled
  - Memory 256MB / CPU 1 core
  - Non-root user
  - 30s execution timeout
```

## Features

- **Multi-turn chat** — Conversational coding with context history
- **File upload** — Upload CSV, JSON, or any file for the agent to process
- **Autonomous debugging** — Agent iterates on errors, no human intervention needed
- **Session isolation** — Each session gets its own Docker container with independent workspace
- **Live execution logs** — WebSocket streaming shows what the agent is doing in real time
- **Session management** — Create, switch, and delete sessions with persistent history

## Tech Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| AI Model | DeepSeek API | Cost-effective, strong code generation |
| Agent Framework | Pydantic AI | Type-safe tool definitions, async-native |
| Backend | FastAPI | High performance, native async, WebSocket support |
| Sandbox | Docker | Industry-standard isolation, resource limits |
| Storage | SQLite | Zero-config, embedded, sufficient for session history |
| Frontend | Vanilla HTML/CSS/JS | No framework overhead, fast to iterate |

## Project Structure

```
SandCoder/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── routes/
│   │   ├── session.py       # Session CRUD endpoints
│   │   ├── chat.py          # Chat endpoint with file upload
│   │   └── ws.py            # WebSocket for live logs
│   ├── agent/
│   │   ├── agent.py         # Pydantic AI agent (DeepSeek)
│   │   └── tools.py         # Sandbox tool wrappers
│   ├── sandbox/
│   │   ├── manager.py       # Docker container lifecycle
│   │   └── executor.py      # Code execution with timeout
│   ├── db/
│   │   ├── database.py      # SQLite connection
│   │   ├── models.py        # Session & Message dataclasses
│   │   └── repository.py    # CRUD operations
│   ├── templates/
│   │   └── chat.html        # Chat interface
│   └── static/
│       └── style.css         # Dark theme styles
├── Dockerfile.sandbox        # Sandbox image (Python 3.12 + numpy/pandas/matplotlib/scipy)
├── requirements.txt
└── sessions/                 # Per-session workspace directories (runtime)
```

## Quick Start

### Prerequisites

- Python 3.12+
- Docker Desktop
- DeepSeek API key ([Get one here](https://platform.deepseek.com/api_keys))

### Setup

```bash
# Clone the repository
git clone <repo-url>
cd SandCoder

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Build the sandbox Docker image
docker build -f Dockerfile.sandbox -t sandcoder-sandbox:latest .

# Set your API key
export DEEPSEEK_API_KEY=sk-your-key-here  # Windows: set DEEPSEEK_API_KEY=sk-your-key-here

# Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000` in your browser.

### Using .env file (alternative)

```bash
cp .env.example .env
# Edit .env with your actual API key
```

## API Reference

### Sessions

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/sessions` | Create a new session |
| `GET` | `/api/sessions` | List all sessions |
| `GET` | `/api/sessions/{id}` | Get session detail with message history |
| `DELETE` | `/api/sessions/{id}` | Delete session and destroy container |

### Chat

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/sessions/{id}/chat` | Send message (multipart: `prompt` + optional `file`) |

### WebSocket

| Endpoint | Description |
|----------|-------------|
| `ws://localhost:8000/api/sessions/{id}/ws` | Live execution log streaming |

### Example Usage

```bash
# Create a session
curl -X POST http://localhost:8000/api/sessions

# Chat with the agent
curl -X POST http://localhost:8000/api/sessions/{session_id}/chat \
  -F "prompt=Write a function that checks if a number is prime, then test it with 17"

# Upload a CSV and analyze it
curl -X POST http://localhost:8000/api/sessions/{session_id}/chat \
  -F "prompt=Calculate the average score from the CSV" \
  -F "file=@data.csv"

# List all sessions
curl http://localhost:8000/api/sessions
```

## Security

- **Network isolation**: Containers run with `--network none`, no external access
- **Resource limits**: 256MB memory, 1 CPU core per container
- **Non-root execution**: All code runs as unprivileged `sandbox` user
- **Execution timeout**: Code killed after 30 seconds
- **Path traversal prevention**: File read/write restricted to workspace directory
- **Auto-cleanup**: Containers removed on session deletion; 30-minute idle timeout

## Design Decisions

- **Per-session containers** over shared containers — stronger isolation, no cross-session state leaks
- **Vanilla frontend** over React/Vue — zero build step, faster iteration, interviewer can read the full frontend in one file
- **SQLite** over PostgreSQL — no external database dependency, single binary to deploy
- **Docker SDK** over subprocess — typed API, better error handling, cleaner container lifecycle management
- **DeepSeek** over OpenAI — comparable code generation quality at significantly lower cost
