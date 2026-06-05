from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from app.db.repository import get_session, add_message, touch_session
from app.sandbox.manager import create_container, get_container
from app.db.repository import update_container
from app.agent.agent import run_agent

router = APIRouter()


class ChatResponse(BaseModel):
    session_id: str
    reply: str


@router.post("/sessions/{session_id}/chat", response_model=ChatResponse)
async def send_message(
    session_id: str,
    prompt: str = Form(...),
    file: UploadFile | None = File(None),
):
    session = get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    # Ensure container exists
    if session.container_id is None or get_container(session.container_id) is None:
        container_id = create_container(session_id)
        update_container(session_id, container_id)
        session.container_id = container_id

    # Save uploaded file to sandbox workspace
    file_info = ""
    if file and session.container_id:
        from app.sandbox.executor import write_file
        content = await file.read()
        text = content.decode("utf-8", errors="replace")
        write_file(session.container_id, file.filename, text)
        file_info = f"\n\n[Uploaded file: {file.filename} is available in the workspace]"

    # Save user message
    add_message(session_id, "user", prompt + file_info)

    # Run agent
    full_prompt = prompt + file_info
    reply = await run_agent(session.container_id, full_prompt)

    # Save assistant message
    add_message(session_id, "assistant", reply)
    touch_session(session_id)

    return ChatResponse(session_id=session_id, reply=reply)
