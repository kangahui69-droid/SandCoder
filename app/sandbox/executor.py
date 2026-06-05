import logging
import os as _os
import subprocess

EXEC_TIMEOUT = 30  # seconds

logger = logging.getLogger(__name__)


def _check_container(container_id: str) -> None:
    """Validate container_id is non-empty."""
    if not container_id or not container_id.strip():
        raise ValueError("container_id must be a non-empty string")


def _safe_path(path: str) -> str:
    """Resolve path safely within workspace. Raises ValueError if path escapes."""
    # Catch absolute paths on both Linux (starts with /) and Windows (drive letter)
    if path.startswith("/") or _os.path.isabs(path):
        raise ValueError(f"Absolute paths not allowed: {path}")
    joined = _os.path.join("/home/sandbox/workspace", path)
    # Normalize to forward slashes so startswith works cross-platform
    full = _os.path.normpath(joined).replace("\\", "/")
    if not full.startswith("/home/sandbox/workspace"):
        raise ValueError(f"Path traversal detected: {path}")
    return full


def execute_code(container_id: str, code: str) -> tuple[str, str, int]:
    """Execute Python code in the sandbox container. Returns (stdout, stderr, exit_code)."""
    _check_container(container_id)
    try:
        result = subprocess.run(
            [
                "docker", "exec", "--user", "sandbox",
                "--workdir", "/home/sandbox/workspace",
                container_id,
                "python", "-c", code,
            ],
            capture_output=True, text=True, timeout=EXEC_TIMEOUT,
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        logger.error("Execution timed out in container %s", container_id)
        return "", "Execution timed out after 30 seconds", -1


def read_file(container_id: str, path: str) -> str:
    """Read a file from the sandbox container."""
    _check_container(container_id)
    safe = _safe_path(path)
    result = subprocess.run(
        ["docker", "exec", "--user", "sandbox", container_id, "cat", safe],
        capture_output=True, text=True, timeout=10,
    )
    if result.returncode != 0:
        logger.error("Error reading file %s: %s", safe, result.stderr)
        return f"Error reading file: {result.stderr}"
    return result.stdout


def write_file(container_id: str, path: str, content: str) -> str:
    """Write content to a file in the sandbox container."""
    _check_container(container_id)
    safe = _safe_path(path)
    result = subprocess.run(
        ["docker", "exec", "-i", "--user", "sandbox", container_id, "tee", safe],
        input=content, capture_output=True, text=True, timeout=10,
    )
    if result.returncode != 0:
        logger.error("Error writing file %s: %s", safe, result.stderr)
        return f"Error writing file: {result.stderr}"
    return f"File written to {path}"


def install_package(container_id: str, package_name: str) -> str:
    """Install a pip package in the sandbox container."""
    _check_container(container_id)
    result = subprocess.run(
        ["docker", "exec", "--user", "root", container_id,
         "pip", "install", "--", package_name],
        capture_output=True, text=True, timeout=60,
    )
    if result.returncode != 0:
        logger.error("Failed to install package %s: %s", package_name, result.stderr)
    return result.stdout if result.returncode == 0 else result.stderr
