"""Legacy LLM service compatibility layer used by regression tests."""

from __future__ import annotations

from typing import Any


async def generate_response(prompt: str, history: list[dict[str, Any]] | None = None) -> str:
    """Generate a minimal response while keeping safe default arguments."""
    _history = history or []
    del _history
    return f"LLM service placeholder response for: {prompt}"
