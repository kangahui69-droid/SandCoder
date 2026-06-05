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

    def test_update_session_name_rejects_empty(self):
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
