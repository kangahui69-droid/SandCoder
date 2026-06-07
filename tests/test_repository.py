"""Tests for database repository layer — pagination and data access."""

from app.db.repository import create_session, add_message, get_messages, get_session


class TestRepository:
    def test_get_messages_returns_most_recent(self):
        session = create_session()

        # Insert 60 messages alternating user/assistant
        for i in range(60):
            role = "user" if i % 2 == 0 else "assistant"
            add_message(session.session_id, role, f"Message {i}")

        messages = get_messages(session.session_id, limit=50)

        # Should return exactly 50 messages
        assert len(messages) == 50

        # Should be the most recent 50: messages 10–59 in chronological order
        assert messages[0].content == "Message 10"
        assert messages[49].content == "Message 59"

    def test_get_messages_default_limit(self):
        session = create_session()

        for i in range(3):
            add_message(session.session_id, "user", f"Msg {i}")

        messages = get_messages(session.session_id)
        assert len(messages) == 3
        assert messages[0].content == "Msg 0"
        assert messages[2].content == "Msg 2"
