import os
import tempfile
import pytest
from fastapi.testclient import TestClient

os.environ["SANDCODER_TEST"] = "1"


@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch):
    """Use a temporary SQLite database for every test, cleaned up afterwards."""
    import app.db.database as db_mod
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    monkeypatch.setattr(db_mod, "DB_PATH", path)
    db_mod.init_db()
    yield
    try:
        os.unlink(path)
    except OSError:
        pass


@pytest.fixture
def client(setup_test_db):
    from app.main import app
    return TestClient(app)
