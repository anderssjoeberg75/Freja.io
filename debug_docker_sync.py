import docker
import tarfile
import io
import time
import os

CONTAINER_NAME = "mainframe_sandbox"

def debug_sync():
    print(f"--- Connecting to Docker ---")
    try:
        client = docker.from_env()
        print("Connected.")
    except Exception as e:
        print(f"Failed to connect: {e}")
        return

    try:
        container = client.containers.get(CONTAINER_NAME)
        print(f"Found container: {container.name} ({container.status})")
        if container.status != "running":
            print("Starting container...")
            container.start()
    except docker.errors.NotFound:
        print(f"Container {CONTAINER_NAME} not found! The app should have created it.")
        return

    # Prepare test file
    filename = f"debug_{int(time.time())}.py"
    content = "print('Hello from inside Docker!')"
    print(f"\n--- Preparing file {filename} ---")
    
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode='w') as tar:
        encoded = content.encode('utf-8')
        ti = tarfile.TarInfo(name=filename)
        ti.size = len(encoded)
        ti.mtime = time.time()
        tar.addfile(ti, io.BytesIO(encoded))
    stream.seek(0)

    print("Uploading archive to /workspace...")
    try:
        container.put_archive('/workspace', stream)
        print("Upload successful.")
    except Exception as e:
        print(f"Upload failed: {e}")
        return

    print("\n--- Listing /workspace ---")
    res = container.exec_run("ls -la /workspace")
    print(res.output.decode('utf-8'))

    print(f"\n--- Executing {filename} ---")
    res = container.exec_run(f"python {filename}")
    print(f"Exit Code: {res.exit_code}")
    print(f"Output: {res.output.decode('utf-8')}")

if __name__ == "__main__":
    debug_sync()
