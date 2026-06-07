import os
import tempfile
import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient

load_dotenv()

os.environ["SANDCODER_TEST"] = "1"
# Clear auth API keys so test requests bypass the auth middleware.
# Set to empty string (not pop) so main.py's load_dotenv() won't re-load from .env.
os.environ["DEEPSEEK_API_KEY"] = ""
os.environ.pop("SANCODER_API_KEY", None)


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
