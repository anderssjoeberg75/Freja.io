import pytest
import asyncio
import json
import sys 
from unittest.mock import AsyncMock, MagicMock, patch
from skills.codex.tools import execute_code_impl, git_operation_impl, audit_code_impl

# --- Tests for Execute Code ---

@pytest.mark.asyncio
async def test_execute_python_code():
    """Test executing python code via mock executor."""
    
    mock_executor = MagicMock()
    mock_executor.run_code.return_value = {"exit_code": 0, "output": "Hello World"}
    
    with patch("app.core.dependencies.get_code_executor", return_value=mock_executor):
        result = await execute_code_impl("python", "print('Hello World')")
        
    data = json.loads(result)
    assert data["exit_code"] == 0
    assert data["output"] == "Hello World"
    mock_executor.run_code.assert_called_once_with("print('Hello World')")

@pytest.mark.asyncio
async def test_execute_shell_command():
    """Test executing shell command via mock executor."""
    
    mock_executor = MagicMock()
    mock_executor.run_command.return_value = {"exit_code": 0, "output": "file.txt"}
    
    with patch("app.core.dependencies.get_code_executor", return_value=mock_executor):
        result = await execute_code_impl("shell", "ls")
        
    data = json.loads(result)
    assert data["output"] == "file.txt"
    mock_executor.run_command.assert_called_once_with("ls")

@pytest.mark.asyncio
async def test_execute_code_no_docker():
    """Test handling of missing docker environment."""
    
    with patch("app.core.dependencies.get_code_executor", return_value=None):
        result = await execute_code_impl("python", "print('fail')")
        
    assert "Error" in result
    assert "Docker" in result

# --- Tests for Git Operations ---

@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_tool_registrations():
    """Test that tools are registered with correct names."""
    from skills.codex.tools import register_tools
    
    # Mock the decorator returned by register
    mock_decorator = MagicMock()
    mock_registry = MagicMock()
    mock_registry.register.return_value = mock_decorator
    
    register_tools(mock_registry)
    
    # Check registrations
    calls = mock_registry.register.call_args_list
    registered_names = [c.kwargs.get("name") for c in calls]
    
    assert "execute_codex_code" in registered_names
    assert "tool_code_executor" in registered_names
    assert "run_code" in registered_names
    assert "codex_git_ops" in registered_names
    assert "codex_audit_codebase" in registered_names
    assert "tool_analyze_code" in registered_names

@pytest.mark.asyncio
async def test_audit_execution_in_docker():
    """Test that audit code is executed inside Docker."""
    mock_executor = MagicMock()
    mock_executor.run_code.return_value = {"exit_code": 0, "output": "Report Generated"}
    
    # Mock code_auditor path and file reading
    with patch("app.core.dependencies.get_code_executor", return_value=mock_executor):
        with patch("builtins.open", new_callable=MagicMock) as mock_open:
            mock_file = MagicMock()
            mock_file.__enter__.return_value.read.return_value = "import foo"
            mock_open.return_value = mock_file
            
            with patch("app.tools.code_auditor.__file__", "/tmp/code_auditor.py"):
                 # Mock import to ensure it doesn't fail
                with patch.dict(sys.modules, {"app.tools.code_auditor": MagicMock(__file__="/tmp/code_auditor.py")}):
                    result = await audit_code_impl()
            
    data = json.loads(result)
    assert data["exit_code"] == 0
    assert data["output"] == "Report Generated"
    
    # Verify run_code was called with script content
    args, _ = mock_executor.run_code.call_args
    assert "import foo" in args[0]
    assert "if __name__ == '__main__':" in args[0]
    assert "run_code_audit()" in args[0]

@pytest.mark.asyncio
async def test_git_clone():
    """Test git clone operation."""
    
    with patch("app.tools.git_core.GitTool.clone_repo", return_value="Cloning into...") as mock_clone:
        result = await git_operation_impl("clone", "http://github.com/repo.git")
        
    assert "Cloning" in result
    mock_clone.assert_called_with("http://github.com/repo.git", None)

@pytest.mark.asyncio
async def test_git_checkout():
    """Test git checkout operation."""
    
    with patch("app.tools.git_core.GitTool.checkout_branch", return_value="Switched to branch") as mock_checkout:
        result = await git_operation_impl("checkout", "feature-branch")
        
    assert "Switched" in result
    mock_checkout.assert_called_with("feature-branch", False)

@pytest.mark.asyncio
async def test_git_status():
    """Test git status operation."""
    
    with patch("app.tools.git_core.GitTool.get_status", return_value="On branch main") as mock_status:
        result = await git_operation_impl("status")
        
    assert "On branch main" in result
    mock_status.assert_called()

# --- Tests for Audit Code ---


