import docker
import os
import logging
import pathlib
from typing import Optional

logger = logging.getLogger(__name__)

SANDBOX_IMAGE = "sandcoder-sandbox:latest"
NETWORK_DISABLED = True
MEMORY_LIMIT = "256m"
CPU_LIMIT = 1.0
IDLE_TIMEOUT = 30 * 60  # 30 minutes

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
    """Stop and remove a container."""
    client = get_client()
    try:
        logger.info("Stopping container: %s", container_id)
        container = client.containers.get(container_id)
        container.stop(timeout=5)
        container.remove()
        logger.info("Container stopped and removed: %s", container_id)
    except docker.errors.NotFound:
        logger.warning("Container not found (already removed?): %s", container_id)


def cleanup_stale(active_ids: set[str]):
    """Remove containers not in the active set."""
    client = get_client()
    for container in client.containers.list(filters={"ancestor": SANDBOX_IMAGE}):
        if container.id not in active_ids:
            try:
                logger.info("Cleaning up stale container: %s", container.id)
                container.stop(timeout=5)
                container.remove()
            except Exception as exc:
                logger.warning("Failed to clean up stale container %s: %s", container.id, exc)
