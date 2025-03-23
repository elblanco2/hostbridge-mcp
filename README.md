# HostBridge MCP Server

A Model Context Protocol (MCP) server that simplifies framework deployments on various hosting environments.

## Overview

HostBridge bridges the gap between Large Language Models (LLMs) and hosting environments, allowing novice developers to deploy web applications easily through conversational interfaces. It implements the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) to expose tools, resources, and prompts that guide users through the deployment process.

### Key Features

- **Framework Support**: Deploy Wasp applications with ease, with planned support for more frameworks
- **Multi-Provider**: Support for Netlify, Vercel, and traditional shared hosting environments
- **Guided Deployments**: Prompts to guide users through the deployment process
- **Authentication Management**: Secure storage of hosting provider credentials
- **Troubleshooting**: Built-in tools to diagnose and fix common deployment issues

## Status

This project is currently in early development. Contributions and feedback are welcome!

## Getting Started

### Prerequisites

- Python 3.10+
- MCP Client (e.g., Claude Desktop)
- Hosting provider accounts as needed

### Installation

```bash
# Clone the repository
git clone https://github.com/elblanco2/hostbridge-mcp.git
cd hostbridge-mcp

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file with your configuration:

```
SECURE_STORAGE_PATH=~/.hostbridge/credentials
```

### Usage

1. Start the MCP server:

```bash
python hostbridge/server.py
```

2. Configure Claude Desktop to use the MCP server (or use another MCP client).

3. Ask Claude to help you deploy your application!

## Architecture

HostBridge is built on a modular architecture:

- **Credentials Manager**: Securely stores and retrieves provider credentials
- **Framework Handlers**: Framework-specific deployment logic
- **Hosting Providers**: Provider-specific deployment operations
- **MCP Interface**: Exposes tools, resources, and prompts via the Model Context Protocol

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Model Context Protocol](https://modelcontextprotocol.io/) for enabling this integration
- [Wasp](https://wasp-lang.dev/) for the excellent framework used in our initial support
