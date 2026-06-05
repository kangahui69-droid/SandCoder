import uuid
from datetime import datetime, UTC
from typing import Optional
from .database import get_connection
from .models import Session, Message


def create_session() -> Session:
    session_id = str(uuid.uuid4())
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO sessions (session_id, name) VALUES (?, ?)",
            (session_id, "New Session"),
        )
    return Session(session_id=session_id, name="New Session")


def get_session(session_id: str) -> Optional[Session]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
        ).fetchone()
    if row is None:
        return None
    return Session(**dict(row))


def list_sessions() -> list[Session]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM sessions ORDER BY last_active DESC"
        ).fetchall()
    return [Session(**dict(r)) for r in rows]


def delete_session(session_id: str):
    with get_connection() as conn:
        conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))


def update_container(session_id: str, container_id: str):
    with get_connection() as conn:
        conn.execute(
            "UPDATE sessions SET container_id = ?, last_active = ? WHERE session_id = ?",
            (container_id, datetime.now(UTC).isoformat(), session_id),
        )


def update_session_name(session_id: str, name: str):
    """Update the display name of a session."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE sessions SET name = ? WHERE session_id = ?",
            (name, session_id),
        )


def touch_session(session_id: str):
    with get_connection() as conn:
        conn.execute(
            "UPDATE sessions SET last_active = ? WHERE session_id = ?",
            (datetime.now(UTC).isoformat(), session_id),
        )


def add_message(session_id: str, role: str, content: str, msg_type: str = "text") -> Message:
    with get_connection() as conn:
        conn.execute("BEGIN")
        cursor = conn.execute(
            "INSERT INTO messages (session_id, role, content, type) VALUES (?, ?, ?, ?)",
            (session_id, role, content, msg_type),
        )
        msg_id = cursor.lastrowid
        conn.execute(
            "UPDATE sessions SET last_active = ? WHERE session_id = ?",
            (datetime.now(UTC).isoformat(), session_id),
        )
        # Auto-name from first user message
        if role == "user" and content.strip():
            row = conn.execute(
                "SELECT name FROM sessions WHERE session_id = ?", (session_id,)
            ).fetchone()
            if row and row["name"] == "New Session":
                name = content.strip()[:40]
                conn.execute(
                    "UPDATE sessions SET name = ? WHERE session_id = ?",
                    (name, session_id),
                )
    return Message(
        id=msg_id,
        session_id=session_id,
        role=role,
        content=content,
        type=msg_type,
    )


def get_messages(session_id: str) -> list[Message]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM messages WHERE session_id = ? ORDER BY created_at ASC",
            (session_id,),
        ).fetchall()
    return [Message(**dict(r)) for r in rows]
