import asyncio
import json
import httpx
from typing import Optional, Literal
from pydantic import BaseModel, Field

from app.core import dependencies
from app.services.tool_registry import ToolRegistry
from skills.codex.git_core import GitTool


# --- Tool Schemas ---

class AuditAndFixSchema(BaseModel):
    base_branch: str = Field("main", description="Branch to base the fix on.")
    pr_title: str = Field("Auto-fix: Critical findings", description="Title for the pull request.")
    pr_body: str = Field("Automated fix for critical findings detected by audit.", description="Body for the pull request.")

async def audit_and_fix_impl(base_branch: str = "main", pr_title: str = "Auto-fix: Critical findings", pr_body: str = "Automated fix for critical findings detected by audit.") -> str:
    """
    Kör audit, identifierar kritiska findings, försöker auto-fixa, testar, kör statisk analys, committar och pushar till ny branch, och skapar PR via GitHub API.
    """
    import os
    import re
    import uuid
    import subprocess
    import httpx
    from app.core.config import get_credential, settings
    loop = asyncio.get_event_loop()
    executor = dependencies.get_code_executor()
    if not executor:
        return "Error: Code Execution environment not available."

    # 1. Kör audit (självanalys)
    audit_cmd = "python3 skills/codex/auditor.py"
    audit_result = await loop.run_in_executor(None, executor.run_command, audit_cmd)
    output = audit_result.get("output", "")
    # 2. Identifiera kritiska findings (🔴 eller 'Kritiskt:')
    critical = re.findall(r"🔴|Kritiskt:", output)
    if not critical:
        return "✅ Ingen kritisk issue hittad vid audit."

    # 3. Generera fix med LLM (använd run_and_fix_impl på de filer som nämns i findings)
    # För demo: försök auto-fixa alla .py-filer som nämns i rapporten efter 🔴
    files_to_fix = set(re.findall(r"FIL: ([^\s]+\.py)", output))
    fix_results = []
    for file_path in files_to_fix:
        # Kör run_and_fix_impl för varje fil
        fix_result = await run_and_fix_impl(f"pytest {file_path}", file_path, max_retries=2)
        fix_results.append(f"{file_path}: {fix_result}")

    # 4. Kör tester (pytest)
    test_result = await loop.run_in_executor(None, executor.run_command, "pytest --maxfail=1 --disable-warnings")
    if test_result.get("exit_code", 1) != 0:
        return f"❌ Tester misslyckades efter fix: {test_result.get('output','')}"

    # 5. Kör statisk analys (flake8)
    static_result = await static_analysis_impl(tool="flake8", path=".")
    if "No issues found" not in static_result:
        return f"❌ Statisk analys misslyckades: {static_result}"

    # 6. Skapa ny branch, commit, push
    branch_name = f"auto-fix-{uuid.uuid4().hex[:8]}"
    git_tool = __import__("skills.codex.git_core", fromlist=["GitTool"]).GitTool()
    await loop.run_in_executor(None, git_tool._run_git, ["checkout", base_branch])
    await loop.run_in_executor(None, git_tool._run_git, ["pull"])
    await loop.run_in_executor(None, git_tool._run_git, ["checkout", "-b", branch_name])
    await loop.run_in_executor(None, git_tool._run_git, ["add", "."])
    await loop.run_in_executor(None, git_tool._run_git, ["commit", "-m", pr_title])
    await loop.run_in_executor(None, git_tool._run_git, ["push", "-u", "origin", branch_name])

    # 7. Skapa PR via GitHub API
    github_token = get_credential("GITHUB_TOKEN") or getattr(settings, "GITHUB_TOKEN", None)
    repo_url = os.environ.get("GITHUB_REPO") or getattr(settings, "GITHUB_REPO", None)
    if not github_token or not repo_url:
        return f"Fix och push klar på branch {branch_name}, men PR kunde inte skapas (saknar GITHUB_TOKEN eller GITHUB_REPO)."
    owner_repo = repo_url.split("github.com/")[-1].replace(".git", "")
    api_url = f"https://api.github.com/repos/{owner_repo}/pulls"
    headers = {"Authorization": f"token {github_token}", "Accept": "application/vnd.github+json"}
    pr_data = {"title": pr_title, "head": branch_name, "base": base_branch, "body": pr_body}
    async with httpx.AsyncClient() as client:
        resp = await client.post(api_url, headers=headers, json=pr_data)
        if resp.status_code == 201:
            pr_url = resp.json().get("html_url", "")
            return f"✅ Fix klar och PR skapad: {pr_url}\n\nFixade filer: {', '.join(files_to_fix)}\nTestresultat: OK\nStatisk analys: OK"
        else:
            return f"Fix och push klar på branch {branch_name}, men PR kunde inte skapas: {resp.text}"
class StaticAnalysisSchema(BaseModel):
    tool: Literal["flake8", "ruff"] = Field("flake8", description="Which static analysis tool to use.")
    path: str = Field(".", description="Path to analyze (default: project root)")

async def static_analysis_impl(tool: str = "flake8", path: str = ".") -> str:
    """Runs static code analysis (flake8 or ruff) in the Docker sandbox."""
    executor = dependencies.get_code_executor()
    if not executor:
        return "Error: Code Execution environment not available."
    loop = asyncio.get_event_loop()
    if tool == "ruff":
        cmd = f"ruff {path} --format=github"
    else:
        cmd = f"flake8 {path} --format=default"
    result = await loop.run_in_executor(None, executor.run_command, cmd)
    output = result.get("output", "")
    if not output.strip():
        return f"✅ No issues found by {tool}."
    return f"{tool} output:\n{output}"
# --- Additional Schemas ---

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
        import subprocess
        
        # Uppdatera från GitHub innan analysen så att vi alltid analyserar senaste filerna
        try:
            print("[AUDIT] Drar senaste koden från GitHub innan analys...")
            pull_result = subprocess.run(
                ["git", "pull"],
                cwd=executor.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            print(f"[AUDIT] Git pull lyckades: {pull_result.stdout.strip()}")
        except subprocess.CalledProcessError as e:
            print(f"[AUDIT] Varning: Git pull misslyckades. Analyserar lokala filer istället. Fel: {e.stderr.strip()}")
            
        # Fetch config safely
        from app.core.database import get_db_settings_sync
        settings_dict = get_db_settings_sync()
        codex_model = settings_dict.get("CODEX_MODEL", "gemini-2.0-flash")
        ollama_url = settings_dict.get("OLLAMA_URL", "http://host.docker.internal:11434")
            
        cmd = f"sh -c \"OLLAMA_URL='{ollama_url}' CODEX_MODEL='{codex_model}' python3 skills/codex/auditor.py\""
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
                        # Chat service sent a message, we only need to provide the document
                        await telegram_service.send_document(host_path, caption=f"Självanalys Rapport ({codex_model})")
                except Exception as e:
                    print(f"Telegram notification failed: {e}")
                
                # If we are in a telegram context, we should not return the full text to the chat_service.
                # However, tools.py doesn't know the context directly here easily, so we still return
                # the full file content, and rely on chat_service.py to TRUNCATE it for Telegram users.
                try:
                    with open(host_path, "r", encoding="utf-8") as f:
                        file_content = f.read()
                    return f"✅ Självanalysklar! Här är den fullständiga rapporten:\n\n{file_content}"
                except Exception as e:
                    return f"Kunde läsa filen men fick ett fel vid inläsning: {e}\n\nSammanfattning:\n{output}"
            else:
                print(f"Error: generated file {host_path} not found on host (Bind mount issue?)")

        return output
        
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
        name="codex_audit_and_fix",
        description="Performs audit, auto-fixes critical findings, tests, runs static analysis, and creates a pull request.",
        args_schema=AuditAndFixSchema,
    )(audit_and_fix_impl)

    registry.register(
        name="codex_static_analysis",
        description="Runs static code analysis (flake8 or ruff) in the Docker sandbox.",
        args_schema=StaticAnalysisSchema,
    )(static_analysis_impl)

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
        description="Analyzes the Freja codebase for bugs and improvements. Use this when the user asks for 'självanalys', 'själv analys', 'self-analysis', 'self analysis', or 'analyze code'. DO NOT search the web for this.",
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
