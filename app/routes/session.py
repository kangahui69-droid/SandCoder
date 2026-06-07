import logging
import pathlib
import shutil

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.db.repository import (
    create_session, list_sessions, get_session,
    delete_session, get_messages, update_session_name,
)
from app.db.models import Session

logger = logging.getLogger(__name__)

router = APIRouter()


class SessionResponse(BaseModel):
    session_id: str
    container_id: str | None = None
    name: str = "New Session"
    created_at: str | None = None
    last_active: str | None = None
    status: str = "active"


class MessageResponse(BaseModel):
    id: int | None = None
    role: str
    content: str
    type: str = "text"
    created_at: str | None = None


class SessionDetailResponse(BaseModel):
    session: SessionResponse
    messages: list[MessageResponse]


class RenameRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)


@router.post("/sessions", response_model=SessionResponse, status_code=201)
def create_new_session():
    session = create_session()
    return SessionResponse(**session.__dict__)


@router.get("/sessions", response_model=list[SessionResponse])
def list_all_sessions():
    sessions = list_sessions()
    return [SessionResponse(**s.__dict__) for s in sessions]


@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
def get_session_detail(session_id: str):
    session = get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    messages = get_messages(session_id)
    return SessionDetailResponse(
        session=SessionResponse(**session.__dict__),
        messages=[
            MessageResponse(
                id=m.id,
                role=m.role,
                content=m.content,
                type=m.type,
                created_at=m.created_at,
            )
            for m in messages
        ],
    )


@router.patch("/sessions/{session_id}", response_model=SessionResponse)
def rename_session(session_id: str, body: RenameRequest):
    session = get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    update_session_name(session_id, body.name)
    session.name = body.name
    return SessionResponse(**session.__dict__)


@router.delete("/sessions/{session_id}", status_code=204)
def remove_session(session_id: str):
    from app.sandbox.manager import stop_container
    session = get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.container_id:
        stop_container(session.container_id)
    delete_session(session_id)

    # Clean up workspace directory
    workspace = pathlib.Path(__file__).parents[2] / "sessions" / session_id
    if workspace.exists():
        try:
            shutil.rmtree(workspace)
            logger.info("Removed workspace: %s", workspace)
        except OSError as e:
            logger.warning("Failed to remove workspace %s: %s", workspace, e)
