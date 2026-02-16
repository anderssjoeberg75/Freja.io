import sys
import os
import json

sys.path.append(os.getcwd())

# Force load dependencies (similar to main.py)
from app.services.tool_registry import registry
import app.tools.implementations # Registers Codex

# Also load basic tools? `main.py` doesn't explicitly import `basic_tools`?
# `app/tools/implementations.py` imports `skills._core.skill_loader` which discovers skills.
# But `basic_tools`? 
# In `app/services/chat_service.py`: `from app.services.tool_registry import registry`.
# The `basic_tools` might be imported via `app/__init__` or `implementations`?

# Let's check if basic_tools is loaded.
try:
    import app.tools.basic_tools
    # Does basic_tools register itself?
    # It has `@registry.register`. So yes, if imported.
except ImportError:
    pass

print("--- Registered Tools ---")
tools = registry.get_gemini_function_declarations()

found_audit = False
found_analyze = False

for tool in tools:
    name = tool['name']
    desc = tool.get('description', '')
    print(f"Tool: {name}")
    print(f"  Desc: {desc[:50]}...")
    
    if name == 'codex_audit_codebase':
        found_audit = True
    if name == 'tool_analyze_code':
        found_analyze = True

print("-" * 20)
if found_audit:
    print("✅ codex_audit_codebase FOUND")
else:
    print("❌ codex_audit_codebase MISSING")

if found_analyze:
    print("✅ tool_analyze_code FOUND")
else:
    print("❌ tool_analyze_code MISSING")
