"""Google Calendar module."""

from .tools import register_tools

def register(registry) -> None:
    register_tools(registry)
