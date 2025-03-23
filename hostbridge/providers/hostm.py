"""
Hostm.com hosting provider implementation.

This provider handles deployments to Hostm.com shared hosting environments
using their API and SFTP/SSH access.
"""

import json
import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional
import time

try:
    import paramiko
    import requests
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False

from .base import HostingProvider, HostingProviderFactory

logger = logging.getLogger("hostbridge.providers.hostm")

class HostmProvider(HostingProvider):
    """
    Provider for Hostm.com shared hosting environments.
    
    Hostm.com offers affordable shared hosting with PHP, MySQL, Node.js,
    and other technologies commonly used for web applications.
    """
    
    # API endpoints
    API_BASE_URL = "https://api.hostm.com/v1"
    
    def __init__(self):
        """Initialize the Hostm provider."""
        if not DEPENDENCIES_AVAILABLE:
            logger.warning(
                "One or more required dependencies (paramiko, requests) are not installed. "
                "Install them for full Hostm.com support."
            )
    
    def check_status(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check the status of the Hostm.com hosting account.
        
        Args:
            credentials: Dictionary containing:
                - api_key: Hostm.com API key
                - account_id: Hostm.com account ID
                - host: SSH hostname (optional)
                - user: SSH username (optional)
                - password: SSH password (optional)
                
        Returns:
            Status information dictionary
        """
        api_key = credentials.get("api_key")
        account_id = credentials.get("account_id")
        
        if not (api_key and account_id):
            raise ValueError("Hostm.com API key and account ID are required")
        
        try:
            # Check account status using API
            if DEPENDENCIES_AVAILABLE:
                # Use API to check account status
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                
                response = requests.get(
                    f"{self.API_BASE_URL}/accounts/{account_id}",
                    headers=headers
                )
                
                if response.status_code != 200:
                    raise ValueError(f"API error: {response.text}")
                
                account_info = response.json()
                
                # Get hosting package info
                response = requests.get(
                    f"{self.API_BASE_URL}/accounts/{account_id}/package",
                    headers=headers
                )
                
                package_info = {}
                if response.status_code == 200:
                    package_info = response.json()
                
                return {
                    "status": "active",
                    "account_id": account_id,
                    "email": account_info.get("email"),
                    "hosting_package": package_info.get("name", "Unknown"),
                    "disk_quota": package_info.get("disk_quota", "Unknown"),
                    "bandwidth_quota": package_info.get("bandwidth_quota", "Unknown"),
                    "domains": len(account_info.get("domains", [])),
                }
            else:
                # Fallback to basic status check
                return {
                    "status": "unknown",
                    "message": "Dependencies not available for full status check"
                }
        except Exception as e:
            logger.error("Failed to check Hostm.com status: %s", str(e))
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
        Deploy a built application to Hostm.com.
        
        Args:
            credentials: Dictionary containing:
                - api_key: Hostm.com API key
                - account_id: Hostm.com account ID
                - host: SSH hostname
                - user: SSH username
                - password: SSH password (optional)
                - key_path: Path to SSH private key (optional)
            build_path: Path to the built application
            config: Deployment configuration, may include:
                - domain: Target domain for deployment
                - subdirectory: Subdirectory for deployment (default: public_html)
                - environment: Environment configuration
                
        Returns:
            Deployment result information
        """
        api_key = credentials.get("api_key")
        account_id = credentials.get("account_id")
        host = credentials.get("host")
        user = credentials.get("user")
        password = credentials.get("password")
        key_path = credentials.get("key_path")
        
        if not (api_key and account_id and host and user and (password or key_path)):
            raise ValueError("Incomplete Hostm.com credentials")
        
        domain = config.get("domain", "default")
        subdirectory = config.get("subdirectory", "public_html")
        remote_dir = f"/home/{user}/{subdirectory}"
        
        if domain != "default":
            # Use domain-specific directory
            remote_dir = f"/home/{user}/domains/{domain}/public_html"
        
        try:
            # Step 1: Check if domain exists (if specified)
            if domain != "default" and DEPENDENCIES_AVAILABLE:
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                
                response = requests.get(
                    f"{self.API_BASE_URL}/accounts/{account_id}/domains",
                    headers=headers
                )
                
                if response.status_code == 200:
                    domains = response.json().get("domains", [])
                    domain_exists = any(d.get("name") == domain for d in domains)
                    
                    if not domain_exists:
                        logger.warning(f"Domain {domain} not found in account. Creating directory anyway.")
            
            # Step 2: Prepare any environment configuration
            if config.get("environment") and build_path.joinpath(".env").exists():
                # Create or update .env file
                env_content = []
                for key, value in config["environment"].items():
                    env_content.append(f"{key}={value}")
                
                with open(build_path.joinpath(".env"), "w") as f:
                    f.write("\n".join(env_content))
            
            # Step 3: Upload files using SFTP
            if DEPENDENCIES_AVAILABLE:
                # Use paramiko for SSH/SFTP
                ssh_client = paramiko.SSHClient()
                ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                connect_args = {
                    "hostname": host,
                    "username": user,
                    "port": 22
                }
                
                if password:
                    connect_args["password"] = password
                elif key_path:
                    connect_args["key_filename"] = key_path
                
                ssh_client.connect(**connect_args)
                
                # Ensure remote directory exists
                try:
                    stdin, stdout, stderr = ssh_client.exec_command(f"mkdir -p {remote_dir}")
                    stderr_output = stderr.read().decode()
                    if stderr_output:
                        logger.warning(f"Error creating directory: {stderr_output}")
                except Exception as e:
                    logger.warning(f"Error creating directory: {str(e)}")
                
                # Upload files using SFTP
                sftp = ssh_client.open_sftp()
                self._upload_directory(sftp, build_path, remote_dir)
                sftp.close()
                
                # Set permissions
                try:
                    stdin, stdout, stderr = ssh_client.exec_command(f"chmod -R 755 {remote_dir}")
                    stderr_output = stderr.read().decode()
                    if stderr_output:
                        logger.warning(f"Error setting permissions: {stderr_output}")
                except Exception as e:
                    logger.warning(f"Error setting permissions: {str(e)}")
                
                ssh_client.close()
            else:
                # Use subprocess for SCP as fallback
                cmd = ["scp", "-r"]
                
                # Add identity file if provided
                if key_path:
                    cmd.extend(["-i", key_path])
                
                # Add source and destination
                cmd.extend([
                    str(build_path) + "/*",
                    f"{user}@{host}:{remote_dir}"
                ])
                
                # Execute command
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    raise ValueError(f"SCP failed: {result.stderr}")
            
            # Step 4: Verify deployment and get URL
            url = f"http://{domain}" if domain != "default" else f"http://{host}"
            
            return {
                "url": url,
                "remote_dir": remote_dir,
                "success": True,
                "timestamp": time.time()
            }
        except Exception as e:
            logger.error("Hostm.com deployment failed: %s", str(e))
            return {
                "url": None,
                "success": False,
                "error": str(e)
            }
    
    def get_requirements(self) -> Dict[str, Any]:
        """
        Get the requirements for Hostm.com.
        
        Returns:
            Dictionary of requirements information
        """
        return {
            "supported": [
                "php",
                "mysql",
                "node.js",
                "python",
                "ruby",
                "perl"
            ],
            "dependencies": [
                {
                    "name": "paramiko",
                    "install": "pip install paramiko",
                    "required": True
                },
                {
                    "name": "requests",
                    "install": "pip install requests",
                    "required": True
                }
            ],
            "required_access": [
                "api_key",
                "account_id",
                "ssh_credentials"
            ],
            "limits": {
                "depends_on_plan": True,
                "standard_plan": {
                    "storage": "10GB",
                    "bandwidth": "Unlimited",
                    "databases": 5,
                    "domains": 10
                }
            }
        }
    
    def _upload_directory(
        self, 
        sftp: 'paramiko.SFTPClient', 
        local_dir: Path, 
        remote_dir: str
    ):
        """
        Recursively upload a directory via SFTP.
        
        Args:
            sftp: SFTP client instance
            local_dir: Local directory path
            remote_dir: Remote directory path
        """
        local_dir = Path(local_dir)
        
        for item in local_dir.iterdir():
            if item.is_dir():
                # Skip node_modules and other large directories
                if item.name in ["node_modules", ".git", ".svn", "__pycache__"]:
                    continue
                    
                # Create remote directory if it doesn't exist
                try:
                    sftp.stat(os.path.join(remote_dir, item.name))
                except FileNotFoundError:
                    sftp.mkdir(os.path.join(remote_dir, item.name))
                
                # Recursively upload directory contents
                self._upload_directory(
                    sftp,
                    item,
                    os.path.join(remote_dir, item.name)
                )
            else:
                # Skip hidden files
                if item.name.startswith(".") and item.name != ".htaccess":
                    continue
                    
                # Upload file
                sftp.put(
                    str(item),
                    os.path.join(remote_dir, item.name)
                )


# Register the provider
HostingProviderFactory.register("hostm", HostmProvider)
