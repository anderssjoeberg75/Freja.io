"""HTTP endpoints for Strava OAuth callback handling."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from skills.strava import get_strava_command_processor

router = APIRouter(tags=["strava"])


# Section: OAuth callback endpoint for Strava connect flow.
@router.get("/api/integrations/strava/callback")
async def strava_callback(
    code: str = Query(..., description="OAuth authorization code"),
    state: str = Query(..., description="Telegram user/chat identifier"),
):
    """Exchange callback code into tokens and persist them for the user represented by `state`."""
    processor = get_strava_command_processor()
    try:
        await processor.auth.exchange_code(state, code)
        return {
            "success": True,
            "message": "Strava connected successfully for this chat.",
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Strava callback failed: {exc}") from exc
