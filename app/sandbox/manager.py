import docker
import os
import logging
import pathlib
from datetime import datetime, UTC, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

SANDBOX_IMAGE = "sandcoder-sandbox:latest"
NETWORK_DISABLED = True
MEMORY_LIMIT = "256m"
CPU_LIMIT = 1.0
IDLE_TIMEOUT = 30 * 60  # 30 minutes
CLEANUP_INTERVAL = 5 * 60  # check every 5 minutes

_client = None


def get_client() -> docker.DockerClient:
    global _client
    if _client is None:
        _client = docker.from_env()
    return _client


def build_image():
    """Build the sandbox image from Dockerfile.sandbox."""
    client = get_client()
    dockerfile_dir = pathlib.Path(__file__).parents[2]
    try:
        logger.info("Building sandbox image: %s", SANDBOX_IMAGE)
        client.images.build(
            path=str(dockerfile_dir),
            dockerfile="Dockerfile.sandbox",
            tag=SANDBOX_IMAGE,
        )
        logger.info("Sandbox image built successfully: %s", SANDBOX_IMAGE)
    except (docker.errors.DockerException, docker.errors.APIError) as exc:
        logger.error("Failed to build sandbox image: %s", exc)
        raise


def create_container(session_id: str) -> str:
    """Create a new sandbox container for a session."""
    client = get_client()
    workspace = pathlib.Path(__file__).parents[2] / "sessions" / session_id
    os.makedirs(workspace, exist_ok=True)

    try:
        logger.info("Creating sandbox container for session: %s", session_id)
        container = client.containers.run(
            SANDBOX_IMAGE,
            command="sleep infinity",
            volumes={str(workspace): {"bind": "/home/sandbox/workspace", "mode": "rw"}},
            network_mode="none" if NETWORK_DISABLED else None,
            mem_limit=MEMORY_LIMIT,
            nano_cpus=int(CPU_LIMIT * 1e9),
            detach=True,
            remove=True,
        )
        logger.info("Container created: %s (session: %s)", container.id, session_id)
        return container.id
    except docker.errors.ImageNotFound:
        logger.error("Sandbox image not found: %s — build it first", SANDBOX_IMAGE)
        raise
    except (docker.errors.DockerException, docker.errors.APIError) as exc:
        logger.error("Failed to create container for session %s: %s", session_id, exc)
        raise


def get_container(container_id: str) -> Optional[docker.models.containers.Container]:
    """Get a container by ID, or None if not found."""
    client = get_client()
    try:
        return client.containers.get(container_id)
    except docker.errors.NotFound:
        return None


def stop_container(container_id: str):
    """Stop and remove a container. Containers use auto-remove, so stop() is sufficient."""
    client = get_client()
    try:
        logger.info("Stopping container: %s", container_id)
        container = client.containers.get(container_id)
        container.stop(timeout=5)
        logger.info("Container stopped: %s", container_id)
    except docker.errors.NotFound:
        logger.warning("Container not found (already removed?): %s", container_id)
    except docker.errors.APIError as exc:
        if exc.status_code == 409:
            logger.debug("Container %s already being removed", container_id)
        else:
            raise


def cleanup_stale(active_ids: set[str]):
    """Remove containers not in the active set. Containers use auto-remove."""
    client = get_client()
    for container in client.containers.list(filters={"ancestor": SANDBOX_IMAGE}):
        if container.id not in active_ids:
            try:
                logger.info("Cleaning up stale container: %s", container.id)
                container.stop(timeout=5)
            except docker.errors.NotFound:
                pass
            except Exception as exc:
                logger.warning("Failed to clean up stale container %s: %s", container.id, exc)


def cleanup_idle_containers():
    """Stop containers for sessions that have been idle longer than IDLE_TIMEOUT."""
    from app.db.repository import list_sessions, clear_container

    cutoff = datetime.now(UTC) - timedelta(seconds=IDLE_TIMEOUT)
    sessions = list_sessions()

    for s in sessions:
        if not s.container_id:
            continue
        try:
            last_active = datetime.fromisoformat(s.last_active)
        except (ValueError, TypeError):
            logger.debug("Skipping session %s — invalid last_active: %s", s.session_id, s.last_active)
            continue

        if last_active < cutoff:
            logger.info("Idle timeout: stopping container %s for session %s (last active %s)",
                        s.container_id, s.session_id, s.last_active)
            try:
                stop_container(s.container_id)
            except Exception:
                logger.warning("Failed to stop idle container %s", s.container_id, exc_info=True)
            clear_container(s.session_id)
            logger.info("Cleared container_id for idle session %s", s.session_id)
