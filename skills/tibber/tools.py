"""Tibber tool registrations exposed by the Tibber skill."""

from app.services.tool_registry import ToolRegistry
from app.tools.definitions import GetTibberEnergyAnalysis


def register_tools(registry: ToolRegistry) -> None:
    """Register Tibber tools in the shared tool registry."""

    @registry.register(
        name="get_tibber_energy_analysis",
        description=(
            "Fetches Tibber hourly consumption and price data, summarizes costs and usage patterns, "
            "and returns actionable tips to reduce electricity spending."
        ),
        args_schema=GetTibberEnergyAnalysis,
    )
    async def get_tibber_energy_analysis_impl(days: int = 7) -> str:
        from app.tools.tibber_core import TibberConfigError, get_tibber_energy_analysis

        try:
            return await get_tibber_energy_analysis(days=days)
        except TibberConfigError as exc:
            return f"Tibber integration is not configured: {exc}"
        except Exception as exc:
            return f"Failed to analyze Tibber energy data: {exc}"
