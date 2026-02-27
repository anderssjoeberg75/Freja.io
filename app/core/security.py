import secrets
from typing import Optional

from fastapi import Header, HTTPException, Request

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


def check_ip_allowlist(request: Request) -> None:
    """
    Check if the client's IP is in the ALLOWED_IPS list.
    Localhost is always allowed.
    """
    allowed_ips_str = get_credential("ALLOWED_IPS")
    if not allowed_ips_str:
        return

    client_ip = request.client.host
    if client_ip in ("127.0.0.1", "::1"):
        return

    allowed_ips = [ip.strip() for ip in allowed_ips_str.split(",") if ip.strip()]
    if not allowed_ips:
        return

    if client_ip not in allowed_ips:
        logger.warning(f"Access denied for IP: {client_ip}")
        raise HTTPException(status_code=403, detail="Access denied: IP not allowed.")
