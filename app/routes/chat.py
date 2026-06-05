import logging
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, UserPromptPart, TextPart
from app.db.repository import get_session, get_messages, add_message, touch_session, update_container
from app.sandbox.manager import create_container, get_container
from app.agent.agent import run_agent
from app.sandbox.executor import write_file as sandbox_write

logger = logging.getLogger(__name__)

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
    if file and file.filename and session.container_id:
        content = await file.read()
        text = content.decode("utf-8", errors="replace")
        try:
            sandbox_write(session.container_id, file.filename, text)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid filename: {e}")
        file_info = f"\n\n[Uploaded file: {file.filename} is available in the workspace]"

    # Load conversation history before saving current message
    prior_messages = get_messages(session_id)
    history: list[ModelMessage] = []
    for msg in prior_messages:
        if msg.role == "user":
            history.append(ModelRequest(parts=[UserPromptPart(msg.content)]))
        elif msg.role == "assistant":
            history.append(ModelResponse(parts=[TextPart(msg.content)]))

    # Save user message
    add_message(session_id, "user", prompt + file_info)

    # Run agent with conversation history
    full_prompt = prompt + file_info
    reply = await run_agent(session.container_id, full_prompt, session_id, message_history=history)

    # Save assistant message
    add_message(session_id, "assistant", reply)
    touch_session(session_id)

    return ChatResponse(session_id=session_id, reply=reply)
