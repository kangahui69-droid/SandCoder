import subprocess
import tempfile
import os

EXEC_TIMEOUT = 30  # seconds


def execute_code(container_id: str, code: str) -> tuple[str, str, int]:
    """Execute Python code in the sandbox container. Returns (stdout, stderr, exit_code)."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as f:
        f.write(code)
        tmp_path = f.name

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
        return "", "Execution timed out after 30 seconds", -1
    finally:
        os.unlink(tmp_path)


def read_file(container_id: str, path: str) -> str:
    """Read a file from the sandbox container."""
    result = subprocess.run(
        ["docker", "exec", "--user", "sandbox", container_id, "cat", path],
        capture_output=True, text=True, timeout=10,
    )
    if result.returncode != 0:
        return f"Error reading file: {result.stderr}"
    return result.stdout


def write_file(container_id: str, path: str, content: str) -> str:
    """Write content to a file in the sandbox container."""
    result = subprocess.run(
        ["docker", "exec", "--user", "sandbox", container_id, "tee", path],
        input=content, capture_output=True, text=True, timeout=10,
    )
    if result.returncode != 0:
        return f"Error writing file: {result.stderr}"
    return f"File written to {path}"


def install_package(container_id: str, package_name: str) -> str:
    """Install a pip package in the sandbox container."""
    result = subprocess.run(
        ["docker", "exec", "--user", "root", container_id,
         "pip", "install", package_name],
        capture_output=True, text=True, timeout=60,
    )
    return result.stdout if result.returncode == 0 else result.stderr
