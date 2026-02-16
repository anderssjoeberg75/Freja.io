import sys
import os
import asyncio
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("verify_audit")

# Add project root to path
sys.path.append(os.getcwd())

async def run_test():
    try:
        from app.core import dependencies
        from app.tools.code_executor import CodeExecutor
        
        # Initialize executor directly (bypass dependency injection to ensure fresh instance)
        executor = CodeExecutor()
        
        print("--- 1. Checking Environment Variables in Container ---")
        # specific check for keys
        cmd_env = 'python3 -c "import os; print(f\'GOOGLE={bool(os.environ.get(\'GOOGLE_API_KEY\'))}\'); print(f\'OPENAI={bool(os.environ.get(\'OPENAI_API_KEY\'))}\')"'
        res_env = executor.run_command(cmd_env)
        print(f"Environment Check:\n{res_env.get('output', '')}")
        
        print("\n--- 2. Checking Internet Connectivity in Container ---")
        # curl or ping
        cmd_net = 'curl -I https://www.google.com --connect-timeout 5'
        res_net = executor.run_command(cmd_net)
        print(f"Network Check (Google):\n{res_net.get('output', '')}\nExit Code: {res_net.get('exit_code')}")
        
        print("\n--- 3. Running Actual Audit Script ---")
        # Load the actual auditor code
        import app.tools.code_auditor
        auditor_file = app.tools.code_auditor.__file__
        with open(auditor_file, "r") as f:
            script_content = f.read()
        
        # Append execution call that prints to stdout
        script_content += "\n\nif __name__ == '__main__':\n    print(run_code_audit())"
        
        # Run it
        limit = 120 # 2 minutes timeout
        # CodeExecutor run_code doesn't support timeout arg in my implementation, 
        # but docker exec usually waits.
        
        result = executor.run_code(script_content)
        
        print("\n--- Audit Execution Result ---")
        print(f"Exit Code: {result.get('exit_code')}")
        print("Output (Truncated to last 2000 chars):")
        output = result.get('output', '')
        print(output[-2000:] if len(output) > 2000 else output)
        
        # Check for specific errors in output
        if "failed: " in output:
            print("\n!!! FAILURE DETECTED IN LOGS !!!")
            # Extract failure lines
            for line in output.split('\n'):
                if "failed:" in line or "Error" in line:
                    print(f"Failure Detail: {line.strip()}")

    except Exception as e:
        print(f"Test Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_test())
