"""Authentication handler for Garmin Connect using garth library."""

import logging
import os
from pathlib import Path
from typing import Any

import garth
from garth.exc import GarthException, GarthHTTPError

# Import project configuration
from app.core.config import get_credential, BASE_DIR

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Raised when authentication with Garmin Connect fails."""
    pass


class SessionExpiredError(AuthenticationError):
    """Raised when the Garmin Connect session has expired."""
    pass


class GarminAuth:
    """
    Handle Garmin Connect authentication.
    
    Uses the garth library for OAuth-based authentication with Garmin Connect.
    Supports saving and loading session tokens for persistent authentication.
    """

    def __init__(
        self,
        token_dir: Path | str | None = None,
    ):
        """
        Initialize the authentication handler.
        
        Args:
            token_dir: Directory to store authentication tokens.
                      Defaults to project's config/garmin_tokens
        """
        if token_dir:
            self.token_dir = Path(token_dir)
        else:
            self.token_dir = Path(BASE_DIR) / "db" / "tokens" / "garmin_tokens"
            
        self._is_authenticated = False

    @property
    def is_authenticated(self) -> bool:
        """Check if currently authenticated."""
        return self._is_authenticated

    def login(self, email: str | None = None, password: str | None = None, save_tokens: bool = True) -> bool:
        """
        Authenticate with Garmin Connect using email and password.
        
        If email/password not provided, tries to fetch from credentials.
        
        Args:
            email: Garmin Connect email address
            password: Garmin Connect password
            save_tokens: Whether to save tokens for future use
            
        Returns:
            True if authentication was successful
            
        Raises:
            AuthenticationError: If authentication fails
        """
        email = email or get_credential("GARMIN_EMAIL")
        password = password or get_credential("GARMIN_PASSWORD")
        
        if not email or not password:
            logger.error("[GARMIN] Missing credentials.")
            raise AuthenticationError("Missing Garmin credentials (email/password).")

        try:
            masked_email = email[:3] + "***" if email else "None"
            logger.info(f"[GARMIN] Attempting to log in as {masked_email} using garminconnect library...")
            
            # Use garminconnect library for login as it handles Cloudflare/SSO better
            from garminconnect import Garmin
            
            # Initialize Garmin client
            # We don't save the client itself, just use it to get tokens
            gc_client = Garmin(email, password)
            gc_client.login()
            
            logger.info("[GARMIN] garminconnect login successful. Saving tokens...")
            
            # Save tokens from the garminconnect's internal garth client
            # Ensure directory exists
            self.token_dir.mkdir(parents=True, exist_ok=True)
            gc_client.garth.dump(str(self.token_dir))
            
            # Now configure our global garth instance from these saved tokens
            garth.configure(domain="garmin.com")
            garth.load(str(self.token_dir))
            
            self._is_authenticated = True
            logger.info("[GARMIN] Successfully configured global garth client via garminconnect tokens")

            return True

        except Exception as e:
            logger.error(f"[GARMIN] Login failed: {e}")
            raise AuthenticationError(f"Failed to authenticate: {e}") from e

    def save_tokens(self) -> None:
        """
        Save authentication tokens to disk.
        """
        try:
            self.token_dir.mkdir(parents=True, exist_ok=True)
            garth.save(str(self.token_dir))
            logger.info(f"[GARMIN] Saved authentication tokens to {self.token_dir}")
        except Exception as e:
            logger.warning(f"[GARMIN] Failed to save tokens: {e}")

    def load_tokens(self) -> bool:
        """
        Load authentication tokens from disk.
        
        Returns:
            True if tokens were loaded successfully and are valid
        """
        if not self.token_dir.exists():
            logger.debug(f"[GARMIN] No token directory found at {self.token_dir}")
            return False

        try:
            garth.configure(domain="garmin.com")
            garth.resume(str(self.token_dir))
            # Verify we are actually logged in by checking username
            if garth.client.username:
                self._is_authenticated = True
                logger.info("[GARMIN] Successfully loaded authentication tokens")
                return True
            return False
        except GarthException as e:
            logger.warning(f"[GARMIN] Failed to load tokens: {e}")
            return False
        except Exception as e:
            logger.warning(f"[GARMIN] Unexpected error loading tokens: {e}")
            return False

    def ensure_authenticated(self) -> None:
        """
        Ensure we have valid authentication.
        
        First tries to load saved tokens, then raises an error if not authenticated.
        """
        if self._is_authenticated:
            return

        if self.load_tokens():
            return
            
        # Try auto-login if credentials exist
        try:
            if self.login():
                return
        except:
            pass

        raise AuthenticationError(
            "Not authenticated. Please call login() with your credentials first."
        )

    @property
    def client(self) -> garth.Client:
        """
        Get the underlying garth client for direct API calls.
        """
        self.ensure_authenticated()
        return garth.client
