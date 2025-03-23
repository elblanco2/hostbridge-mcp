"""
Base classes for framework handlers.
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional, Type

logger = logging.getLogger("hostbridge.frameworks")

class FrameworkHandler(ABC):
    """
    Abstract base class for framework handlers.
    
    Framework handlers are responsible for:
    1. Creating new projects for a specific framework
    2. Building projects for deployment
    3. Getting framework-specific requirements
    4. Providing configuration templates
    """
    
    @property
    def name(self) -> str:
        """
        Get the name of the framework.
        
        Returns:
            Framework name
        """
        return self.__class__.__name__.replace("FrameworkHandler", "").lower()
    
    @abstractmethod
    def create_project(
        self, 
        project_dir: Path, 
        config: Dict[str, Any]
    ) -> Path:
        """
        Create a new project for this framework.
        
        Args:
            project_dir: Directory where the project should be created
            config: Configuration options for the project
            
        Returns:
            Path to the created project
        """
        pass
    
    @abstractmethod
    def build_project(
        self, 
        project_dir: Path, 
        config: Dict[str, Any]
    ) -> Path:
        """
        Build the project for deployment.
        
        Args:
            project_dir: Path to the project
            config: Build configuration
            
        Returns:
            Path to the build output
        """
        pass
    
    @abstractmethod
    def get_requirements(self) -> Dict[str, Any]:
        """
        Get the requirements for this framework.
        
        Returns:
            Dictionary of requirements information
        """
        pass
    
    def get_configuration_template(self) -> Dict[str, Any]:
        """
        Get a template configuration for this framework.
        
        Returns:
            Dictionary representing a template configuration
        """
        return {
            "app_name": "my-app",
            "template": "basic"
        }
    
    def update_project_config(
        self, 
        project_dir: Path, 
        config: Dict[str, Any]
    ) -> None:
        """
        Update project configuration based on the provided config.
        
        Args:
            project_dir: Path to the project
            config: Configuration updates
        """
        # Default implementation does nothing
        pass

class FrameworkManager:
    """
    Manages framework handlers and provides access to them.
    """
    
    _handlers: Dict[str, Type[FrameworkHandler]] = {}
    
    @classmethod
    def register(cls, name: str, handler_class: Type[FrameworkHandler]) -> None:
        """
        Register a framework handler.
        
        Args:
            name: Name of the framework
            handler_class: Handler class for the framework
        """
        cls._handlers[name.lower()] = handler_class
        logger.info("Registered framework handler: %s", name)
    
    @classmethod
    def get_framework_handler(cls, name: str) -> Optional[FrameworkHandler]:
        """
        Get a framework handler instance by name.
        
        Args:
            name: Name of the framework
            
        Returns:
            Framework handler instance or None if not found
        """
        handler_class = cls._handlers.get(name.lower())
        if not handler_class:
            logger.error("No framework handler registered for: %s", name)
            return None
            
        return handler_class()
    
    @classmethod
    def get_available_frameworks(cls) -> Dict[str, Type[FrameworkHandler]]:
        """
        Get all registered framework handlers.
        
        Returns:
            Dictionary of framework names to handler classes
        """
        return cls._handlers.copy()
