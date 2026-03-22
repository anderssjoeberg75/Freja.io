import subprocess
import os
from typing import List, Optional, Tuple
from app.core.logging import logger

class GitTool:
    """
    Manages Git operations for the project.
    Allows cloning, branching, committing, and pushing code.
    """
    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path

    def _run_git(self, args: List[str]) -> Tuple[bool, str]:
        """Runs a git command in the repo directory."""
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                return True, result.stdout.strip()
            else:
                return False, result.stderr.strip()
        except Exception as e:
            logger.error(f"Git command failed: {e}")
            return False, str(e)

    def clone_repo(self, url: str, dest: Optional[str] = None) -> str:
        """Clones a repository."""
        target = dest or self.repo_path
        if os.path.exists(target) and os.listdir(target):
             return f"Directory {target} is not empty. Skipping clone."
             
        success, output = self._run_git(["clone", url, target])
        return output if success else f"Clone failed: {output}"

    def checkout_branch(self, branch_name: str, create: bool = False) -> str:
        """Checks out a branch, optionally creating it."""
        args = ["checkout"]
        if create:
            args.append("-b")
        args.append(branch_name)
        
        success, output = self._run_git(args)
        return output if success else f"Checkout failed: {output}"

    def commit_changes(self, message: str) -> str:
        """STAGES all changes and commits them."""
        # Stage all
        self._run_git(["add", "."])
        
        # Commit
        success, output = self._run_git(["commit", "-m", message])
        return output if success else f"Commit failed: {output}"

    def push_changes(self, remote: str = "origin", branch: str = "main") -> str:
        """Pushes changes to remote."""
        success, output = self._run_git(["push", remote, branch])
        return output if success else f"Push failed: {output}"
        
    def get_status(self) -> str:
        """Returns git status."""
        success, output = self._run_git(["status"])
        return output if success else "Failed to get status"

    def get_log(self, limit: int = 5) -> str:
        """Returns recent commit log."""
        success, output = self._run_git(["log", f"-n {limit}", "--oneline"])
        return output if success else "Failed to get log"
