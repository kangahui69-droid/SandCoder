from app.db.repository import (
    create_session, get_session, update_session_name, add_message
)


class TestSessionNaming:
    def test_create_session_has_default_name(self):
        session = create_session()
        assert session.name == "New Session"
        assert session.session_id

    def test_update_session_name(self):
        session = create_session()
        update_session_name(session.session_id, "Data Analysis Task")
        reloaded = get_session(session.session_id)
        assert reloaded.name == "Data Analysis Task"

    def test_update_session_name_allows_empty_at_repo_level(self):
        session = create_session()
        update_session_name(session.session_id, "")
        reloaded = get_session(session.session_id)
        assert reloaded.name == ""

    def test_auto_name_from_first_message(self):
        session = create_session()
        add_message(session.session_id, "user", "Help me analyze CSV data with pandas")
        reloaded = get_session(session.session_id)
        assert reloaded.name == "Help me analyze CSV data with pandas"

    def test_auto_name_truncates_long_prompt(self):
        session = create_session()
        long_prompt = "A" * 100
        add_message(session.session_id, "user", long_prompt)
        reloaded = get_session(session.session_id)
        assert len(reloaded.name) == 40
        assert reloaded.name == "A" * 40

    def test_auto_name_only_on_first_message(self):
        session = create_session()
        add_message(session.session_id, "user", "First message")
        add_message(session.session_id, "assistant", "Response")
        add_message(session.session_id, "user", "Second message should not rename")
        reloaded = get_session(session.session_id)
        assert reloaded.name == "First message"

    def test_auto_name_skips_if_already_named(self):
        session = create_session()
        update_session_name(session.session_id, "My Custom Name")
        add_message(session.session_id, "user", "Later message")
        reloaded = get_session(session.session_id)
        assert reloaded.name == "My Custom Name"

    def test_auto_name_skips_empty_prompt(self):
        session = create_session()
        add_message(session.session_id, "user", "")
        reloaded = get_session(session.session_id)
        assert reloaded.name == "New Session"

    def test_auto_name_skips_whitespace_only_prompt(self):
        session = create_session()
        add_message(session.session_id, "user", "   ")
        reloaded = get_session(session.session_id)
        assert reloaded.name == "New Session"


class TestSessionNamingAPI:
    def test_patch_session_name(self, client):
        r = client.post("/api/sessions")
        session_id = r.json()["session_id"]
        assert r.json()["name"] == "New Session"

        r2 = client.patch(f"/api/sessions/{session_id}", json={"name": "My Task"})
        assert r2.status_code == 200
        assert r2.json()["name"] == "My Task"

    def test_patch_session_not_found(self, client):
        r = client.patch("/api/sessions/nonexistent", json={"name": "Test"})
        assert r.status_code == 404

    def test_patch_session_empty_name(self, client):
        r = client.post("/api/sessions")
        session_id = r.json()["session_id"]
        r2 = client.patch(f"/api/sessions/{session_id}", json={"name": ""})
        assert r2.status_code == 422

    def test_patch_session_name_too_long(self, client):
        r = client.post("/api/sessions")
        session_id = r.json()["session_id"]
        r2 = client.patch(f"/api/sessions/{session_id}", json={"name": "A" * 201})
        assert r2.status_code == 422

    def test_patch_session_name_max_length(self, client):
        r = client.post("/api/sessions")
        session_id = r.json()["session_id"]
        name_200 = "A" * 200
        r2 = client.patch(f"/api/sessions/{session_id}", json={"name": name_200})
        assert r2.status_code == 200
        assert r2.json()["name"] == name_200

    def test_session_list_includes_name(self, client):
        client.post("/api/sessions")
        r = client.get("/api/sessions")
        sessions = r.json()
        assert len(sessions) >= 1
        assert "name" in sessions[0]

    def test_create_session_has_name_in_response(self, client):
        r = client.post("/api/sessions")
        data = r.json()
        assert "name" in data
        assert data["name"] == "New Session"

    def test_session_detail_includes_name(self, client):
        r = client.post("/api/sessions")
        session_id = r.json()["session_id"]
        r2 = client.get(f"/api/sessions/{session_id}")
        assert r2.status_code == 200
        assert r2.json()["session"]["name"] == "New Session"
