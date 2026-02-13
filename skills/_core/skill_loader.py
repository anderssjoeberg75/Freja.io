"""Skill discovery and registration utilities for Freja.io."""

# Section: Imports
from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path
from types import ModuleType
from typing import Dict, Iterable

from app.core.logging import logger
from skills._core.skill_types import SkillManifest


# Section: Loader State
_SKILLS_PACKAGE = "skills"
_IGNORED_SKILL_DIRS = {"_core", "__pycache__"}
_discovered_modules: Dict[str, ModuleType] = {}


# Section: Internal Discovery Helpers
def _iter_skill_names() -> Iterable[str]:
    """Yield importable skill package names from the skills/ directory."""
    skills_path = Path(__file__).resolve().parents[1]
    for module_info in pkgutil.iter_modules([str(skills_path)]):
        if not module_info.ispkg:
            continue
        if module_info.name.startswith("_") or module_info.name in _IGNORED_SKILL_DIRS:
            continue
        yield module_info.name


def _import_skill_module(skill_name: str) -> ModuleType | None:
    """Import a skill package and return the module, or None on import failure."""
    module_path = f"{_SKILLS_PACKAGE}.{skill_name}"
    try:
        return importlib.import_module(module_path)
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.exception("Failed to import skill package {}: {}", module_path, exc)
        return None


# Section: Public Registration APIs
def discover_and_register_skills(registry) -> list[SkillManifest]:
    """Discover all skill packages and register any tool hooks they expose."""
    manifests: list[SkillManifest] = []

    for skill_name in _iter_skill_names():
        module = _discovered_modules.get(skill_name) or _import_skill_module(skill_name)
        if module is None:
            continue

        _discovered_modules[skill_name] = module
        manifest = getattr(module, "SKILL", None)
        if isinstance(manifest, SkillManifest):
            manifests.append(manifest)

        registrar = getattr(module, "register", None)
        if callable(registrar):
            registrar(registry)
            logger.info("Registered skill '{}' tools: {}", skill_name, getattr(manifest, "tools", []))
        else:
            logger.info("Skill '{}' has no tool registry hook.", skill_name)

    return manifests


def register_telegram_handlers(application) -> None:
    """Run optional Telegram handler hooks for all discovered skills."""
    for skill_name in _iter_skill_names():
        module = _discovered_modules.get(skill_name) or _import_skill_module(skill_name)
        if module is None:
            continue

        _discovered_modules[skill_name] = module
        telegram_registrar = getattr(module, "register_telegram", None)
        if callable(telegram_registrar):
            telegram_registrar(application)
            logger.info("Registered Telegram handlers for skill '{}'.", skill_name)
