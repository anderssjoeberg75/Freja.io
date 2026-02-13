"""Shared pytest configuration for Freja.io test suite."""

# Section: Imports
import sys
from pathlib import Path


# Section: Python Path Bootstrap
# Ensure repository root is importable when pytest is executed from different working dirs.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
