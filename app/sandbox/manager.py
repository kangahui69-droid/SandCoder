import docker
import os
import time
from datetime import datetime, timezone
from threading import Thread

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
    dockerfile_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    )
    client.images.build(
        path=dockerfile_dir,
        dockerfile="Dockerfile.sandbox",
        tag=SANDBOX_IMAGE,
    )


def create_container(session_id: str) -> str:
    """Create a new sandbox container for a session."""
    client = get_client()
    workspace = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "sessions", session_id
    )
    os.makedirs(workspace, exist_ok=True)

    container = client.containers.run(
        SANDBOX_IMAGE,
        command="sleep infinity",
        volumes={workspace: {"bind": "/home/sandbox/workspace", "mode": "rw"}},
        network_mode="none" if NETWORK_DISABLED else None,
        mem_limit=MEMORY_LIMIT,
        nano_cpus=int(CPU_LIMIT * 1e9),
        detach=True,
        remove=True,
    )
    return container.id


def get_container(container_id: str):
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
        container = client.containers.get(container_id)
        container.stop(timeout=5)
        container.remove()
    except docker.errors.NotFound:
        pass


def cleanup_stale(active_ids: set[str]):
    """Remove containers not in the active set."""
    client = get_client()
    for container in client.containers.list(filters={"ancestor": SANDBOX_IMAGE}):
        if container.id not in active_ids:
            try:
                container.stop(timeout=5)
                container.remove()
            except Exception:
                pass
