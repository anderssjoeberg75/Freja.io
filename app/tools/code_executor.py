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
    
<<<<<<< HEAD
    def __init__(self, image_tag: str = "python:3.10-slim", container_name: str = "mainframe_sandbox"):
=======
    def __init__(self, image_tag: str = "freja-codex-sandbox", container_name: str = "mainframe_sandbox"):
>>>>>>> 331190c (Update: 2026-02-16 17:26:31)
        self.image_tag = image_tag
        self.container_name = container_name
        self.client = None
        self.container = None
        # attempt connection immediately
        self._connect()
<<<<<<< HEAD
=======
        self._ensure_image()
>>>>>>> 331190c (Update: 2026-02-16 17:26:31)

    def _connect(self):
        """Connect to Docker daemon."""
        try:
            self.client = docker.from_env()
            logger.info("Connected to Docker daemon.")
        except Exception as e:
            logger.error(f"Failed to connect to Docker: {e}")
            self.client = None

<<<<<<< HEAD
    def ensure_container_running(self):
        """Ensures the sandbox container is running."""
=======
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

    def ensure_container_running(self):
        """Ensures the sandbox container is running and synced."""
>>>>>>> 331190c (Update: 2026-02-16 17:26:31)
        if not self.client:
            self._connect()
            if not self.client:
                return False

<<<<<<< HEAD
=======
        # Force reload of keys from .env directly to handle hot-updates
        try:
            from dotenv import dotenv_values
            config = dotenv_values(".env")
            google_key = config.get("GOOGLE_API_KEY") or os.environ.get("GOOGLE_API_KEY") or ""
            openai_key = config.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY") or ""
        except ImportError:
            google_key = os.environ.get("GOOGLE_API_KEY") or ""
            openai_key = os.environ.get("OPENAI_API_KEY") or ""

>>>>>>> 331190c (Update: 2026-02-16 17:26:31)
        try:
            # Check if container exists
            try:
                self.container = self.client.containers.get(self.container_name)
<<<<<<< HEAD
=======
                
                # Check if container has the keys (recreation needed if missing)
                self.container.reload()
                env_list = self.container.attrs['Config']['Env']
                image_name = self.container.attrs['Config']['Image']
                
                has_google = any(e.startswith("GOOGLE_API_KEY=") and len(e) > 16 for e in env_list)
                has_openai = any(e.startswith("OPENAI_API_KEY=") and len(e) > 16 for e in env_list)
                
                # If we have keys but container doesn't, OR image mismatch, recreate
                if (google_key and not has_google) or (openai_key and not has_openai) or (image_name != self.image_tag):
                    logger.info(f"Container configuration mismatch (Image: {image_name} vs {self.image_tag}). Recreating...")
                    self.container.stop()
                    self.container.remove()
                    raise docker.errors.NotFound("Forced recreation")

>>>>>>> 331190c (Update: 2026-02-16 17:26:31)
                if self.container.status != "running":
                    logger.info(f"Starting existing container {self.container_name}...")
                    self.container.start()
            except docker.errors.NotFound:
                # Create and start new container
                logger.info(f"Creating new container {self.container_name}...")
                
<<<<<<< HEAD
                # Load environment variables to pass to container
                from app.core.config import settings
                env_vars = {
                    "GOOGLE_API_KEY": settings.GOOGLE_API_KEY or "",
                    "OPENAI_API_KEY": settings.OPENAI_API_KEY or "",
                    "PYTHONUNBUFFERED": "1"
                }
                
=======
                env_vars = {
                    "GOOGLE_API_KEY": google_key,
                    "OPENAI_API_KEY": openai_key,
                    "PYTHONUNBUFFERED": "1"
                }
                
                # Mount current working directory to /workspace
                cwd = os.getcwd()
                volumes = {
                    cwd: {'bind': '/workspace', 'mode': 'rw'}
                }
                
>>>>>>> 331190c (Update: 2026-02-16 17:26:31)
                self.container = self.client.containers.run(
                    self.image_tag,
                    detach=True,
                    name=self.container_name,
                    command="tail -f /dev/null",
<<<<<<< HEAD
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

=======
                    volumes=volumes, # Bind mount!
                    network_mode="bridge",
                    environment=env_vars,
                    restart_policy={"Name": "on-failure"},
                    # mem_limit="1g", # Increased for analysis
                )
                logger.info(f"Started new container: {self.container.id}")
            
>>>>>>> 331190c (Update: 2026-02-16 17:26:31)
            return True
        except Exception as e:
            logger.error(f"Error managing container: {e}")
            return False
<<<<<<< HEAD

=======
>>>>>>> 331190c (Update: 2026-02-16 17:26:31)
    def run_code(self, code: str, language: str = "python") -> Dict[str, Any]:
        """
        Executes code in the container.
        """
        if not self.ensure_container_running():
            return {"error": "Docker container not available. Is Docker installed and running?"}

        try:
<<<<<<< HEAD
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
=======
            import tarfile
            import io
            
            # Create script filename
            script_name = f"script_{int(time.time())}.py"
            
            # Create tar stream in memory
            stream = io.BytesIO()
            with tarfile.open(fileobj=stream, mode='w') as tar:
                encoded_code = code.encode('utf-8')
                tarinfo = tarfile.TarInfo(name=script_name)
                tarinfo.size = len(encoded_code)
                tarinfo.mtime = time.time()
                tar.addfile(tarinfo, io.BytesIO(encoded_code))
                
            stream.seek(0)
            
            # Upload to container
            self.container.put_archive('/workspace', stream)
            
            # Execute in container
            # Using python directly on the file inside the container (mounted volume)
            cmd = f"python {script_name}"
            exec_result = self.container.exec_run(cmd)
            
            output_text = exec_result.output.decode("utf-8")
            
            if exec_result.exit_code != 0:
                # With bind mount, file sync issues are unlikely unless permissions are wrong.
                pass
            
            return {
                "exit_code": exec_result.exit_code,
                "output": output_text,
>>>>>>> 331190c (Update: 2026-02-16 17:26:31)
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
