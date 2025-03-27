"""
MCP server implementation for Arc.

This module provides the Model Context Protocol (MCP) server implementation
that exposes the providers, frameworks, and tools of Arc.
"""

import asyncio
import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

from mcp.server import Server
import mcp.types as types

from .credentials import CredentialsManager
from .frameworks import FrameworkManager
from .providers import HostingProviderFactory

logger = logging.getLogger("arc.server")

class ArcServer:
    """
    MCP server implementation for Arc.
    
    This class initializes and runs the MCP server that exposes Arc
    functionality to clients.
    """
    
    def __init__(
        self, 
        secure_storage_path: Optional[str] = None,
        debug: bool = False
    ):
        """
        Initialize the Arc MCP server.
        
        Args:
            secure_storage_path: Path for storing credentials
            debug: Whether to enable debug logging
        """
        # Set up logging
        log_level = logging.DEBUG if debug else logging.INFO
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        
        # Initialize storage path
        if not secure_storage_path:
            secure_storage_path = os.path.expanduser("~/.arc/credentials")
        
        # Initialize components
        self.credentials_manager = CredentialsManager(secure_storage_path)
        
        # Initialize MCP server
        self.app = Server("arc-server")
        
        # Register MCP endpoints
        self._register_tools()
        self._register_resources()
        self._register_prompts()
    
    def _register_tools(self):
        """Register MCP tools."""
        
        @self.app.tool()
        async def authenticate_provider(
            provider: str,
            credentials: Dict[str, str]
        ) -> str:
            """
            Store authentication credentials for a hosting provider.
            
            Args:
                provider: The hosting provider (e.g., 'netlify', 'vercel', 'shared_hosting', 'hostm')
                credentials: Provider-specific credentials (API keys, usernames, passwords)
            """
            try:
                success = self.credentials_manager.store_credentials(provider, credentials)
                if success:
                    return f"Successfully authenticated with {provider}"
                else:
                    return f"Failed to store credentials for {provider}"
            except Exception as e:
                logger.error(f"Authentication error: {str(e)}")
                return f"Failed to authenticate: {str(e)}"
        
        @self.app.tool()
        async def check_server_status(provider: str) -> str:
            """
            Check the status of the configured server.
            
            Args:
                provider: The hosting provider to check
            """
            try:
                credentials = self.credentials_manager.get_credentials(provider)
                if not credentials:
                    return f"No credentials found for {provider}"
                
                hosting_provider = HostingProviderFactory.get_provider(provider)
                if not hosting_provider:
                    return f"Unsupported provider: {provider}"
                
                status = hosting_provider.check_status(credentials)
                return json.dumps(status, indent=2)
            except Exception as e:
                logger.error(f"Status check error: {str(e)}")
                return f"Failed to check status: {str(e)}"
        
        @self.app.tool()
        async def analyze_requirements(
            framework: str,
            provider: str
        ) -> str:
            """
            Analyze and return the requirements for deploying a framework on a provider.
            
            Args:
                framework: The framework to analyze
                provider: The hosting provider to target
            """
            try:
                framework_handler = FrameworkManager.get_framework_handler(framework)
                if not framework_handler:
                    return f"Unsupported framework: {framework}"
                
                hosting_provider = HostingProviderFactory.get_provider(provider)
                if not hosting_provider:
                    return f"Unsupported provider: {provider}"
                
                framework_reqs = framework_handler.get_requirements()
                provider_reqs = hosting_provider.get_requirements()
                
                combined_reqs = {
                    "framework": framework_reqs,
                    "provider": provider_reqs,
                    "compatibility_issues": []
                }
                
                # Identify compatibility issues
                for req in framework_reqs.get("required", []):
                    if "supported" in provider_reqs and req not in provider_reqs.get("supported", []):
                        # Extract base requirement name (without version)
                        req_name = req.split()[0] if " " in req else req
                        if not any(req_name in s for s in provider_reqs.get("supported", [])):
                            combined_reqs["compatibility_issues"].append(
                                f"Provider {provider} may not support {req_name} required by {framework}"
                            )
                
                # Add provider comparison if available
                if "providers_comparison" in framework_reqs:
                    combined_reqs["providers_comparison"] = framework_reqs["providers_comparison"]
                
                return json.dumps(combined_reqs, indent=2)
            except Exception as e:
                logger.error(f"Requirements analysis error: {str(e)}")
                return f"Failed to analyze requirements: {str(e)}"
        
        @self.app.tool()
        async def deploy_framework(
            framework: str,
            provider: str,
            app_name: str,
            config: Dict[str, Any]
        ) -> str:
            """
            Deploy a framework to the specified hosting provider.
            
            Args:
                framework: Framework to deploy (e.g., 'wasp')
                provider: Hosting provider to deploy to
                app_name: Name of the application
                config: Framework-specific configuration
            """
            logs = []
            
            try:
                # Get credentials
                credentials = self.credentials_manager.get_credentials(provider)
                if not credentials:
                    return "No credentials found for the specified provider"
                
                # Get provider and framework handlers
                hosting_provider = HostingProviderFactory.get_provider(provider)
                if not hosting_provider:
                    return f"Unsupported provider: {provider}"
                
                framework_handler = FrameworkManager.get_framework_handler(framework)
                if not framework_handler:
                    return f"Unsupported framework: {framework}"
                
                # Create a temporary directory for the project
                with tempfile.TemporaryDirectory() as project_dir:
                    logs.append(f"Created temporary project directory: {project_dir}")
                    
                    # Create the project
                    logs.append("Creating project...")
                    project_config = {
                        "app_name": app_name,
                        **config
                    }
                    app_dir = framework_handler.create_project(Path(project_dir), project_config)
                    
                    # Build the project
                    logs.append("Building project...")
                    build_dir = framework_handler.build_project(app_dir, config)
                    
                    # Deploy the project
                    logs.append(f"Deploying to {provider}...")
                    result = hosting_provider.deploy(credentials, build_dir, config)
                    
                    if result.get("success"):
                        url = result.get("url", "Unknown URL")
                        logs.append(f"Deployment complete! Your application is available at: {url}")
                    else:
                        logs.append(f"Deployment failed: {result.get('error', 'Unknown error')}")
                    
                    return "\\n".join(logs)
                
            except Exception as e:
                logger.error(f"Deployment error: {str(e)}")
                logs.append(f"Error: {str(e)}")
                return "\\n".join(logs)
        
        @self.app.tool()
        async def troubleshoot_deployment(
            framework: str,
            provider: str,
            error_logs: str
        ) -> str:
            """
            Analyze deployment errors and suggest solutions.
            
            Args:
                framework: The framework being deployed
                provider: The hosting provider
                error_logs: Error logs from the failed deployment
            """
            try:
                # This would be a more sophisticated analysis in a real implementation
                # For now, we'll use a simple pattern matching approach
                
                common_issues = {
                    "EACCES": "Permission denied. Check if you have the necessary permissions.",
                    "ECONNREFUSED": "Connection refused. The server might be down or unreachable.",
                    "npm ERR!": "NPM dependency installation failed. Check package.json.",
                    "DATABASE_URL": "Database URL is missing or invalid.",
                    "Out of memory": "The server ran out of memory. Consider upgrading your plan.",
                    "command not found": "Required command not found. Make sure all dependencies are installed.",
                    "timeout": "Operation timed out. Check your network connection or server response time.",
                    "FATAL ERROR: Ineffective mark-compacts": "Node.js memory limit exceeded. Try allocating more memory.",
                    "certificate": "SSL certificate issue. Check your SSL configuration.",
                    "port is already in use": "Port conflict. Another service is using the required port."
                }
                
                # Framework-specific issues
                framework_issues = {
                    "wasp": {
                        "Error: Cannot find module": "Missing Node.js module. Try running 'npm install' in your project.",
                        "spawn wasp ENOENT": "Wasp CLI not found. Make sure it's installed and in your PATH.",
                        ".wasp/build": "Build directory not found. Make sure the Wasp build was successful."
                    }
                }
                
                # Provider-specific issues
                provider_issues = {
                    "netlify": {
                        "deploy upload missing": "Upload failed. Check your internet connection.",
                        "Error: Not authorized": "Authentication error. Check your Netlify token.",
                        "Error: Site not found": "Specified site doesn't exist. Check the site name."
                    },
                    "vercel": {
                        "Error: The path you're trying to deploy": "Invalid project structure for Vercel.",
                        "Error: No authorization token": "Missing Vercel token. Check your authentication.",
                        "Error: Invalid project settings": "Project configuration not compatible with Vercel."
                    },
                    "shared_hosting": {
                        "ssh: connect to host": "SSH connection failed. Check hostname and credentials.",
                        "Permission denied": "Access denied. Check your SSH credentials and file permissions.",
                        "No space left on device": "Server has run out of disk space."
                    },
                    "hostm": {
                        "API rate limit exceeded": "Too many API requests. Wait and try again later.",
                        "Domain not configured": "The domain is not properly set up on Hostm.",
                        "Account suspended": "Your Hostm account may be suspended."
                    }
                }
                
                suggestions = []
                
                # Check common issues
                for pattern, solution in common_issues.items():
                    if pattern in error_logs:
                        suggestions.append(f"Issue: {pattern}\\nSuggestion: {solution}")
                
                # Check framework-specific issues
                if framework in framework_issues:
                    for pattern, solution in framework_issues[framework].items():
                        if pattern in error_logs:
                            suggestions.append(f"Framework issue: {pattern}\\nSuggestion: {solution}")
                
                # Check provider-specific issues
                if provider in provider_issues:
                    for pattern, solution in provider_issues[provider].items():
                        if pattern in error_logs:
                            suggestions.append(f"Provider issue: {pattern}\\nSuggestion: {solution}")
                
                if not suggestions:
                    framework_specific = f"No common issues identified. Consider checking {framework} documentation for specific error patterns."
                    provider_specific = f"Also check {provider} deployment guides for provider-specific issues."
                    return f"{framework_specific}\\n\\n{provider_specific}"
                
                return "\\n\\n".join(suggestions)
            except Exception as e:
                logger.error(f"Troubleshooting error: {str(e)}")
                return f"Failed to troubleshoot: {str(e)}"
    
    def _register_resources(self):
        """Register MCP resources."""
        
        @self.app.list_resources()
        async def list_resources() -> List[types.Resource]:
            """List available resources."""
            return [
                types.Resource(
                    uri="hosting://providers",
                    name="Hosting Providers",
                    description="List of supported hosting providers"
                ),
                types.Resource(
                    uri="hosting://frameworks",
                    name="Supported Frameworks",
                    description="List of supported frameworks"
                ),
                types.Resource(
                    uri="hosting://templates/{framework}",
                    name="Framework Templates",
                    description="Available templates for a specific framework"
                ),
                types.Resource(
                    uri="hosting://deployment-logs/{provider}/{app_name}",
                    name="Deployment Logs",
                    description="Logs from previous deployments"
                )
            ]
        
        @self.app.read_resource()
        async def read_resource(uri: str) -> str:
            """Read a resource."""
            try:
                if uri == "hosting://providers":
                    providers = HostingProviderFactory.get_available_providers()
                    
                    # Build providers data
                    providers_data = {
                        "supported": list(providers.keys()),
                        "features": {}
                    }
                    
                    # Add features for each provider
                    for name, provider_class in providers.items():
                        provider = provider_class()
                        requirements = provider.get_requirements()
                        providers_data["features"][name] = {
                            "supported": requirements.get("supported", []),
                            "required_access": requirements.get("required_access", []),
                            "limits": requirements.get("limits", {})
                        }
                    
                    return json.dumps(providers_data, indent=2)
                    
                elif uri == "hosting://frameworks":
                    frameworks = FrameworkManager.get_available_frameworks()
                    
                    # Build frameworks data
                    frameworks_data = {
                        "supported": list(frameworks.keys()),
                        "coming_soon": ["next.js", "astro", "remix"]
                    }
                    
                    # Add requirements for each framework
                    frameworks_data["requirements"] = {}
                    for name, framework_class in frameworks.items():
                        framework = framework_class()
                        frameworks_data["requirements"][name] = framework.get_requirements()
                    
                    return json.dumps(frameworks_data, indent=2)
                    
                elif uri.startswith("hosting://templates/"):
                    framework = uri.split("/")[-1]
                    framework_handler = FrameworkManager.get_framework_handler(framework)
                    
                    if not framework_handler:
                        return json.dumps({"error": f"Framework not supported: {framework}"})
                    
                    requirements = framework_handler.get_requirements()
                    templates = requirements.get("templates", {})
                    
                    templates_data = {
                        "templates": [
                            {
                                "name": name,
                                "description": description
                            }
                            for name, description in templates.items()
                        ],
                        "configuration_template": framework_handler.get_configuration_template()
                    }
                    
                    return json.dumps(templates_data, indent=2)
                    
                elif uri.startswith("hosting://deployment-logs/"):
                    parts = uri.split("/")
                    if len(parts) >= 4:
                        provider = parts[2]
                        app_name = parts[3]
                        
                        # In a real implementation, fetch logs from storage
                        return json.dumps({
                            "provider": provider,
                            "app_name": app_name,
                            "logs": [
                                {
                                    "timestamp": "2025-03-23T12:34:56Z",
                                    "message": "Example deployment log entry"
                                }
                            ]
                        }, indent=2)
                
                return json.dumps({"error": f"Resource not found: {uri}"})
            except Exception as e:
                logger.error(f"Resource read error: {str(e)}")
                return json.dumps({"error": f"Failed to read resource: {str(e)}"})
    
    def _register_prompts(self):
        """Register MCP prompts."""
        
        @self.app.list_prompts()
        async def list_prompts() -> List[types.Prompt]:
            """List available prompts."""
            return [
                types.Prompt(
                    name="wasp-deployment",
                    description="Guide for deploying a Wasp application",
                    arguments=[
                        types.PromptArgument(
                            name="provider",
                            description="Hosting provider",
                            required=True
                        ),
                        types.PromptArgument(
                            name="app_name",
                            description="Application name",
                            required=True
                        )
                    ]
                ),
                types.Prompt(
                    name="troubleshooting",
                    description="Guide for troubleshooting deployment issues",
                    arguments=[
                        types.PromptArgument(
                            name="framework",
                            description="Framework being deployed",
                            required=True
                        ),
                        types.PromptArgument(
                            name="provider",
                            description="Hosting provider",
                            required=True
                        )
                    ]
                )
            ]
        
        @self.app.get_prompt()
        async def get_prompt(
            name: str,
            arguments: Optional[Dict[str, str]] = None
        ) -> types.GetPromptResult:
            """Get a specific prompt."""
            try:
                if name == "wasp-deployment":
                    provider = arguments.get("provider", "unknown") if arguments else "unknown"
                    app_name = arguments.get("app_name", "myapp") if arguments else "myapp"
                    
                    return types.GetPromptResult(
                        messages=[
                            types.PromptMessage(
                                role="user",
                                content=types.TextContent(
                                    type="text",
                                    text=f"""
I want to deploy a Wasp application named "{app_name}" to {provider}.
Can you guide me through the process step by step?
Please include:
1. What information I'll need to provide
2. Any prerequisites I should install
3. How to authenticate with {provider}
4. The deployment process
5. How to verify the deployment was successful
6. Common issues I might encounter
"""
                                )
                            )
                        ]
                    )
                    
                elif name == "troubleshooting":
                    framework = arguments.get("framework", "unknown") if arguments else "unknown"
                    provider = arguments.get("provider", "unknown") if arguments else "unknown"
                    
                    return types.GetPromptResult(
                        messages=[
                            types.PromptMessage(
                                role="user",
                                content=types.TextContent(
                                    type="text",
                                    text=f"""
I'm having issues deploying my {framework} application to {provider}.
Can you help me troubleshoot the problem?
Please:
1. Ask me for any error messages or logs
2. Help me understand what might be causing the issue
3. Suggest potential solutions
4. Guide me through implementing the fixes
5. Explain how to verify the issue is resolved
"""
                                )
                            )
                        ]
                    )
                
                return types.GetPromptResult(
                    messages=[
                        types.PromptMessage(
                            role="user",
                            content=types.TextContent(
                                type="text",
                                text=f"No prompt found with name: {name}"
                            )
                        )
                    ]
                )
            except Exception as e:
                logger.error(f"Prompt error: {str(e)}")
                return types.GetPromptResult(
                    messages=[
                        types.PromptMessage(
                            role="user",
                            content=types.TextContent(
                                type="text",
                                text=f"Error retrieving prompt: {str(e)}"
                            )
                        )
                    ]
                )
    
    async def run(self, transport='stdio'):
        """
        Run the MCP server.
        
        Args:
            transport: The transport to use ('stdio' or 'sse')
        """
        logger.info("Starting Arc MCP server...")
        
        if transport == 'stdio':
            from mcp.server.stdio import stdio_server
            
            async with stdio_server() as streams:
                await self.app.run(
                    streams[0],
                    streams[1],
                    self.app.create_initialization_options()
                )
        elif transport == 'sse':
            # For HTTP-based SSE transport, using the Servlet-based implementation
            # This is a placeholder - in a real implementation, you would configure your HTTP server
            from mcp.server.servlet_sse import create_sse_servlet
            
            # Here you would integrate with your chosen web framework
            logger.info("SSE transport not fully implemented yet")
        else:
            raise ValueError(f"Unsupported transport: {transport}")


def main():
    """Run the Arc MCP server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Arc MCP Server")
    parser.add_argument(
        "--debug", 
        action="store_true", 
        help="Enable debug logging"
    )
    parser.add_argument(
        "--secure-storage-path",
        type=str,
        help="Path for storing credentials"
    )
    parser.add_argument(
        "--transport",
        type=str,
        default="stdio",
        choices=["stdio", "sse"],
        help="Transport to use (stdio or sse)"
    )
    
    args = parser.parse_args()
    
    server = ArcServer(
        secure_storage_path=args.secure_storage_path,
        debug=args.debug
    )
    
    asyncio.run(server.run(transport=args.transport))


if __name__ == "__main__":
    main()
