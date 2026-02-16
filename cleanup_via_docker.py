import sys
import os
# Add project root to path
sys.path.append(os.getcwd())

from app.tools.code_executor import CodeExecutor

def clean():
    print("Initializing CodeExecutor...")
    executor = CodeExecutor()
    
    files_to_remove = "script_*.py debug_*.py"
    print(f"Removing {files_to_remove} inside container...")
    
    # Run rm inside container. Since /workspace is bind-mounted to current dir,
    # this deletes files on host too. Container runs as root, so permissions are fine.
    result = executor.run_command(f"rm -f {files_to_remove}")
    
    print(f"Exit Code: {result.get('exit_code')}")
    print(f"Output: {result.get('output')}")

if __name__ == "__main__":
    clean()
