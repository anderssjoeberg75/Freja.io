import docker
import os
import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class CodeExecutor:
    """
    A secure code execution environment using Docker.
    Allows running Python code and shell commands in an isolated container.
    """
    
    def __init__(self, image_tag: str = "freja-codex-sandbox", container_name: str = "mainframe_sandbox"):
        self.image_tag = image_tag
        self.container_name = container_name
        self.project_root = self._resolve_project_root()
        self.client = None
        self.container = None
        # attempt connection immediately
        self._connect()
        self._ensure_image()

    def _resolve_project_root(self) -> str:
        """Resolve the host project root that should be bind-mounted into /workspace."""
        env_root = os.environ.get("FREJA_PROJECT_ROOT")
        if env_root:
            return str(Path(env_root).expanduser().resolve())

        # skills/codex/executor.py -> project root is two levels up from skills/
        return str(Path(__file__).resolve().parents[2])

    def _connect(self):
        """Connect to Docker daemon."""
        try:
            self.client = docker.from_env()
            logger.info("Connected to Docker daemon.")
        except Exception as e:
            logger.error(f"Failed to connect to Docker: {e}")
            self.client = None

    def _ensure_image(self):
        """Builds the sandbox image if it doesn't exist."""
        if not self.client: return
        
        try:
            self.client.images.get(self.image_tag)
        except docker.errors.ImageNotFound:
            logger.info(f"Image {self.image_tag} not found. Building from Dockerfile.sandbox...")
            try:
                # Build from Dockerfile.sandbox in skills/codex/
                self.client.images.build(
                    path=".",
                    dockerfile="skills/codex/Dockerfile.sandbox",
                    tag=self.image_tag,
                    rm=True
                )
                logger.info(f"Successfully built {self.image_tag}")
            except Exception as e:
                logger.error(f"Failed to build sandbox image: {e}")

    def ensure_container_running(self, force_recreate: bool = False):
        """Ensures the sandbox container is running and synced."""
        if not self.client:
            self._connect()
            if not self.client:
                return False

        # Force reload of keys from .env directly to handle hot-updates
        try:
            from dotenv import dotenv_values
            config = dotenv_values(".env")
            google_key = config.get("GOOGLE_API_KEY") or os.environ.get("GOOGLE_API_KEY") or ""
            openai_key = config.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY") or ""
        except ImportError:
            google_key = os.environ.get("GOOGLE_API_KEY") or ""
            openai_key = os.environ.get("OPENAI_API_KEY") or ""

        try:
            # Check if container exists
            try:
                self.container = self.client.containers.get(self.container_name)
                
                if force_recreate:
                    logger.info("Forced recreation requested.")
                    self.container.stop()
                    self.container.remove()
                    raise docker.errors.NotFound("Forced recreation")

                # Check if container has the keys (recreation needed if missing)
                self.container.reload()
                env_list = self.container.attrs['Config']['Env']
                image_name = self.container.attrs['Config']['Image']
                mounts = self.container.attrs.get('Mounts', [])
                
                has_google = any(e.startswith("GOOGLE_API_KEY=") and len(e) > 16 for e in env_list)
                has_openai = any(e.startswith("OPENAI_API_KEY=") and len(e) > 16 for e in env_list)
                workspace_mount_ok = any(
                    m.get('Destination') == '/workspace' and Path(m.get('Source', '')).resolve() == Path(self.project_root)
                    for m in mounts
                )
                
                # If we have keys but container doesn't, OR image mismatch, recreate
                if (
                    (google_key and not has_google)
                    or (openai_key and not has_openai)
                    or (image_name != self.image_tag)
                    or (not workspace_mount_ok)
                ):
                    logger.info(f"Container configuration mismatch. Recreating...")
                    self.container.stop()
                    self.container.remove()
                    raise docker.errors.NotFound("Forced recreation")

                if self.container.status != "running":
                    logger.info(f"Starting existing container {self.container_name}...")
                    self.container.start()
            except docker.errors.NotFound:
                # Create and start new container
                logger.info(f"Creating new container {self.container_name}...")
                
                env_vars = {
                    "GOOGLE_API_KEY": google_key,
                    "OPENAI_API_KEY": openai_key,
                    "PYTHONUNBUFFERED": "1"
                }
                
                # Mount project root to /workspace to ensure self-analysis reads latest host files
                volumes = {
                    self.project_root: {'bind': '/workspace', 'mode': 'rw'}
                }
                
                self.container = self.client.containers.run(
                    self.image_tag,
                    detach=True,
                    name=self.container_name,
                    # CMD is now defined in Dockerfile to run execution_server.py
                    # We don't override input command unless we want to debug
                    volumes=volumes, 
                    network_mode="bridge",
                    network_disabled=True,
                    cap_drop=["ALL"],
                    environment=env_vars,
                    restart_policy={"Name": "on-failure"},
                )
                logger.info(f"Started new container: {self.container.id}")
                
                 # Wait a bit for server to start
                time.sleep(2)
            
            return True
        except Exception as e:
            logger.error(f"Error managing container: {e}")
            return False

    def run_code(self, code: str, language: str = "python") -> Dict[str, Any]:
        """
        Executes code in the container via the execution server.
        """
        if not self.ensure_container_running():
            return {"error": "Docker container not available. Is Docker installed and running?"}

        try:
            import json
            import tarfile
            import io
            
            if language == "python":
                # Prepare JSON payload for the server
                payload = json.dumps({"code": code})
                payload_filename = f"payload_{int(time.time()*1000)}.json"
                
                # Create tar stream for the payload file
                stream = io.BytesIO()
                with tarfile.open(fileobj=stream, mode='w') as tar:
                    encoded = payload.encode('utf-8')
                    tarinfo = tarfile.TarInfo(name=payload_filename)
                    tarinfo.size = len(encoded)
                    tarinfo.mtime = time.time()
                    tar.addfile(tarinfo, io.BytesIO(encoded))
                    
                stream.seek(0)
                self.container.put_archive('/workspace', stream)
                
                # Execute curl inside container using the payload file
                # The execution server listens on localhost:5000
                cmd = f"curl -s -X POST -H 'Content-Type: application/json' -d @{payload_filename} http://localhost:5000/execute"
                exec_result = self.container.exec_run(cmd)
                
                output = exec_result.output.decode("utf-8")
                
                # Try to clean up payload file (optional, but good practice)
                self.container.exec_run(f"rm {payload_filename}")

                if exec_result.exit_code != 0:
                    return {"exit_code": exec_result.exit_code, "output": f"Execution Server Error: {output}", "command": cmd}
                
                try:
                    # Parse the JSON response from the server
                    response_data = json.loads(output)
                    return {
                        "exit_code": response_data.get("exit_code", 0),
                        "output": response_data.get("output", ""),
                        "stdout": response_data.get("stdout", ""),
                        "stderr": response_data.get("stderr", ""),
                        "command": "python_execution_server"
                    }
                except json.JSONDecodeError:
                    return {"exit_code": 1, "output": f"Invalid JSON response from server: {output}", "command": cmd}
                    
            else:
                # Fallback for Shell commands - executed directly via docker exec
                exec_result = self.container.exec_run(code)
                return {
                    "exit_code": exec_result.exit_code,
                    "output": exec_result.output.decode("utf-8"),
                    "command": code
                }

        except Exception as e:
            logger.error(f"Execution failed: {e}")
            return {"error": str(e)}

    def run_command(self, command: str) -> Dict[str, Any]:
        """
        Executes a shell command in the container.
        """
        # Shell commands bypass the Python server and run directly in the container
        return self.run_code(command, language="shell")

    def reset_context(self) -> Dict[str, Any]:
        """Resets the Python execution context."""
        if not self.ensure_container_running():
            return {"error": "Container not running"}
            
        cmd = "curl -X POST http://localhost:5000/reset"
        exec_result = self.container.exec_run(cmd)
        return {"output": exec_result.output.decode("utf-8")}

    def stop_container(self):
        """Stops and removes the container."""
        if self.container:
            try:
                self.container.stop()
                self.container.remove()
                logger.info(f"Container {self.container_name} stopped and removed.")
                self.container = None
            except Exception as e:
                logger.error(f"Error stopping container: {e}")
