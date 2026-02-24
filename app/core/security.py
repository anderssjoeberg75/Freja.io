import secrets
from typing import Optional

from fastapi import Header, HTTPException

from app.core.config import get_credential
from app.core.logging import logger


def _extract_bearer_token(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    prefix = "bearer "
    if authorization.lower().startswith(prefix):
        return authorization[len(prefix):].strip()
    return None


def require_admin(
    authorization: Optional[str] = Header(None),
    x_admin_token: Optional[str] = Header(None),
) -> None:
    """FastAPI dependency enforcing admin token access."""
    token = get_credential("ADMIN_API_TOKEN")
    if not token:
        logger.error("ADMIN_API_TOKEN not configured; admin endpoint access denied.")
        raise HTTPException(status_code=503, detail="Admin token not configured.")

    provided = x_admin_token or _extract_bearer_token(authorization)
    if provided:
        provided = provided.strip()
    if not provided or not secrets.compare_digest(provided, token):
        raise HTTPException(status_code=401, detail="Unauthorized")
