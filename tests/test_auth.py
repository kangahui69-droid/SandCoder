"""Tests for auth middleware — API key enforcement and pass-through logic."""

import app.main


class TestAuthMiddleware:
    """Test the X-API-Key auth middleware on HTTP endpoints."""

    def test_api_returns_401_without_key(self, client, monkeypatch):
        monkeypatch.setattr(app.main, "SANCODER_API_KEY", "secret-key")
        r = client.get("/api/sessions")
        assert r.status_code == 401
        assert "Invalid or missing API key" in r.json()["detail"]

    def test_api_passes_with_correct_key(self, client, monkeypatch):
        monkeypatch.setattr(app.main, "SANCODER_API_KEY", "secret-key")
        r = client.get("/api/sessions", headers={"X-API-Key": "secret-key"})
        assert r.status_code == 200

    def test_api_rejects_wrong_key(self, client, monkeypatch):
        monkeypatch.setattr(app.main, "SANCODER_API_KEY", "secret-key")
        r = client.get("/api/sessions", headers={"X-API-Key": "wrong-key"})
        assert r.status_code == 401

    def test_non_api_routes_skip_auth(self, client, monkeypatch):
        monkeypatch.setattr(app.main, "SANCODER_API_KEY", "secret-key")
        r = client.get("/")
        assert r.status_code == 200

    def test_websocket_path_skipped_by_middleware(self, client, monkeypatch):
        monkeypatch.setattr(app.main, "SANCODER_API_KEY", "secret-key")
        r = client.get("/api/sessions/fake-id/ws")
        assert r.status_code != 401

    def test_no_key_configured_skips_auth(self, client, monkeypatch):
        monkeypatch.setattr(app.main, "SANCODER_API_KEY", "")
        r = client.get("/api/sessions")
        assert r.status_code == 200
