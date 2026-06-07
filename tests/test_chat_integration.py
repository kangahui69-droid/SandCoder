from unittest.mock import patch, AsyncMock

from pydantic_ai.exceptions import ModelHTTPError, AgentRunError


class TestChatIntegration:
    """Integration tests for chat endpoints (no real agent or Docker)."""

    def test_chat_nonexistent_session_returns_404(self, client):
        response = client.post("/api/sessions/nonexistent/chat", data={"prompt": "test"})
        assert response.status_code == 404

    def test_chat_saves_messages(self, client):
        r = client.post("/api/sessions")
        assert r.status_code == 201
        session_id = r.json()["session_id"]

        with (
            patch("app.routes.chat.run_agent", new=AsyncMock(return_value="Mocked agent response")),
            patch("app.routes.chat.get_container", return_value=None),
            patch("app.routes.chat.create_container", return_value="fake_container_id"),
        ):
            response = client.post(
                f"/api/sessions/{session_id}/chat",
                data={"prompt": "Hello, code!"},
            )

        assert response.status_code == 200
        data = response.json()
        assert "reply" in data
        assert data["reply"] == "Mocked agent response"

        r2 = client.get(f"/api/sessions/{session_id}")
        assert r2.status_code == 200
        detail = r2.json()
        messages = detail["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Hello, code!"
        assert messages[1]["role"] == "assistant"
        assert messages[1]["content"] == "Mocked agent response"

    def test_chat_with_file_upload(self, client):
        r = client.post("/api/sessions")
        assert r.status_code == 201
        session_id = r.json()["session_id"]

        with (
            patch("app.routes.chat.run_agent", new=AsyncMock(return_value="Mocked agent response")),
            patch("app.routes.chat.get_container", return_value=None),
            patch("app.routes.chat.create_container", return_value="fake_container_id"),
            patch("app.routes.chat.sandbox_write", return_value="File written"),
        ):
            response = client.post(
                f"/api/sessions/{session_id}/chat",
                data={"prompt": "Analyze this CSV"},
                files={"file": ("data.csv", b"a,b,c\n1,2,3\n", "text/csv")},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["reply"] == "Mocked agent response"

    def test_chat_handles_rate_limit(self, client):
        r = client.post("/api/sessions")
        session_id = r.json()["session_id"]

        with (
            patch("app.routes.chat.run_agent",
                  new=AsyncMock(side_effect=ModelHTTPError(
                      status_code=429, model_name="deepseek-chat", body="Rate limited"))),
            patch("app.routes.chat.get_container", return_value=None),
            patch("app.routes.chat.create_container", return_value="fake_container_id"),
        ):
            response = client.post(
                f"/api/sessions/{session_id}/chat",
                data={"prompt": "Test rate limit"},
            )

        assert response.status_code == 200
        assert "过于频繁" in response.json()["reply"]

    def test_chat_handles_agent_run_error(self, client):
        r = client.post("/api/sessions")
        session_id = r.json()["session_id"]

        with (
            patch("app.routes.chat.run_agent",
                  new=AsyncMock(side_effect=AgentRunError("agent failure"))),
            patch("app.routes.chat.get_container", return_value=None),
            patch("app.routes.chat.create_container", return_value="fake_container_id"),
        ):
            response = client.post(
                f"/api/sessions/{session_id}/chat",
                data={"prompt": "Test agent error"},
            )

        assert response.status_code == 200
        assert "执行过程中出现错误" in response.json()["reply"]
