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
    vault_verify = getattr(settings, "VAULT_VERIFY", None)
    
    if vault_verify is None:
        # Auto-detect: disable verification for localhost/127.0.0.1
        if "127.0.0.1" in vault_url or "localhost" in vault_url:
            vault_verify = False
        else:
            vault_verify = True
    
    # Ensure it's a boolean (pydantic might load it as string from .env)
    if isinstance(vault_verify, str):
        vault_verify = vault_verify.lower() in ("true", "1", "yes", "on")
            
    import time
    for attempt in range(3):
        try:
            logger.debug(f"[Vault] Attempting connection to {vault_url} with token (len {len(vault_token)}) and verify={vault_verify} (Attempt {attempt+1}/3)")
            client = hvac.Client(url=vault_url, token=vault_token, verify=vault_verify)
            if not vault_verify:
                # Suppress urllib3 insecure request warnings for local development
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            if client.is_authenticated():
                logger.debug("[Vault] Client successfully authenticated.")
                _vault_client = client
                return client
            else:
                logger.warning("[Vault] Client connection established but authentication failed.")
                break
        except hvac.exceptions.Unauthorized:
            logger.error("[Vault] Unauthorized - check your VAULT_TOKEN")
            break
        except Exception as e:
            logger.error(f"[Vault] Connection failed: {e}")
            if attempt < 2:
                time.sleep(1)
            else:
                logger.error("[Vault] All connection attempts exhausted.")
    
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
def delete_vault_secret(key: str, path: str = None) -> bool:
    """Remove a specific key from a Vault secret path."""
    client = get_vault_client()
    if not client:
        return False

    mount_point = getattr(settings, "VAULT_MOUNT_POINT", "secret")
    secret_path = path or getattr(settings, "VAULT_SECRET_PATH", "freja")

    try:
        # Read existing
        read_response = client.secrets.kv.v2.read_secret_version(
            mount_point=mount_point,
            path=secret_path,
        )
        existing_data = read_response.get("data", {}).get("data", {})
        
        if key in existing_data:
            del existing_data[key]
            
            client.secrets.kv.v2.create_or_update_secret(
                mount_point=mount_point,
                path=secret_path,
                secret=existing_data,
            )
            return True
        return True # Already gone
    except hvac.exceptions.InvalidPath:
        return True # Path doesn't exist, so key is "deleted"
    except Exception as e:
        logger.error(f"[Vault] Failed to delete secret {key}: {e}")
        return False
