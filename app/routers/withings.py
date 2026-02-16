"""HTTP endpoints for Withings OAuth callback handling."""

from fastapi import APIRouter, HTTPException, Query
from app.core.dependencies import get_withings
from app.core.config import get_credential

router = APIRouter(tags=["withings"])

@router.get("/api/integrations/withings/callback")
async def withings_callback(
    code: str = Query(..., description="OAuth authorization code"),
    state: str = Query(None, description="State (not strictly used here but good for OAuth)"),
):
    """Exchange callback code into tokens and persist them."""
    withings = get_withings()
    if not withings:
        raise HTTPException(status_code=500, detail="Withings tool not initialized")
    
    # We need the redirect_uri that was used in the authorize call.
    # We can try to derive it from the Strava settings or a default.
    redirect_uri = get_credential("WITHINGS_REDIRECT_URI")
    if not redirect_uri:
        # Fallback to a common pattern if not set
        redirect_uri = "http://localhost:8000/api/integrations/withings/callback"

    success, message = withings.exchange_code(code, redirect_uri)
    if success:
        return {
            "success": True,
            "message": "Withings connected successfully.",
        }
    else:
        raise HTTPException(status_code=400, detail=f"Withings callback failed: {message}")
