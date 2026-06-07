"""Tests for database module — DB_PATH resolution."""


class TestDatabase:
    def test_db_path_env_var_override(self, monkeypatch):
        monkeypatch.setenv("SANDCODER_DB_PATH", "/custom/path/test.db")
        import importlib
        import app.db.database as db_mod
        importlib.reload(db_mod)
        assert db_mod.DB_PATH == "/custom/path/test.db"
