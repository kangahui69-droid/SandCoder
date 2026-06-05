import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.db.database import init_db
from app.db.repository import list_sessions
from app.routes.session import router as session_router
from app.routes.chat import router as chat_router
from app.routes.ws import router as ws_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    yield
    # Shutdown: cleanup executor and Docker containers
    from app.agent.tools import shutdown_executor
    from app.sandbox.manager import stop_container
    for s in list_sessions():
        if s.container_id:
            try:
                stop_container(s.container_id)
            except Exception:
                logger.warning("Failed to stop container %s on shutdown", s.container_id)
    shutdown_executor()


app = FastAPI(title="SandCoder", version="0.1.0", lifespan=lifespan)

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
    from fastapi.responses import FileResponse, HTMLResponse
    templates_dir = os.path.join(os.path.dirname(__file__), "templates")
    chat_html = os.path.join(templates_dir, "chat.html")
    if os.path.isfile(chat_html):
        return FileResponse(chat_html)
    return HTMLResponse(
        "<h1>SandCoder</h1><p>Frontend not built yet. Run Task 11 to create templates.</p>",
        status_code=503,
    )
