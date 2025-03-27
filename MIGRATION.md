# Migration from HostBridge to Arc

This document provides guidance on migrating from HostBridge to Arc, which is the new name for the project.

## Project Renaming

The project has been renamed from "HostBridge" to "Arc" to better reflect its purpose: providing a streamlined arc from development to deployment, with a special focus on shared hosting environments.

## File Structure Changes

The main module has been renamed from `hostbridge` to `arc`. If you were using the previous version, you'll need to update your imports and command-line invocations.

## Configuration Changes

The credential storage path has changed from `~/.hostbridge/credentials` to `~/.arc/credentials`. If you had existing credentials, you'll need to either:

1. Move your credential files to the new location, or
2. Specify the old path using the `--secure-storage-path` option

## Command-Line Usage

Previously:
```bash
hostbridge [options]
```

Now:
```bash
arc [options]
```

## API Changes

The MCP server class has been renamed from `HostBridgeServer` to `ArcServer`, but the API interface remains the same.

## Claude Desktop Configuration

If you're using Claude Desktop, update your configuration to use the new server name:

```json
{
  "mcpServers": {
    "arc": {
      "command": "python",
      "args": [
        "-m",
        "arc",
        "--debug"
      ]
    }
  }
}
```

## Features and Functionality

All features from HostBridge have been preserved in Arc. The focus on shared hosting deployment remains a key differentiator of the project.
