import asyncio
import contextvars
from concurrent.futures import ThreadPoolExecutor
from app.sandbox.executor import execute_code, read_file, write_file, install_package

_executor: ThreadPoolExecutor | None = None
_container_id: contextvars.ContextVar[str] = contextvars.ContextVar("container_id", default="")


def init_executor():
    """Initialize the thread pool executor. Called during app startup."""
    global _executor
    if _executor is None:
        _executor = ThreadPoolExecutor(max_workers=4)


def get_executor() -> ThreadPoolExecutor:
    """Get the executor, initializing it lazily if needed."""
    global _executor
    if _executor is None:
        _executor = ThreadPoolExecutor(max_workers=4)
    return _executor


def set_container(container_id: str):
    """Set the active container for subsequent tool calls. ContextVar ensures per-request isolation."""
    _container_id.set(container_id)


def shutdown_executor():
    """Shutdown the thread pool executor. Call during app teardown."""
    global _executor
    if _executor is not None:
        _executor.shutdown(wait=True)
        _executor = None


async def run_in_thread(func, *args):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(get_executor(), func, *args)


async def tool_execute_code(code: str) -> str:
    """Execute Python code in the sandbox. Returns stdout, or stderr with exit code on failure."""
    container_id = _container_id.get()
    stdout, stderr, exit_code = await run_in_thread(execute_code, container_id, code)
    if exit_code == 0:
        return stdout or "(executed successfully, no output)"
    return f"Exit code: {exit_code}\nStderr: {stderr}"


async def tool_read_file(path: str) -> str:
    """Read a file from the sandbox workspace. Path is resolved safely by the executor."""
    container_id = _container_id.get()
    return await run_in_thread(read_file, container_id, path)


async def tool_write_file(path: str, content: str) -> str:
    """Write content to a file in the sandbox workspace. Path is resolved safely by the executor."""
    container_id = _container_id.get()
    return await run_in_thread(write_file, container_id, path, content)


async def tool_install_package(package_name: str) -> str:
    """Install a pip package in the sandbox."""
    container_id = _container_id.get()
    return await run_in_thread(install_package, container_id, package_name)
