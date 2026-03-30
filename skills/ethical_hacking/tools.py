"""Ethical hacking tool registrations exposed by the ethical hacking skill."""

from app.services.tool_registry import ToolRegistry
from skills._core.definitions import RunPentestRecon


def register_tools(registry: ToolRegistry) -> None:
    """Register ethical hacking tools in the shared tool registry."""

    @registry.register(
        name="run_pentest_recon",
        description=(
            "Runs authorized pentest reconnaissance by scanning TCP ports and checking "
            "web security headers/TLS indicators for common vulnerabilities."
        ),
        args_schema=RunPentestRecon,
    )
    async def run_pentest_recon_impl(
        target: str,
        ports: str = "1-1024",
        timeout_seconds: float = 0.5,
        include_web_checks: bool = True,
    ) -> str:
        from skills.ethical_hacking.core import run_pentest_recon

        try:
            return await run_pentest_recon(
                target=target,
                ports=ports,
                timeout_seconds=timeout_seconds,
                include_web_checks=include_web_checks,
            )
        except Exception as exc:
            return f"Pentest recon failed: {exc}"
