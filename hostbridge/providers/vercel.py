"""
Vercel hosting provider implementation.

This provider handles deployments to Vercel using the Vercel CLI.
"""

import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any

from .base import HostingProvider, HostingProviderFactory

logger = logging.getLogger("hostbridge.providers.vercel")

class VercelProvider(HostingProvider):
    """
    Provider for Vercel deployments using the Vercel CLI.
    """
    
    def check_status(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check the status of the Vercel account.
        
        Args:
            credentials: Dictionary containing:
                - token: Vercel API token
                
        Returns:
            Status information dictionary
        """
        token = credentials.get("token")
        if not token:
            raise ValueError("Vercel API token is required")
        
        try:
            # Use Vercel CLI to check account info
            cmd = ["vercel", "whoami", "--token", token, "--json"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise ValueError(f"Vercel CLI failed: {result.stderr}")
            
            # Parse the JSON response
            user_info = json.loads(result.stdout)
            
            # Get project count
            cmd = ["vercel", "list", "--token", token, "--json"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            projects_info = []
            
            if result.returncode == 0:
                projects_info = json.loads(result.stdout)
            
            return {
                "status": "active",
                "username": user_info.get("username"),
                "email": user_info.get("email"),
                "projects": len(projects_info),
                "plan": user_info.get("plan", {}).get("name", "free")
            }
        except Exception as e:
            logger.error("Failed to check Vercel status: %s", str(e))
            return {
                "status": f"error: {str(e)}"
            }
    
    def deploy(
        self, 
        credentials: Dict[str, Any], 
        build_path: Path, 
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Deploy a built application to Vercel.
        
        Args:
            credentials: Dictionary containing:
                - token: Vercel API token
            build_path: Path to the built application
            config: Deployment configuration, may include:
                - project_name: Name of the Vercel project
                - team_name: Name of the Vercel team
                - environment: Environment variables for deployment
                
        Returns:
            Deployment result information
        """
        token = credentials.get("token")
        if not token:
            raise ValueError("Vercel API token is required")
        
        try:
            # Build the deployment command
            cmd = [
                "vercel",
                "--prod",  # Production deployment
                "--cwd", str(build_path),
                "--token", token,
                "--confirm",  # Skip confirmation prompts
                "--json"  # JSON output for parsing
            ]
            
            # Add project name if specified
            project_name = config.get("project_name")
            if project_name:
                cmd.extend(["--name", project_name])
            
            # Add team name if specified
            team_name = config.get("team_name")
            if team_name:
                cmd.extend(["--scope", team_name])
            
            # Add environment variables if specified
            environment = config.get("environment", {})
            for key, value in environment.items():
                cmd.extend(["--env", f"{key}={value}"])
            
            # Execute command
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise ValueError(f"Vercel deployment failed: {result.stderr}")
            
            # Parse deployment result
            deploy_result = json.loads(result.stdout)
            
            return {
                "url": deploy_result.get("url"),
                "deploy_url": deploy_result.get("deployUrl"),
                "project_name": deploy_result.get("name"),
                "success": True
            }
        except Exception as e:
            logger.error("Vercel deployment failed: %s", str(e))
            return {
                "url": None,
                "success": False,
                "error": str(e)
            }
    
    def get_requirements(self) -> Dict[str, Any]:
        """
        Get the requirements for Vercel.
        
        Returns:
            Dictionary of requirements information
        """
        return {
            "supported": [
                "node",
                "npm",
                "next.js",
                "react",
                "svelte",
                "vue",
                "nuxt",
                "astro",
                "python",
                "go",
                "ruby",
                "php",
                "serverless",
                "edge-functions"
            ],
            "dependencies": [
                {
                    "name": "vercel-cli",
                    "install": "npm install -g vercel",
                    "required": True
                }
            ],
            "limits": {
                "free_tier": {
                    "bandwidth": "100GB/month",
                    "serverless_function_execution": "100GB-hours",
                    "builds": "Unlimited"
                }
            }
        }


# Register the provider
HostingProviderFactory.register("vercel", VercelProvider)
