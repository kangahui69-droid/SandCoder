import asyncio
import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from app.db.database import init_db
from app.db.repository import list_sessions
from app.routes.session import router as session_router
from app.routes.chat import router as chat_router
from app.routes.ws import router as ws_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting SandCoder...")
    init_db()
    logger.info("Database initialized")

    # Pre-flight checks
    _startup_checks()

    # Ensure sandbox Docker image exists
    from app.sandbox.manager import build_image
    try:
        build_image()
    except Exception:
        logger.warning("Failed to build sandbox image — containers will fail to start")

    # Initialize thread pool executor
    from app.agent.tools import init_executor
    init_executor()

    # Start idle container cleanup background task
    from app.sandbox.manager import cleanup_idle_containers, CLEANUP_INTERVAL

    cleanup_task: asyncio.Task | None = None

    async def _cleanup_loop():
        while True:
            await asyncio.sleep(CLEANUP_INTERVAL)
            try:
                await asyncio.to_thread(cleanup_idle_containers)
            except Exception:
                logger.warning("Idle cleanup iteration failed", exc_info=True)

    cleanup_task = asyncio.create_task(_cleanup_loop())

    logger.info("SandCoder ready")
    yield
    # Shutdown: cancel cleanup task, stop containers, shutdown executor
    logger.info("Shutting down...")
    if cleanup_task:
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass

    from app.agent.tools import shutdown_executor
    from app.sandbox.manager import stop_container
    for s in list_sessions():
        if s.container_id:
            try:
                stop_container(s.container_id)
            except Exception:
                logger.warning("Failed to stop container %s on shutdown", s.container_id)
    shutdown_executor()
    logger.info("Shutdown complete")


def _startup_checks():
    """Warn about missing dependencies without crashing."""
    if not os.environ.get("DEEPSEEK_API_KEY"):
        logger.warning("DEEPSEEK_API_KEY is not set — agent will fail on first chat request")

    try:
        import docker
        docker.from_env().ping()
        logger.info("Docker is available")
    except Exception:
        logger.warning("Docker is not available — sandbox containers cannot be created")


app = FastAPI(title="SandCoder", version="0.1.0", lifespan=lifespan)

SANCODER_API_KEY = os.environ.get("SANCODER_API_KEY") or os.environ.get("DEEPSEEK_API_KEY", "")


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if not request.url.path.startswith("/api/") or "/ws" in request.url.path:
        return await call_next(request)
    if not SANCODER_API_KEY:
        return await call_next(request)
    client_key = request.headers.get("X-API-Key", "")
    if client_key != SANCODER_API_KEY:
        return JSONResponse(status_code=401, content={"detail": "Invalid or missing API key"})
    return await call_next(request)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(session_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(ws_router, prefix="/api")

# Static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
async def root():
    templates_dir = os.path.join(os.path.dirname(__file__), "templates")
    chat_html = os.path.join(templates_dir, "chat.html")
    if os.path.isfile(chat_html):
        with open(chat_html, "r", encoding="utf-8") as f:
            content = f.read()
        import json
        key_injection = f'<script>window.SANDCODER_API_KEY = {json.dumps(SANCODER_API_KEY)};</script>'
        content = content.replace("</head>", f"{key_injection}\n</head>", 1)
        return HTMLResponse(content)
    return HTMLResponse(
        "<h1>SandCoder</h1><p>Frontend not built yet. Run Task 11 to create templates.</p>",
        status_code=503,
    )
