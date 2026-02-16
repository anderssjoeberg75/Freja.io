import asyncio
import json
from typing import Optional, Literal
from pydantic import BaseModel, Field

from app.core import dependencies
from app.services.tool_registry import ToolRegistry
from app.tools.git_core import GitTool
from app.tools.code_auditor import run_code_audit

# --- Tool Schemas ---

class ExecuteCodeSchema(BaseModel):
    # This schema defines the arguments required for execute_codex_code
    language: Literal["python", "shell"] = Field(..., description="Language to execute. Use 'python' for Python scripts and 'shell' for bash commands.")
    code: str = Field(..., description="The code or command to execute inside the Docker sandbox.")

class GitOperationSchema(BaseModel):
    # This schema defines the arguments required for codex_git_ops
    action: Literal["clone", "checkout", "commit", "push", "status", "log"] = Field(..., description="The Git action to perform.")
    argument: Optional[str] = Field(None, description="Argument for the action (e.g., repo URL, branch name, commit message). Mandatory for clone, checkout, and commit.")

class AuditCodeSchema(BaseModel):
    # No arguments needed for this tool
    pass

# --- Tool Implementations ---

async def execute_code_impl(language: str, code: str) -> str:
    """Executes code in the Docker sandbox."""
    executor = dependencies.get_code_executor()
    
    # Check if executor is available (might be None if Docker is missing)
    if not executor:
        return "Error: Code Execution environment not available. Is Docker installed?"
    
    loop = asyncio.get_event_loop()
    
    if language == "python":
        # Run python code via executor.run_code
        result = await loop.run_in_executor(None, executor.run_code, code)
    else:
         # Run shell command via executor.run_command
        result = await loop.run_in_executor(None, executor.run_command, code)
        
    return json.dumps(result, indent=2)

async def git_operation_impl(action: str, argument: Optional[str] = None) -> str:
    """Performs Git operations."""
    git_tool = GitTool() # Initialize on demand
    loop = asyncio.get_event_loop()
    
    if action == "clone":
        if not argument: return "Error: Missing URL for clone."
        return await loop.run_in_executor(None, git_tool.clone_repo, argument, None)
    
    elif action == "checkout":
        if not argument: return "Error: Missing branch name."
        # Assuming checkout existing branch for simplicity
        return await loop.run_in_executor(None, git_tool.checkout_branch, argument, False)
        
    elif action == "commit":
        if not argument: return "Error: Missing commit message."
        return await loop.run_in_executor(None, git_tool.commit_changes, argument)
        
    elif action == "push":
        # Push to origin/current-branch
        return await loop.run_in_executor(None, git_tool.push_changes)
        
    elif action == "status":
        return await loop.run_in_executor(None, git_tool.get_status)
        
    elif action == "log":
        return await loop.run_in_executor(None, git_tool.get_log)
        
    return f"Unknown action: {action}"

async def audit_code_impl() -> str:
    """Triggers self-analysis inside Docker."""
    executor = dependencies.get_code_executor()
    if not executor:
        return "Error: Docker environment not available for code audit. Please install Docker."

    # Read the auditor source code
    try:
        import app.tools.code_auditor
        auditor_file = app.tools.code_auditor.__file__
        with open(auditor_file, "r") as f:
            script_content = f.read()
        
        # Append execution call
        script_content += "\n\nif __name__ == '__main__':\n    print(run_code_audit())"
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, executor.run_code, script_content)
        
        # --- Notification Logic ---
        output = result.get("output", "")
        import re
        import os
        
        # Extract filename from output: "saved to: /workspace/docs/code_audit_...md*"
        match = re.search(r"saved to: (.*?)\*", output)
        if match:
            docker_path = match.group(1).strip()
            
            # With Bind Mounts, /workspace maps to os.getcwd()
            # Docker: /workspace/docs/file.md -> Host: ./docs/file.md
            if "/workspace/" in docker_path:
                rel_path = docker_path.replace("/workspace/", "")
                host_path = os.path.abspath(rel_path)
                
                # Verify file exists on host (should be instant with bind mount)
                if os.path.exists(host_path):
                     try:
                        from app.services.telegram_service import telegram_service
                        if telegram_service:
                            if "✅" in output:
                                clean_output = output.split("✅")[1]
                                summary = clean_output.split("📂")[0].strip()
                                msg = f"✅{summary}"
                            else:
                                msg = output[:2000]
                            
                            await telegram_service.send_message(msg)
                            await telegram_service.send_document(host_path, caption="Självanalys Rapport")
                     except Exception as e:
                        print(f"Telegram notification failed: {e}")
                else:
                    print(f"Error: generated file {host_path} not found on host (Bind mount issue?)")

        return json.dumps(result, indent=2)
        
    except Exception as e:
        return f"Error preparing audit script: {e}"

# --- Registration ---

def register_tools(registry: ToolRegistry) -> None:
    """Register Codex tools."""

    # Register main tool
    registry.register(
        name="execute_codex_code",
        description="Executes Python code or Shell commands in a secure Docker sandbox. Use to run scripts, tests, or system administration tasks.",
        args_schema=ExecuteCodeSchema,
    )(execute_code_impl)

    # Register aliases for backwards compatibility
    registry.register(
        name="tool_code_executor",
        description="Alias for execute_codex_code. Executes Python code or Shell commands.",
        args_schema=ExecuteCodeSchema,
    )(execute_code_impl)

    registry.register(
        name="run_code",
        description="Alias for execute_codex_code. Executes Python code or Shell commands.",
        args_schema=ExecuteCodeSchema,
    )(execute_code_impl)
    
    registry.register(
        name="codex_git_ops",
        description="Manages the internal Git repository. Clone, checkout, commit, push changes.",
        args_schema=GitOperationSchema,
    )(git_operation_impl)

    registry.register(
        name="codex_audit_codebase", 
        description="Analyzes the Freja codebase for bugs and improvements. Use this when the user asks for 'självanalys', 'self-analysis', or 'analyze code'. DO NOT search the web for this.",
        args_schema=AuditCodeSchema,
    )(audit_code_impl)
    
    registry.register(
        name="tool_analyze_code", 
        description="Alias for codex_audit_codebase. Performs self-analysis of the code.",
        args_schema=AuditCodeSchema,
    )(audit_code_impl)
