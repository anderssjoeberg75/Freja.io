import hvac
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

# Vault client instance
_vault_client = None

def get_vault_client():
    global _vault_client
    if _vault_client is not None and _vault_client.is_authenticated():
        return _vault_client

    vault_url = getattr(settings, "VAULT_URL", "http://127.0.0.1:8200")
    vault_token = getattr(settings, "VAULT_TOKEN", "")
    
    try:
        logger.debug(f"[Vault] Attempting connection to {vault_url} with token (len {len(vault_token)})")
        client = hvac.Client(url=vault_url, token=vault_token, verify=False)
        # Suppress urllib3 insecure request warnings for local development
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        if client.is_authenticated():
            logger.debug("[Vault] Client successfully authenticated.")
            _vault_client = client
            return client
        else:
            logger.warning("[Vault] Client connection established but authentication failed.")
    except hvac.exceptions.Unauthorized:
        logger.error("[Vault] Unauthorized - check your VAULT_TOKEN")
    except Exception as e:
        logger.error(f"[Vault] Connection failed: {e}")
    
    return None

def get_vault_secret(key: str, path: str = None) -> str:
    """Read a secret from Vault."""
    client = get_vault_client()
    if not client:
        return ""
    
    mount_point = getattr(settings, "VAULT_MOUNT_POINT", "secret")
    secret_path = path or getattr(settings, "VAULT_SECRET_PATH", "freja")

    try:
        read_response = client.secrets.kv.v2.read_secret_version(
            mount_point=mount_point,
            path=secret_path,
        )
        data = read_response.get("data", {}).get("data", {})
        return data.get(key, "")
    except hvac.exceptions.InvalidPath:
        # Secret path doesn't exist yet, or key not in it
        return ""
    except Exception as e:
        logger.error(f"[Vault] Failed to read secret {key}: {e}")
        return ""

def save_vault_secret(key: str, value: str, path: str = None) -> bool:
    """Save or update a secret in Vault."""
    client = get_vault_client()
    if not client:
        return False

    mount_point = getattr(settings, "VAULT_MOUNT_POINT", "secret")
    secret_path = path or getattr(settings, "VAULT_SECRET_PATH", "freja")

    try:
        # First, read existing to not overwrite other keys
        try:
            read_response = client.secrets.kv.v2.read_secret_version(
                mount_point=mount_point,
                path=secret_path,
            )
            existing_data = read_response.get("data", {}).get("data", {})
        except hvac.exceptions.InvalidPath:
            existing_data = {}

        existing_data[key] = value

        client.secrets.kv.v2.create_or_update_secret(
            mount_point=mount_point,
            path=secret_path,
            secret=existing_data,
        )
        return True
    except Exception as e:
        logger.error(f"[Vault] Failed to save secret {key}: {e}")
        return False

def get_all_vault_secrets(path: str = None) -> dict:
    """Get all secrets stored in Vault."""
    client = get_vault_client()
    if not client:
        return {}
    
    mount_point = getattr(settings, "VAULT_MOUNT_POINT", "secret")
    secret_path = path or getattr(settings, "VAULT_SECRET_PATH", "freja")

    try:
        read_response = client.secrets.kv.v2.read_secret_version(
            mount_point=mount_point,
            path=secret_path,
        )
        return read_response.get("data", {}).get("data", {})
    except hvac.exceptions.InvalidPath:
        return {}
    except Exception as e:
        logger.error(f"[Vault] Failed to read all secrets: {e}")
        return {}
