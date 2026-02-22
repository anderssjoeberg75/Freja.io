import asyncio
import json
import httpx
from typing import Optional, Literal
from pydantic import BaseModel, Field

from app.core import dependencies
from app.services.tool_registry import ToolRegistry

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

    try:
        cmd = "python3 skills/codex/auditor.py"
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, executor.run_command, cmd)
        
        # --- Notification Logic ---
        output = result.get("output", "")
        import re
        import os
        
        # Extract filename from output: "saved to: /workspace/docs/code_audit_...md*"
        match = re.search(r"saved to: (.*?)\*", output)
        if match:
            docker_path = match.group(1).strip()
            
            # Handle both Docker paths (/workspace/...) and direct host paths
            if "/workspace/" in docker_path:
                rel_path = docker_path.replace("/workspace/", "")
                host_path = os.path.abspath(rel_path)
            else:
                host_path = os.path.abspath(docker_path)
                
            # Verify file exists on host
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

class RunAndFixSchema(BaseModel):
    command: str = Field(..., description="The command to run (e.g., 'pytest tests/test_login.py' or 'python script.py').")
    file_path: str = Field(..., description="The path to the file that should be fixed if the command fails.")
    max_retries: int = Field(3, description="Maximum number of auto-fix attempts.")
# Coding model priority order — most capable first
_CODING_MODEL_PRIORITY = [
    "qwen2.5-coder",
    "codellama",
    "starcoder2",
    "deepseek-coder",
    "llama3.1",
    "llama3",
    "mistral",
]

async def _pick_best_coding_model(base_url: str) -> str:
    """Query Ollama /api/tags and return the best available coding model."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{base_url}/api/tags")
            if resp.status_code == 200:
                models = [m["name"] for m in resp.json().get("models", [])]
                for preferred in _CODING_MODEL_PRIORITY:
                    for available in models:
                        if available.split(":")[0].lower().startswith(preferred):
                            return available
                # Return first available model as last resort
                if models:
                    return models[0]
    except Exception:
        pass
    return "llama3.1:8b"  # Safe fallback


async def run_and_fix_impl(command: str, file_path: str, max_retries: int = 3) -> str:
    """Runs a command and attempts to fix the file if it fails."""
    import google.generativeai as genai
    from app.core.config import get_credential, settings
    import os
    import httpx

    executor = dependencies.get_code_executor()
    if not executor:
        return "Error: Code Execution environment not available."

    # Validate file existence
    if not os.path.exists(file_path):
        return f"Error: Target file {file_path} not found."

    api_key = get_credential("GOOGLE_API_KEY") or settings.GOOGLE_API_KEY

    use_ollama = False
    model_name = "gemini-2.0-flash"  # Best quality for code fixing

    if api_key:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_name)
        except Exception:
            use_ollama = True
    else:
        use_ollama = True

    if use_ollama:
        ollama_url = get_credential("OLLAMA_URL") or settings.OLLAMA_URL
        if not ollama_url:
            return "Error: No Google API Key and no OLLAMA_URL found."
        base_url = ollama_url.rstrip("/")
        # Dynamically pick best available coding model from Ollama
        model_name = await _pick_best_coding_model(base_url)
        import logging
        logging.getLogger(__name__).info(f"[Codex] Using Ollama coding model: {model_name}")


    history = []
    
    for attempt in range(max_retries + 1):
        # Run the command
        loop = asyncio.get_event_loop()
        # Use run_command wrapper
        if command.endswith(".py"):
             # If it's a python script, use the python execution for stateful context if desired, 
             # but usually 'command' implies shell. Let's strictly use shell command execution for generality.
             result = await loop.run_in_executor(None, executor.run_code, command)
        else:
             result = await loop.run_in_executor(None, executor.run_command, command)

        exit_code = result.get("exit_code", 1)
        output = result.get("output", "")

        if exit_code == 0:
            return f"✅ Success on attempt {attempt+1}!\nOutput:\n{output}"

        if attempt == max_retries:
            return f"❌ Failed after {max_retries} attempts.\nLast Output:\n{output}"

        # If failed, try to fix
        print(f"Attempt {attempt+1} failed. Generating fix...")
        
        loop = asyncio.get_event_loop()
        def _read_current():
            with open(file_path, "r") as f:
                return f.read()
        current_code = await loop.run_in_executor(None, _read_current)

        prompt = f"""
        The command `{command}` failed using this code in `{file_path}`.
        
        Output:
        {output}
        
        Current Code:
        {current_code}
        
        Fix the code to resolve the error. 
        IMPORTANT: Return ONLY the full fixed code. No markdown formatting, no explanations. 
        Just the raw code ready to be written to the file.
        """
        
        try:
            fixed_code = ""
            if use_ollama:
                 async with httpx.AsyncClient(timeout=60.0) as client:
                    payload = {
                        "model": model_name,
                        "messages": [{"role": "user", "content": prompt}],
                        "stream": False
                    }
                    resp = await client.post(f"{base_url}/api/chat", json=payload)
                    if resp.status_code == 200:
                        fixed_code = resp.json().get("message", {}).get("content", "")
                    else:
                        return f"Ollama Error: {resp.text}"
            else:
                # We use a simple generate_content
                response = await loop.run_in_executor(None, model.generate_content, prompt)
                if not response.text:
                    return f"Error: Empty response from LLM during fix attempt {attempt+1}."
                fixed_code = response.text
            
            # Strip markdown code blocks if present (common LLM behavior)
            if fixed_code.startswith("```"):
                fixed_code = fixed_code.split("\n", 1)[1]
            if fixed_code.endswith("```"):
                fixed_code = fixed_code.rsplit("\n", 1)[0]
            
            # Apply fix
            def _write_fix():
                with open(file_path, "w") as f:
                    f.write(fixed_code)
            await loop.run_in_executor(None, _write_fix)
                
            history.append(f"Attempt {attempt+1}: Fixed code based on error.")
            
        except Exception as e:
            return f"Error during auto-fix generation: {e}"

    return "Unexpected loop exit."

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

    registry.register(
        name="codex_run_and_fix",
        description="Runs a command (test or script) and automatically attempts to fix the code if it fails. Use this for 'run and fix', 'auto-correct', or when you want Freja to autonomously debug.",
        args_schema=RunAndFixSchema,
    )(run_and_fix_impl)
