"""Codex skill package."""

from skills._core.skill_types import SkillManifest
from skills.codex.tools import register_tools

SKILL = SkillManifest(
    name="codex",
    description="Advanced coding and self-evolution capabilities.",
    version="1.0.0",
    tools=["execute_codex_code", "codex_git_ops", "codex_audit_codebase"],
)

def register(registry) -> None:
    """Register Codex tools."""
    register_tools(registry)

__all__ = ["SKILL", "register"]
