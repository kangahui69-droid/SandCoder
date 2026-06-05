import asyncio
import contextvars
import logging
from concurrent.futures import ThreadPoolExecutor
from app.sandbox.executor import execute_code, read_file, write_file, install_package

logger = logging.getLogger(__name__)

_executor: ThreadPoolExecutor | None = None
_container_id: contextvars.ContextVar[str] = contextvars.ContextVar("container_id", default="")
_session_id: contextvars.ContextVar[str] = contextvars.ContextVar("session_id", default="")


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


def set_session(session_id: str):
    """Set the active session for WebSocket progress push."""
    _session_id.set(session_id)


async def _push_log(message: str):
    """Push a log message to WebSocket clients for the current session."""
    sid = _session_id.get()
    if not sid:
        return
    try:
        from app.routes.ws import send_execution_log
        await send_execution_log(sid, message)
    except Exception:
        logger.debug("Failed to push log via WebSocket", exc_info=True)


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
    preview = code[:80].replace('\n', ' ') + ('...' if len(code) > 80 else '')
    await _push_log(f"Executing: {preview}")
    try:
        stdout, stderr, exit_code = await run_in_thread(execute_code, container_id, code)
    except Exception as e:
        await _push_log(f"Execution failed: {e}")
        return f"Error executing code: {e}"
    if exit_code == 0:
        result = stdout or "(executed successfully, no output)"
    else:
        result = f"Exit code: {exit_code}\nStderr: {stderr}"
    await _push_log(f"Done (exit {exit_code})")
    return result


async def tool_read_file(path: str) -> str:
    """Read a file from the sandbox workspace. Path is resolved safely by the executor."""
    container_id = _container_id.get()
    await _push_log(f"Reading file: {path}")
    try:
        result = await run_in_thread(read_file, container_id, path)
    except Exception as e:
        await _push_log(f"Read failed: {e}")
        return f"Error reading file: {e}"
    if result is None:
        await _push_log("Read returned no data")
        return "Error: file not found or empty"
    await _push_log(f"Read {len(result)} bytes")
    return result


async def tool_write_file(path: str, content: str) -> str:
    """Write content to a file in the sandbox workspace. Path is resolved safely by the executor."""
    container_id = _container_id.get()
    await _push_log(f"Writing file: {path} ({len(content)} bytes)")
    try:
        result = await run_in_thread(write_file, container_id, path, content)
    except Exception as e:
        await _push_log(f"Write failed: {e}")
        return f"Error writing file: {e}"
    await _push_log(f"Wrote {path}")
    return result


async def tool_install_package(package_name: str) -> str:
    """Install a pip package in the sandbox."""
    container_id = _container_id.get()
    await _push_log(f"Installing package: {package_name}")
    try:
        result = await run_in_thread(install_package, container_id, package_name)
    except Exception as e:
        await _push_log(f"Install failed: {e}")
        return f"Error installing package: {e}"
    await _push_log(f"Installed {package_name}")
    return result
