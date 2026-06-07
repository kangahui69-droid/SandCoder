import subprocess
import pytest
from unittest.mock import patch, MagicMock

VALID_CONTAINER = "abc123"


class TestSandboxExecutor:
    """Unit tests for sandbox executor functions."""

    def test_execute_code_success(self):
        from app.sandbox.executor import execute_code
        mock_result = MagicMock()
        mock_result.stdout = "Hello"
        mock_result.stderr = ""
        mock_result.returncode = 0
        with patch("app.sandbox.executor.subprocess.run", return_value=mock_result):
            stdout, stderr, rc = execute_code(VALID_CONTAINER, "print('Hello')")
            assert stdout == "Hello"
            assert rc == 0

    def test_execute_code_timeout(self):
        from app.sandbox.executor import execute_code
        with patch("app.sandbox.executor.subprocess.run",
                   side_effect=subprocess.TimeoutExpired("docker exec", 30)):
            stdout, stderr, rc = execute_code(VALID_CONTAINER, "while True: pass")
            assert "timed out" in stderr.lower()
            assert rc == -1

    def test_execute_code_empty_container_id(self):
        from app.sandbox.executor import execute_code
        with pytest.raises(ValueError, match="non-empty"):
            execute_code("", "print('test')")

    def test_read_file_path_traversal_blocked(self):
        from app.sandbox.executor import read_file
        with pytest.raises(ValueError, match="traversal"):
            read_file(VALID_CONTAINER, "../../etc/passwd")

    def test_read_file_empty_container_id(self):
        from app.sandbox.executor import read_file
        with pytest.raises(ValueError, match="non-empty"):
            read_file("", "data.txt")

    def test_write_file_empty_container_id(self):
        from app.sandbox.executor import write_file
        with pytest.raises(ValueError, match="non-empty"):
            write_file("", "data.txt", "content")

    def test_install_package_valid(self):
        from app.sandbox.executor import install_package
        mock_result = MagicMock()
        mock_result.stdout = "Successfully installed numpy"
        mock_result.stderr = ""
        mock_result.returncode = 0
        with patch("app.sandbox.executor.subprocess.run", return_value=mock_result):
            result = install_package(VALID_CONTAINER, "numpy")
            assert "Success" in result

    def test_install_package_shell_metacharacters(self):
        from app.sandbox.executor import install_package
        with pytest.raises(ValueError, match="Invalid package name"):
            install_package(VALID_CONTAINER, "requests; rm -rf /")

    def test_install_package_empty_name(self):
        from app.sandbox.executor import install_package
        with pytest.raises(ValueError, match="non-empty"):
            install_package(VALID_CONTAINER, "")

    def test_install_package_name_too_long(self):
        from app.sandbox.executor import install_package
        long_name = "a" * 200
        with pytest.raises(ValueError, match="too long"):
            install_package(VALID_CONTAINER, long_name)
