"""Core type contracts for Freja skill plugins."""

# Section: Imports
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


# Section: Skill Metadata Contract
@dataclass(frozen=True)
class SkillManifest:
    """Structured metadata that each skill exposes for discovery and introspection."""

    name: str
    description: str
    version: str
    tools: list[str] = field(default_factory=list)
    telegram_commands: list[str] = field(default_factory=list)


# Section: Optional Protocol Helpers
class RegistryRegistrar(Protocol):
    """Protocol for modules exposing register(registry)."""

    def __call__(self, registry) -> None:  # pragma: no cover - protocol typing only
        ...


class TelegramRegistrar(Protocol):
    """Protocol for modules exposing register_telegram(application)."""

    def __call__(self, application) -> None:  # pragma: no cover - protocol typing only
        ...
