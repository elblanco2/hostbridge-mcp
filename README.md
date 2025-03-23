# HostBridge MCP Server

A Model Context Protocol (MCP) server that simplifies framework deployments on various hosting environments.

## Overview

HostBridge bridges the gap between Large Language Models (LLMs) and hosting environments, allowing novice developers to deploy web applications easily through conversational interfaces. It implements the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) to expose tools, resources, and prompts that guide users through the deployment process.

### Key Features

- **Framework Support**: Deploy Wasp applications with ease, with planned support for more frameworks
- **Multi-Provider**: Support for Netlify, Vercel, traditional shared hosting environments, and Hostm.com
- **Guided Deployments**: Prompts to guide users through the deployment process
- **Authentication Management**: Secure storage of hosting provider credentials
- **Troubleshooting**: Built-in tools to diagnose and fix common deployment issues
- **Windsurf Integration**: Seamless handoff to Windsurf (Codeium's VS Code) for continued development

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

# Install the package in development mode
pip install -e .
```

### Configuration

Create a `.env` file with your configuration:

```
SECURE_STORAGE_PATH=~/.hostbridge/credentials
```

### Usage

#### Running from command line

```bash
# Start the server directly
hostbridge

# With debug logging
hostbridge --debug

# With a custom storage path
hostbridge --secure-storage-path=/path/to/credentials
```

#### Using with Claude Desktop

1. Edit your Claude Desktop configuration file:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`

2. Add HostBridge server configuration:

```json
{
  "mcpServers": {
    "hostbridge": {
      "command": "python",
      "args": [
        "-m",
        "hostbridge",
        "--debug"
      ]
    }
  }
}
```

3. Restart Claude Desktop.

4. Start conversations with Claude about deploying your applications!

#### Using with Windsurf (Codeium)

The HostBridge MCP server includes special integration with Windsurf, Codeium's version of VS Code, to provide a seamless development experience after deployment:

1. Deploy your application using HostBridge.
2. Use the "windsurf-handoff" prompt to transition to Windsurf for continued development.
3. Windsurf's AI Flow feature will guide you through adding features and improving your application.

Example conversation with Claude:

```
User: I've deployed my Wasp app to Netlify. Now I want to continue development in Windsurf.

Claude: I'll help you transition to Windsurf for continued development. [Uses windsurf-handoff prompt]

[Claude guides the user through setting up Windsurf with the project, configuring AI Flow, and starting development]
```

## Architecture

HostBridge is built on a modular architecture:

- **Credentials Manager**: Securely stores and retrieves provider credentials
- **Framework Handlers**: Framework-specific deployment logic
- **Hosting Providers**: Provider-specific deployment operations
- **MCP Interface**: Exposes tools, resources, and prompts via the Model Context Protocol

## Supported Providers

| Provider | Status | Features |
|----------|--------|----------|
| Netlify | ✅ Complete | Serverless, Edge, Forms |
| Vercel | ✅ Complete | Serverless, Edge, Analytics |
| Shared Hosting | ✅ Complete | SSH/SFTP, PHP, MySQL |
| Hostm.com | ✅ Complete | Shared Hosting, API Access |

## Supported Frameworks

| Framework | Status | Features |
|-----------|--------|----------|
| Wasp | ✅ Complete | Full-Stack JS Framework |
| Next.js | 🚧 Planned | React Framework |
| Astro | 🚧 Planned | Static Site Generator |

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
flake8
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Model Context Protocol](https://modelcontextprotocol.io/) for enabling this integration
- [Wasp](https://wasp-lang.dev/) for the excellent framework used in our initial support
- [Windsurf](https://codeium.com/windsurf) for AI-powered development environment integration
