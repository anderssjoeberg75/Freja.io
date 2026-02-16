import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

print("Attempting to import skills.codex...")
try:
    import skills.codex
    print("SUCCESS: skills.codex imported.")
except Exception as e:
    print(f"FAILURE: {e}")
    import traceback
    traceback.print_exc()

print("\nAttempting to import skills.codex.tools...")
try:
    import skills.codex.tools
    print("SUCCESS: skills.codex.tools imported.")
except Exception as e:
    print(f"FAILURE: {e}")
    import traceback
    traceback.print_exc()
