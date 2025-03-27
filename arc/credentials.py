"""
Credentials management for Arc.

This module provides secure storage and retrieval of credentials
for various hosting providers.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, Union

logger = logging.getLogger("arc.credentials")

class CredentialsManager:
    """
    Manage credentials for hosting providers.
    
    This class provides secure storage and retrieval of credentials.
    """
    
    def __init__(self, storage_path: str):
        """
        Initialize the credentials manager.
        
        Args:
            storage_path: Path to store credentials
        """
        self.storage_path = Path(storage_path)
        self._ensure_storage_path()
    
    def _ensure_storage_path(self):
        """Ensure the storage directory exists."""
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create storage directory: {e}")
            raise
    
    def store_credentials(self, provider: str, credentials: Dict[str, str]) -> bool:
        """
        Store credentials for a provider.
        
        Args:
            provider: The hosting provider
            credentials: Provider-specific credentials
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Normalize provider name
            provider = provider.lower().replace("-", "_")
            
            # Validate required credentials
            required_fields = self._get_required_fields(provider)
            for field in required_fields:
                if field not in credentials:
                    logger.error(f"Missing required credential '{field}' for provider '{provider}'")
                    return False
            
            # Create credentials file
            credentials_file = self.storage_path.with_suffix(f".{provider}")
            
            # Write credentials
            with open(credentials_file, "w") as f:
                json.dump(credentials, f)
            
            # Secure the file permissions (unix-like systems only)
            if os.name == "posix":
                os.chmod(credentials_file, 0o600)
            
            logger.info(f"Stored credentials for {provider}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store credentials: {e}")
            return False
    
    def get_credentials(self, provider: str) -> Optional[Dict[str, str]]:
        """
        Retrieve credentials for a provider.
        
        Args:
            provider: The hosting provider
            
        Returns:
            Credentials dictionary or None if not found
        """
        try:
            # Normalize provider name
            provider = provider.lower().replace("-", "_")
            
            # Check if credentials file exists
            credentials_file = self.storage_path.with_suffix(f".{provider}")
            if not credentials_file.exists():
                logger.warning(f"No credentials found for {provider}")
                return None
            
            # Read credentials
            with open(credentials_file, "r") as f:
                credentials = json.load(f)
            
            return credentials
            
        except Exception as e:
            logger.error(f"Failed to retrieve credentials: {e}")
            return None
    
    def delete_credentials(self, provider: str) -> bool:
        """
        Delete credentials for a provider.
        
        Args:
            provider: The hosting provider
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Normalize provider name
            provider = provider.lower().replace("-", "_")
            
            # Check if credentials file exists
            credentials_file = self.storage_path.with_suffix(f".{provider}")
            if not credentials_file.exists():
                logger.warning(f"No credentials found for {provider}")
                return False
            
            # Delete credentials file
            credentials_file.unlink()
            
            logger.info(f"Deleted credentials for {provider}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete credentials: {e}")
            return False
    
    def _get_required_fields(self, provider: str) -> list:
        """
        Get required credential fields for a provider.
        
        Args:
            provider: The hosting provider
            
        Returns:
            List of required field names
        """
        # Define required fields for each provider
        provider_fields = {
            "netlify": ["access_token"],
            "vercel": ["access_token"],
            "shared_hosting": ["host", "username", "password"],
            "hostm": ["api_key"]
        }
        
        return provider_fields.get(provider, [])
