"""
Secure credentials management for hosting providers.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Optional, Any

# Optional keyring support for more secure credential storage
try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False

logger = logging.getLogger("hostbridge.credentials")

class CredentialsManager:
    """
    Manages secure storage and retrieval of hosting provider credentials.
    
    This class provides two storage backends:
    1. File-based: Credentials stored in JSON files (less secure)
    2. Keyring: Credentials stored in the system's secure storage (more secure)
    """
    
    def __init__(self, secure_storage_path: str, use_keyring: bool = True):
        """
        Initialize the credentials manager.
        
        Args:
            secure_storage_path: Path where credentials will be stored (if using file-based storage)
            use_keyring: Whether to use the system keyring for credential storage (if available)
        """
        self.secure_storage_path = Path(os.path.expanduser(secure_storage_path))
        self.use_keyring = use_keyring and KEYRING_AVAILABLE
        
        # Create storage directory if it doesn't exist
        if not self.use_keyring:
            self.secure_storage_path.mkdir(parents=True, exist_ok=True)
            
        logger.info(
            "Credentials manager initialized with %s storage", 
            "keyring" if self.use_keyring else "file-based"
        )
    
    def store_credentials(self, provider: str, credentials: Dict[str, Any]) -> bool:
        """
        Store credentials for a hosting provider.
        
        Args:
            provider: Name of the hosting provider
            credentials: Dictionary of credentials to store
            
        Returns:
            True if storage was successful, False otherwise
        """
        try:
            if self.use_keyring:
                # Use system keyring
                keyring.set_password(
                    "hostbridge", 
                    f"provider_{provider}",
                    json.dumps(credentials)
                )
            else:
                # Use file-based storage
                provider_file = self.secure_storage_path / f"{provider}.json"
                with open(provider_file, "w") as f:
                    json.dump(credentials, f)
                    
                # Set restrictive permissions on the file
                os.chmod(provider_file, 0o600)
                
            logger.info("Stored credentials for provider: %s", provider)
            return True
        except Exception as e:
            logger.error("Failed to store credentials for provider %s: %s", provider, str(e))
            return False
    
    def get_credentials(self, provider: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve credentials for a hosting provider.
        
        Args:
            provider: Name of the hosting provider
            
        Returns:
            Dictionary of credentials if available, None otherwise
        """
        try:
            if self.use_keyring:
                # Use system keyring
                credentials_json = keyring.get_password("hostbridge", f"provider_{provider}")
                if credentials_json:
                    return json.loads(credentials_json)
                return None
            else:
                # Use file-based storage
                provider_file = self.secure_storage_path / f"{provider}.json"
                if not provider_file.exists():
                    return None
                    
                with open(provider_file, "r") as f:
                    return json.load(f)
        except Exception as e:
            logger.error("Failed to retrieve credentials for provider %s: %s", provider, str(e))
            return None
    
    def delete_credentials(self, provider: str) -> bool:
        """
        Delete credentials for a hosting provider.
        
        Args:
            provider: Name of the hosting provider
            
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            if self.use_keyring:
                # Use system keyring
                keyring.delete_password("hostbridge", f"provider_{provider}")
            else:
                # Use file-based storage
                provider_file = self.secure_storage_path / f"{provider}.json"
                if provider_file.exists():
                    provider_file.unlink()
                    
            logger.info("Deleted credentials for provider: %s", provider)
            return True
        except Exception as e:
            logger.error("Failed to delete credentials for provider %s: %s", provider, str(e))
            return False
    
    def list_providers(self) -> list[str]:
        """
        List all providers with stored credentials.
        
        Returns:
            List of provider names
        """
        try:
            if self.use_keyring:
                # TODO: Keyring doesn't provide a standard way to list all items
                # This is a limitation of using keyring
                logger.warning("Listing providers is not supported with keyring storage")
                return []
            else:
                # Use file-based storage
                return [
                    f.stem for f in self.secure_storage_path.glob("*.json")
                    if f.is_file()
                ]
        except Exception as e:
            logger.error("Failed to list providers: %s", str(e))
            return []
