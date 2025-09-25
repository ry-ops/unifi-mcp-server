<img src="https://github.com/ry-ops/unifi-mcp-server/blob/main/unifi-mcp-server.png" width="100%">

# MCP Server UniFi - Infrastructure Monitoring

A Model Context Protocol (MCP) server for monitoring UniFi infrastructure through the Site Manager API. This server enables natural language interactions with your UniFi network using AI agents like Claude by wrapping the UniFi Site Manager API.

## Features

- Query UniFi hosts, sites, and devices using natural language through AI agents
- Cloud-based infrastructure monitoring via UniFi Site Manager API
- Compatible with Claude Desktop and other MCP clients
- Secure API key-based authentication
- Device search and filtering capabilities
- Comprehensive infrastructure overview tools

## Prerequisites

- Python 3.8 or higher
- `uv` package manager
- UniFi Site Manager account with API access
- UniFi Site Manager API key

## Setup

1. **Create a Site Manager API key:**
   - Go to [UniFi Site Manager](https://unifi.ui.com)
   - Navigate to API section from the left navigation bar
   - Click "Create API Key"
   - Copy the generated key (it will only be displayed once)

2. **Clone and set up the repository:**
```bash
git clone <your-repository-url>
cd mcp-server-unifi
uv venv
source .venv/bin/activate  # On Unix/macOS
# or
.venv\Scripts\activate  # On Windows
```

3. **Install dependencies:**
```bash
uv sync
```

4. **Configure environment variables:**
Create a `secrets.env` file in the project root:
```env
UNIFI_SITEMGR_BASE=https://api.ui.com
UNIFI_SITEMGR_TOKEN=your_site_manager_api_key_here
UNIFI_TIMEOUT_S=15
```

## Running the Server

Start the MCP development server:
```bash
uv run mcp dev main.py
```

Or run directly:
```bash
uv run main.py
```

The MCP Inspector will be available at http://localhost:5173 for testing and debugging when using `mcp dev`.

## Testing Setup

Test your configuration:
```bash
# Test endpoint connectivity
uv run test_working_features.py

# Get your site and host IDs
uv run get_site_host_ids.py
```

## AI Agent Integration

### Claude Desktop Setup

1. Open Claude Desktop and go to Settings > Developer > Edit Config
2. Add to your `claude_desktop_config.json`:

```json
{
    "mcpServers": {
        "unifi": {
            "command": "uv",
            "args": [
                "--directory",
                "/path/to/mcp-server-unifi",
                "run",
                "main.py"
            ],
            "env": {
                "UNIFI_SITEMGR_TOKEN": "your_site_manager_api_key_here"
            }
        }
    }
}
```

Alternatively, if using the `secrets.env` file:
```json
{
    "mcpServers": {
        "unifi": {
            "command": "uv",
            "args": [
                "--directory",
                "/path/to/mcp-server-unifi",
                "run",
                "main.py"
            ]
        }
    }
}
```

## Available Resources

- `sitemanager://hosts` - List all UniFi OS consoles
- `sitemanager://hosts/{host_id}` - Get specific console details
- `sitemanager://sites` - List all network sites
- `sitemanager://devices` - List all devices across infrastructure
- `sitemanager://devices/{device_id}` - Get specific device details

## Available Tools

- `sm_get_infrastructure_overview` - Complete network summary with statistics
- `sm_search_devices` - Search and filter devices by name, type, or host
- `sm_get_host_summary` - Detailed host analysis with related sites and devices

## Example Usage

Once integrated with Claude Desktop, you can ask natural language questions like:

- "Show me an overview of my UniFi infrastructure"
- "Search for devices with 'living room' in the name"
- "What devices are connected to my main host?"
- "List all my UniFi sites and their device counts"

## Troubleshooting

### Common Issues

**Authentication Errors (401)**
- Verify your Site Manager API key is correct
- Check that the key hasn't expired
- Ensure your UniFi account has appropriate permissions

**Empty Results**
- Confirm your UniFi devices are properly connected to Site Manager
- Check that your account has access to the relevant sites/hosts
- Verify devices are online and reporting to the cloud

**Connection Issues**
- Check internet connectivity
- Verify Site Manager service status
- Increase timeout value in secrets.env

### Debug Commands

```bash
# Test all endpoints
uv run test_working_features.py

# Get site and host information
uv run get_site_host_ids.py
```

## Limitations

This server is optimized for basic Site Manager functionality. The following features are not currently supported:

- ISP Metrics (requires specific UniFi subscription/plan)
- Local Network Control (requires local controller API access)
- UniFi Protect integration (requires additional permissions)
- Advanced Analytics (may require premium Site Manager features)

## Architecture

The server focuses on three core Site Manager endpoints that provide reliable access:
- `/v1/hosts` - UniFi OS console information
- `/v1/sites` - Network site details
- `/v1/devices` - Device inventory across all sites

This targeted approach ensures consistent functionality while avoiding endpoints that may require additional subscriptions or configurations.

## Security

- Store API keys in `secrets.env` (excluded from version control)
- Use HTTPS for all API communications
- Treat API keys as sensitive credentials
- Consider rotating API keys periodically

## Contributing

When adding new features:
1. Test endpoint availability first using the provided testing utilities
2. Follow the existing pattern for resources, tools, and prompts
3. Update documentation for any new capabilities

