# Changelog

## v0.2.0 (2025-03-27)

### Major Changes
- **Project Renamed**: Changed name from "HostBridge" to "Arc"
- **Module Structure**: Reorganized module structure from `hostbridge` to `arc`
- **Configuration Path**: Updated default credentials path from `~/.hostbridge/credentials` to `~/.arc/credentials`

### Added
- New example for deploying Wasp applications to shared hosting
- Added `.gitignore` file for better repository management
- Added GitHub Actions workflow for automated testing
- Added MIGRATION.md guide for transitioning from HostBridge to Arc
- Added this CHANGELOG.md to track project history

### Removed
- Removed Windsurf integration prompt (simplified focus on deployment)

### Under the Hood
- Updated all internal references to use the Arc naming
- Simplified server implementation
- Improved documentation

## v0.1.0 (2025-03-23)

### Initial Release
- Basic MCP server implementation
- Support for framework deployments
- Multi-provider deployment support (Netlify, Vercel, shared hosting, Hostm.com)
- Framework handler for Wasp applications
- Secure credentials management
- Deployment troubleshooting
