import asyncio
from concurrent.futures import ThreadPoolExecutor
from app.sandbox.executor import execute_code, read_file, write_file, install_package

_executor = ThreadPoolExecutor(max_workers=4)
_container_id: str = ""


def set_container(container_id: str):
    """Set the active container for subsequent tool calls. Called before each agent run."""
    global _container_id
    _container_id = container_id


async def run_in_thread(func, *args):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, func, *args)


async def tool_execute_code(code: str) -> str:
    """Execute Python code in the sandbox. Returns stdout, or stderr with exit code on failure."""
    stdout, stderr, exit_code = await run_in_thread(execute_code, _container_id, code)
    if exit_code == 0:
        return stdout or "(executed successfully, no output)"
    return f"Exit code: {exit_code}\nStderr: {stderr}"


async def tool_read_file(path: str) -> str:
    """Read a file from the sandbox workspace."""
    if not path.startswith("/"):
        path = f"/home/sandbox/workspace/{path}"
    return await run_in_thread(read_file, _container_id, path)


async def tool_write_file(path: str, content: str) -> str:
    """Write content to a file in the sandbox workspace."""
    if not path.startswith("/"):
        path = f"/home/sandbox/workspace/{path}"
    return await run_in_thread(write_file, _container_id, path, content)


async def tool_install_package(package_name: str) -> str:
    """Install a pip package in the sandbox (requires root, handled by executor)."""
    return await run_in_thread(install_package, _container_id, package_name)
