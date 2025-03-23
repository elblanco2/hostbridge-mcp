"""
Base classes for hosting provider implementations.
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger("hostbridge.providers")

class HostingProvider(ABC):
    """
    Abstract base class for hosting provider implementations.
    
    All hosting providers must implement these methods to provide
    a consistent interface for deployment operations.
    """
    
    @property
    def name(self) -> str:
        """
        Get the name of the hosting provider.
        
        Returns:
            Provider name
        """
        return self.__class__.__name__.replace("Provider", "").lower()
    
    @abstractmethod
    def check_status(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check the status of the hosting provider.
        
        Args:
            credentials: Provider-specific credentials
            
        Returns:
            Status information as a dictionary
        """
        pass
    
    @abstractmethod
    def deploy(
        self, 
        credentials: Dict[str, Any], 
        build_path: Path, 
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Deploy a built application to the hosting provider.
        
        Args:
            credentials: Provider-specific credentials
            build_path: Path to the built application
            config: Deployment configuration
            
        Returns:
            Deployment result information
        """
        pass
    
    @abstractmethod
    def get_requirements(self) -> Dict[str, Any]:
        """
        Get the requirements for this hosting provider.
        
        Returns:
            Dictionary of requirements information
        """
        pass

class HostingProviderFactory:
    """
    Factory for creating hosting provider instances.
    """
    
    _providers = {}
    
    @classmethod
    def register(cls, provider_name: str, provider_class: type):
        """
        Register a hosting provider class.
        
        Args:
            provider_name: Name of the provider
            provider_class: Provider class to register
        """
        cls._providers[provider_name.lower()] = provider_class
        logger.info("Registered hosting provider: %s", provider_name)
    
    @classmethod
    def get_provider(cls, provider_name: str) -> Optional[HostingProvider]:
        """
        Get a hosting provider instance by name.
        
        Args:
            provider_name: Name of the provider
            
        Returns:
            Provider instance or None if not found
        """
        provider_class = cls._providers.get(provider_name.lower())
        if not provider_class:
            logger.error("No provider registered with name: %s", provider_name)
            return None
            
        return provider_class()
    
    @classmethod
    def get_available_providers(cls) -> Dict[str, type]:
        """
        Get all registered provider classes.
        
        Returns:
            Dictionary of provider names to provider classes
        """
        return cls._providers.copy()
