"""
Shared hosting provider implementation.

This provider handles deployments to traditional shared hosting environments
via SSH/SFTP.
"""

import logging
import os
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

try:
    import paramiko
    PARAMIKO_AVAILABLE = True
except ImportError:
    PARAMIKO_AVAILABLE = False

from .base import HostingProvider, HostingProviderFactory

logger = logging.getLogger("hostbridge.providers.shared_hosting")

class SharedHostingProvider(HostingProvider):
    """
    Provider for traditional shared hosting environments using SSH/SFTP.
    """
    
    def __init__(self):
        """Initialize the shared hosting provider."""
        if not PARAMIKO_AVAILABLE:
            logger.warning(
                "Paramiko is not installed. Using subprocess-based SSH/SCP instead. "
                "Install paramiko for more robust shared hosting support."
            )
    
    def check_status(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check the status of the shared hosting environment.
        
        Args:
            credentials: Dictionary containing:
                - host: SSH hostname
                - user: SSH username
                - password: SSH password (optional)
                - key_path: Path to SSH private key (optional)
                
        Returns:
            Status information dictionary
        """
        host = credentials.get("host")
        user = credentials.get("user")
        
        if not (host and user):
            raise ValueError("SSH host and user are required")
        
        # Status information to collect
        status = {
            "status": "unknown",
            "disk_usage": "unknown",
            "memory_usage": "unknown",
            "load_average": "unknown",
        }
        
        if PARAMIKO_AVAILABLE:
            # Use paramiko for SSH
            try:
                client = self._create_ssh_client(credentials)
                
                # Check connection
                status["status"] = "connected"
                
                # Get disk usage
                stdin, stdout, stderr = client.exec_command("df -h | grep -E '/$|/home'")
                disk_info = stdout.read().decode().strip()
                if disk_info:
                    status["disk_usage"] = disk_info
                
                # Get memory usage
                stdin, stdout, stderr = client.exec_command("free -m | grep Mem")
                mem_info = stdout.read().decode().strip()
                if mem_info:
                    status["memory_usage"] = mem_info
                
                # Get load average
                stdin, stdout, stderr = client.exec_command("cat /proc/loadavg")
                load_info = stdout.read().decode().strip()
                if load_info:
                    parts = load_info.split()
                    if len(parts) >= 3:
                        status["load_average"] = {
                            "1min": float(parts[0]),
                            "5min": float(parts[1]),
                            "15min": float(parts[2]),
                        }
                
                client.close()
            except Exception as e:
                logger.error("Failed to check server status: %s", str(e))
                status["status"] = f"error: {str(e)}"
        else:
            # Use subprocess for SSH
            try:
                # Just check if we can connect
                cmd = ["ssh"]
                
                # Add identity file if provided
                key_path = credentials.get("key_path")
                if key_path:
                    cmd.extend(["-i", key_path])
                
                # Add host
                cmd.extend([f"{user}@{host}", "echo 'Connection test'"])
                
                # Run command
                result = subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    status["status"] = "connected"
                else:
                    status["status"] = f"error: {result.stderr.strip()}"
            except Exception as e:
                logger.error("Failed to check server status: %s", str(e))
                status["status"] = f"error: {str(e)}"
        
        return status
    
    def deploy(
        self, 
        credentials: Dict[str, Any], 
        build_path: Path, 
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Deploy a built application to the shared hosting environment.
        
        Args:
            credentials: Dictionary containing:
                - host: SSH hostname
                - user: SSH username
                - password: SSH password (optional)
                - key_path: Path to SSH private key (optional)
                - directory: Remote directory for deployment
            build_path: Path to the built application
            config: Deployment configuration
            
        Returns:
            Deployment result information
        """
        host = credentials.get("host")
        user = credentials.get("user")
        password = credentials.get("password")
        key_path = credentials.get("key_path")
        remote_dir = credentials.get("directory", "/var/www/html")
        
        if not (host and user and (password or key_path)):
            raise ValueError("SSH credentials are incomplete")
        
        try:
            if PARAMIKO_AVAILABLE:
                # Use paramiko for SFTP
                client = self._create_ssh_client(credentials)
                
                # Ensure remote directory exists
                stdin, stdout, stderr = client.exec_command(f"mkdir -p {remote_dir}")
                if stderr.read():
                    raise ValueError(f"Failed to create remote directory: {stderr.read().decode()}")
                
                # Upload files using SFTP
                sftp = client.open_sftp()
                
                # Recursively upload build directory
                self._upload_directory(sftp, build_path, remote_dir)
                
                sftp.close()
                client.close()
            else:
                # Use subprocess for SCP
                cmd = ["scp", "-r"]
                
                # Add identity file if provided
                if key_path:
                    cmd.extend(["-i", key_path])
                
                # Add source and destination
                cmd.extend([
                    str(build_path) + "/*",
                    f"{user}@{host}:{remote_dir}"
                ])
                
                # Run command
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    raise ValueError(f"SCP failed: {result.stderr}")
            
            # Get the URL based on the server configuration
            url = config.get("url", f"http://{host}")
            
            return {
                "url": url,
                "remote_dir": remote_dir,
                "success": True
            }
        except Exception as e:
            logger.error("Deployment failed: %s", str(e))
            return {
                "url": None,
                "remote_dir": remote_dir,
                "success": False,
                "error": str(e)
            }
    
    def get_requirements(self) -> Dict[str, Any]:
        """
        Get the requirements for shared hosting.
        
        Returns:
            Dictionary of requirements information
        """
        return {
            "supported": [
                "php",
                "node",
                "mysql",
                "postgresql",
                "sqlite"
            ],
            "required_access": [
                "ssh",
                "sftp"
            ],
            "dependencies": [
                {"name": "paramiko", "optional": True, "description": "For enhanced SSH/SFTP support"}
            ]
        }
    
    def _create_ssh_client(self, credentials: Dict[str, Any]) -> 'paramiko.SSHClient':
        """
        Create an SSH client using the provided credentials.
        
        Args:
            credentials: SSH credentials
            
        Returns:
            Connected paramiko.SSHClient instance
        """
        if not PARAMIKO_AVAILABLE:
            raise ImportError("Paramiko is required for this operation")
        
        host = credentials.get("host")
        user = credentials.get("user")
        password = credentials.get("password")
        key_path = credentials.get("key_path")
        port = int(credentials.get("port", 22))
        
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        connect_args = {
            "hostname": host,
            "username": user,
            "port": port
        }
        
        if password:
            connect_args["password"] = password
        elif key_path:
            connect_args["key_filename"] = key_path
        
        client.connect(**connect_args)
        return client
    
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
                # Upload file
                sftp.put(
                    str(item),
                    os.path.join(remote_dir, item.name)
                )


# Register the provider
HostingProviderFactory.register("shared_hosting", SharedHostingProvider)
