import docker
import os
import time
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class CodeExecutor:
    """
    A secure code execution environment using Docker.
    Allows running Python code and shell commands in an isolated container.
    """
    
    def __init__(self, image_tag: str = "python:3.10-slim", container_name: str = "mainframe_sandbox"):
        self.image_tag = image_tag
        self.container_name = container_name
        self.client = None
        self.container = None
        # attempt connection immediately
        self._connect()

    def _connect(self):
        """Connect to Docker daemon."""
        try:
            self.client = docker.from_env()
            logger.info("Connected to Docker daemon.")
        except Exception as e:
            logger.error(f"Failed to connect to Docker: {e}")
            self.client = None

    def ensure_container_running(self):
        """Ensures the sandbox container is running."""
        if not self.client:
            self._connect()
            if not self.client:
                return False

        try:
            # Check if container exists
            try:
                self.container = self.client.containers.get(self.container_name)
                if self.container.status != "running":
                    logger.info(f"Starting existing container {self.container_name}...")
                    self.container.start()
            except docker.errors.NotFound:
                # Create and start new container
                logger.info(f"Creating new container {self.container_name}...")
                
                # Load environment variables to pass to container
                from app.core.config import settings
                env_vars = {
                    "GOOGLE_API_KEY": settings.GOOGLE_API_KEY or "",
                    "OPENAI_API_KEY": settings.OPENAI_API_KEY or "",
                    "PYTHONUNBUFFERED": "1"
                }
                
                self.container = self.client.containers.run(
                    self.image_tag,
                    detach=True,
                    name=self.container_name,
                    command="tail -f /dev/null",
                    # volumes={'/opt/mainframe': {'bind': '/workspace', 'mode': 'rw'}}, # Removed due to SMB issues
                    working_dir="/workspace",
                    network_mode="bridge",
                    environment=env_vars, # Inject API Keys
                    restart_policy={"Name": "on-failure"},
                    mem_limit="512m",
                )
                logger.info(f"Started new container: {self.container.id}")
            
                # ALWAYS Copy project files into container to ensure sync
                # This handles both new containers and existing ones (syncing changes)
                try:
                    import tarfile
                    import io
                    
                    # Resolve real path to handle symlinks (GVFS/SMB)
                    source_path = os.path.realpath('/opt/mainframe')
                    
                    # Create a tar stream
                    stream = io.BytesIO()
                    
                    def filter_copy(tarinfo):
                        # Exclude heavy/unnecessary directories
                        name = tarinfo.name
                        if "/venv" in name or "/.git" in name or "/__pycache__" in name or "/node_modules" in name or "/data" in name:
                            return None
                        return tarinfo

                    with tarfile.open(fileobj=stream, mode='w') as tar:
                        try:
                            # Use the resolved path, but keep arcname as '.'
                            tar.add(source_path, arcname='.', filter=filter_copy)
                        except Exception as e:
                            logger.warning(f"Could not add full folder: {e}")

                    stream.seek(0)
                    self.container.put_archive('/workspace', stream)
                except Exception as e:
                    logger.error(f"Failed to sync project files: {e}")

            return True
        except Exception as e:
            logger.error(f"Error managing container: {e}")
            return False

    def run_code(self, code: str, language: str = "python") -> Dict[str, Any]:
        """
        Executes code in the container.
        """
        if not self.ensure_container_running():
            return {"error": "Docker container not available. Is Docker installed and running?"}

        try:
            # Write code to file
            filename = f"script_{int(time.time())}.py"
            with open(filename, "w") as f:
                f.write(code)
            
            # Execute in container
            # Using python directly on the file inside the container (mounted volume)
            cmd = f"python {filename}"
            exec_result = self.container.exec_run(cmd)
            
            # Cleanup
            try:
                os.remove(filename)
            except: pass
            
            return {
                "exit_code": exec_result.exit_code,
                "output": exec_result.output.decode("utf-8"),
                "command": cmd
            }
        except Exception as e:
            logger.error(f"Execution execution failed: {e}")
            return {"error": str(e)}

    def run_command(self, command: str) -> Dict[str, Any]:
        """
        Executes a shell command in the container.
        """
        if not self.ensure_container_running():
            return {"error": "Docker container not available"}

        try:
            exec_result = self.container.exec_run(command)
            return {
                "exit_code": exec_result.exit_code,
                "output": exec_result.output.decode("utf-8"),
                "command": command
            }
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return {"error": str(e)}

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
