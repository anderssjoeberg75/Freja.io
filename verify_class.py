import sys
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app.tools.code_executor")
logger.setLevel(logging.INFO)

# Add project root to path
sys.path.append(os.getcwd())

try:
    from app.tools.code_executor import CodeExecutor
    
    print("Initializing CodeExecutor...")
    executor = CodeExecutor()
    
    print("Running test code...")
    result = executor.run_code("print('Hello from CodeExecutor Class!')")
    
    print("\n--- RESULT ---")
    print(result)
    
    if result.get("exit_code") == 0:
        print("SUCCESS")
    else:
        print("FAILURE")
        print("Output:", result.get("output"))

except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
