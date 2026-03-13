"""HTTP endpoints for Fitbit OAuth callback handling."""

from fastapi import APIRouter, HTTPException, Query
from app.core.dependencies import get_fitbit
from app.core.config import get_credential

router = APIRouter(tags=["fitbit"])

@router.get("/api/integrations/fitbit/callback")
async def fitbit_callback(
    code: str = Query(..., description="OAuth authorization code"),
    state: str = Query(None, description="State"),
):
    """Exchange callback code into tokens and persist them."""
    fitbit = get_fitbit()
    if not fitbit:
        raise HTTPException(status_code=500, detail="Fitbit tool not initialized")
    
    redirect_uri = get_credential("FITBIT_REDIRECT_URI")
    if not redirect_uri:
        # Fallback
        redirect_uri = "http://localhost:8000/api/integrations/fitbit/callback"

    success, message = await fitbit.exchange_code(code, redirect_uri)
    if success:
        return {
            "success": True,
            "message": "Fitbit connected successfully. You can close this window and refresh Freja.",
        }
    else:
        raise HTTPException(status_code=400, detail=f"Fitbit callback failed: {message}")
