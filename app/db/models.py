from dataclasses import dataclass
from typing import Optional


@dataclass
class Session:
    session_id: str
    container_id: Optional[str] = None
    name: str = "New Session"
    created_at: Optional[str] = None
    last_active: Optional[str] = None
    status: str = "active"


@dataclass
class Message:
    session_id: str
    role: str
    content: str
    type: str = "text"
    id: Optional[int] = None
    created_at: Optional[str] = None
