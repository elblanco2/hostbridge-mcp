"""
Wasp framework handler implementation.

This handler supports creating and building Wasp applications
(https://wasp-lang.dev/).
"""

import logging
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional

from .base import FrameworkHandler, FrameworkManager

logger = logging.getLogger("hostbridge.frameworks.wasp")

class WaspFrameworkHandler(FrameworkHandler):
    """
    Handler for Wasp framework applications.
    
    Wasp is a full-stack framework for building web applications with
    less code. It uses a declarative language to define models, routes,
    and more.
    """
    
    def create_project(
        self, 
        project_dir: Path, 
        config: Dict[str, Any]
    ) -> Path:
        """
        Create a new Wasp project.
        
        Args:
            project_dir: Directory where the project should be created
            config: Configuration options including:
                - app_name: Name of the application
                - template: Template to use (basic, with-auth, todo)
                - include_auth: Whether to include authentication
                
        Returns:
            Path to the created project
        """
        app_name = config.get("app_name")
        if not app_name:
            raise ValueError("app_name is required for creating a Wasp project")
        
        template = config.get("template", "basic")
        include_auth = config.get("include_auth", False)
        
        # Build command for wasp new
        cmd = ["wasp", "new", app_name]
        
        # Add template if it's not the default
        if template != "basic":
            cmd.extend(["--template", template])
        
        # Add auth if requested and not already in template
        if include_auth and template != "with-auth":
            cmd.extend(["--with-auth"])
        
        logger.info("Creating Wasp project: %s", " ".join(cmd))
        
        try:
            # Execute command
            result = subprocess.run(
                cmd, 
                cwd=project_dir,
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.debug("Wasp project creation output: %s", result.stdout)
            
            # Update project configuration if needed
            app_dir = project_dir / app_name
            self.update_project_config(app_dir, config)
            
            return app_dir
        except subprocess.CalledProcessError as e:
            logger.error("Failed to create Wasp project: %s", e.stderr)
            raise ValueError(f"Failed to create Wasp project: {e.stderr}")
    
    def build_project(
        self, 
        project_dir: Path, 
        config: Dict[str, Any]
    ) -> Path:
        """
        Build the Wasp project for deployment.
        
        Args:
            project_dir: Path to the project
            config: Build configuration including:
                - env_vars: Environment variables for the build
                
        Returns:
            Path to the build output
        """
        # Apply any environment variables for the build
        env_vars = config.get("env_vars", {})
        env = dict(subprocess.check_output(["env"], universal_newlines=True).splitlines(), 
                  **env_vars)
        
        logger.info("Building Wasp project at: %s", project_dir)
        
        try:
            # Run wasp build
            result = subprocess.run(
                ["wasp", "build"],
                cwd=project_dir,
                env=env,
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.debug("Wasp build output: %s", result.stdout)
            
            # Return path to build output
            build_path = project_dir / ".wasp" / "build"
            if not build_path.exists():
                raise ValueError("Build directory not found after build")
                
            return build_path
        except subprocess.CalledProcessError as e:
            logger.error("Failed to build Wasp project: %s", e.stderr)
            raise ValueError(f"Failed to build Wasp project: {e.stderr}")
    
    def update_project_config(
        self, 
        project_dir: Path, 
        config: Dict[str, Any]
    ) -> None:
        """
        Update the Wasp project configuration.
        
        Args:
            project_dir: Path to the project
            config: Configuration updates including:
                - database_type: Type of database to use
                - app_name: Application name
                - app_title: Application title
        """
        main_wasp_path = project_dir / "main.wasp"
        if not main_wasp_path.exists():
            logger.warning("main.wasp not found at %s", main_wasp_path)
            return
            
        try:
            # Read existing config
            with open(main_wasp_path, "r") as f:
                content = f.read()
                
            # Apply database configuration
            db_type = config.get("database_type", "sqlite")
            if db_type.lower() == "postgresql" and "db: {" not in content:
                with open(main_wasp_path, "a") as f:
                    f.write('\ndb: { provider: "postgresql", url: env("DATABASE_URL") }\n')
                    
            # Apply app title change if provided
            app_title = config.get("app_title")
            if app_title:
                # Look for existing title
                title_pattern = r'title:\s*"([^"]+)"'
                if re.search(title_pattern, content):
                    # Replace existing title
                    content = re.sub(
                        title_pattern,
                        f'title: "{app_title}"',
                        content
                    )
                else:
                    # Look for app declaration
                    app_pattern = r'app\s+\w+\s*{([^}]*)}'
                    if re.search(app_pattern, content):
                        # Insert title into app declaration
                        content = re.sub(
                            app_pattern,
                            lambda m: m.group(0).replace(
                                '{',
                                '{\n  title: "' + app_title + '",',
                                1
                            ),
                            content
                        )
                    
                    # Write updated content
                    with open(main_wasp_path, "w") as f:
                        f.write(content)
            
            # Apply other configurations
            # Add custom NPM dependencies if specified
            npm_dependencies = config.get("npm_dependencies", {})
            if npm_dependencies:
                package_json_path = project_dir / "package.json"
                if package_json_path.exists():
                    # Update package.json
                    import json
                    with open(package_json_path, "r") as f:
                        package_data = json.load(f)
                    
                    # Update dependencies
                    if "dependencies" not in package_data:
                        package_data["dependencies"] = {}
                    
                    package_data["dependencies"].update(npm_dependencies)
                    
                    # Write updated package.json
                    with open(package_json_path, "w") as f:
                        json.dump(package_data, f, indent=2)
                    
                    # Install dependencies
                    try:
                        subprocess.run(
                            ["npm", "install"],
                            cwd=project_dir,
                            capture_output=True,
                            check=True
                        )
                    except subprocess.CalledProcessError:
                        logger.warning("Failed to install NPM dependencies")
            
        except Exception as e:
            logger.warning("Failed to update Wasp project configuration: %s", str(e))
    
    def get_requirements(self) -> Dict[str, Any]:
        """
        Get the requirements for Wasp.
        
        Returns:
            Dictionary of requirements information
        """
        # Try to determine installed Wasp version
        wasp_version = "unknown"
        try:
            result = subprocess.run(
                ["wasp", "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            wasp_version = result.stdout.strip()
        except:
            pass
        
        return {
            "required": [
                f"wasp-cli >={wasp_version or '0.11.0'}",
                "node >= 16.0.0",
                "npm >= 6.0.0"
            ],
            "optional": [
                "postgresql",
                "sqlite"
            ],
            "resources": {
                "minimal": {
                    "memory": "512MB",
                    "cpu": "0.5",
                    "storage": "1GB"
                },
                "recommended": {
                    "memory": "1GB",
                    "cpu": "1.0",
                    "storage": "5GB"
                }
            },
            "templates": {
                "basic": "Simple starter project",
                "with-auth": "Project with user authentication",
                "todo": "Todo list application example"
            }
        }
    
    def get_configuration_template(self) -> Dict[str, Any]:
        """
        Get a template configuration for Wasp.
        
        Returns:
            Dictionary representing a template configuration
        """
        return {
            "app_name": "my-wasp-app",
            "template": "basic",
            "include_auth": False,
            "database_type": "sqlite",
            "app_title": "My Wasp Application",
            "npm_dependencies": {
                # Example dependencies
                "@chakra-ui/react": "^2.3.4",
                "@emotion/react": "^11.10.4",
                "@emotion/styled": "^11.10.4",
                "framer-motion": "^7.3.6"
            },
            "env_vars": {
                "NODE_ENV": "production"
            }
        }


# Register the framework handler
FrameworkManager.register("wasp", WaspFrameworkHandler)
