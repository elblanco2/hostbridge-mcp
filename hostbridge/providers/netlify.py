"""
Netlify hosting provider implementation.

This provider handles deployments to Netlify using the Netlify CLI.
"""

import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any

from .base import HostingProvider, HostingProviderFactory

logger = logging.getLogger("hostbridge.providers.netlify")

class NetlifyProvider(HostingProvider):
    """
    Provider for Netlify deployments using the Netlify CLI.
    """
    
    def check_status(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check the status of the Netlify account.
        
        Args:
            credentials: Dictionary containing:
                - access_token: Netlify access token
                
        Returns:
            Status information dictionary
        """
        token = credentials.get("access_token")
        if not token:
            raise ValueError("Netlify access token is required")
        
        try:
            # Use Netlify CLI to check account info
            cmd = ["netlify", "api", "getUser", "--json", "--auth", token]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise ValueError(f"Netlify CLI failed: {result.stderr}")
            
            # Parse the JSON response
            user_info = json.loads(result.stdout)
            
            # Get site count
            cmd = ["netlify", "sites:list", "--json", "--auth", token]
            result = subprocess.run(cmd, capture_output=True, text=True)
            sites_info = []
            
            if result.returncode == 0:
                sites_info = json.loads(result.stdout)
            
            return {
                "status": "active",
                "email": user_info.get("email"),
                "sites": len(sites_info),
                "plan": user_info.get("billing", {}).get("plan", "free")
            }
        except Exception as e:
            logger.error("Failed to check Netlify status: %s", str(e))
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
        Deploy a built application to Netlify.
        
        Args:
            credentials: Dictionary containing:
                - access_token: Netlify access token
            build_path: Path to the built application
            config: Deployment configuration, may include:
                - site_name: Name of the Netlify site
                - team_name: Name of the Netlify team
                
        Returns:
            Deployment result information
        """
        token = credentials.get("access_token")
        if not token:
            raise ValueError("Netlify access token is required")
        
        try:
            # Build the deployment command
            cmd = [
                "netlify", "deploy",
                "--prod",  # Production deployment
                "--dir", str(build_path),
                "--auth", token,
                "--json"  # JSON output for parsing
            ]
            
            # Add site name if specified
            site_name = config.get("site_name")
            if site_name:
                cmd.extend(["--site", site_name])
            
            # Add team name if specified
            team_name = config.get("team_name")
            if team_name:
                cmd.extend(["--team", team_name])
            
            # Execute command
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise ValueError(f"Netlify deployment failed: {result.stderr}")
            
            # Parse deployment result
            deploy_result = json.loads(result.stdout)
            
            return {
                "url": deploy_result.get("url"),
                "deploy_url": deploy_result.get("deploy_url"),
                "site_name": deploy_result.get("site_name"),
                "success": True
            }
        except Exception as e:
            logger.error("Netlify deployment failed: %s", str(e))
            return {
                "url": None,
                "success": False,
                "error": str(e)
            }
    
    def get_requirements(self) -> Dict[str, Any]:
        """
        Get the requirements for Netlify.
        
        Returns:
            Dictionary of requirements information
        """
        return {
            "supported": [
                "node",
                "npm",
                "ruby",
                "python",
                "go",
                "php",
                "postgresql",
                "sqlite",
                "serverless"
            ],
            "dependencies": [
                {
                    "name": "netlify-cli",
                    "install": "npm install -g netlify-cli",
                    "required": True
                }
            ],
            "limits": {
                "free_tier": {
                    "bandwidth": "100GB/month",
                    "build_minutes": "300/month",
                    "sites": "Unlimited"
                }
            }
        }


# Register the provider
HostingProviderFactory.register("netlify", NetlifyProvider)
