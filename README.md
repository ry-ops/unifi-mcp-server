<img src="https://github.com/ry-ops/unifi-mcp-server/blob/main/unifi-mcp-server.png" width="100%">

# UniFi MCP Server - Infrastructure Monitoring

A streamlined Model Context Protocol (MCP) server for monitoring UniFi infrastructure through the Site Manager API.

## Overview

This MCP server provides cloud-based monitoring of UniFi networks through Ubiquiti's Site Manager API. It's optimized for reliable infrastructure monitoring using only the working endpoints from your UniFi setup.

**Current Capabilities:**
- Infrastructure overview and monitoring
- Device inventory and search across your network
- Host and site management
- Cloud-based UniFi network analysis

**Architecture:** This server focuses on the three core Site Manager endpoints that provide consistent access: hosts, sites, and devices. It removes non-functional endpoints to provide a clean, reliable monitoring experience.

## Features

### Resources
- `sitemanager://hosts` - List all UniFi OS consoles
- `sitemanager://hosts/{host_id}` - Get specific console details  
- `sitemanager://sites` - List all network sites
- `sitemanager://devices` - List all devices across infrastructure
- `sitemanager://devices/{device_id}` - Get specific device details

### Tools
- `sm_get_infrastructure_overview` - Complete network summary with statistics
- `sm_search_devices` - Search and filter devices by name, type, or host
- `sm_get_host_summary` - Detailed host analysis with related sites and devices

### Guided Workflows
- Infrastructure monitoring guidance
- Device search and filtering workflows
- Site analysis procedures

## Installation

### Prerequisites
- Python 3.8+
- UniFi Site Manager account with API access
- Valid Site Manager API key

### Setup

1. **Clone the repository:**
```bash
git clone <repository-url>
cd unifi-mcp-server
```

2. **Install dependencies:**
```bash
uv install
# or
pip install -r requirements.txt
```

3. **Create secrets.env file:**
```env
UNIFI_SITEMGR_BASE=https://api.ui.com
UNIFI_SITEMGR_TOKEN=your_site_manager_api_key_here
UNIFI_TIMEOUT_S=15
```

4. **Get your Site Manager API key:**
   - Sign in to [UniFi Site Manager](https://unifi.ui.com)
   - Navigate to API section in left sidebar
   - Click "Create API Key"
   - Copy the generated key to your `secrets.env` file

## Usage

### Running the Server
```bash
uv run main.py
# or
python main.py
```

### Testing Connectivity
```bash
# Test what endpoints are accessible
uv run test_working_features.py

# Get your site and host IDs
uv run get_site_host_ids.py
```

### MCP Client Integration

Add to your MCP client configuration:
```json
{
  "mcpServers": {
    "unifi": {
      "command": "uv",
      "args": ["run", "main.py"],
      "cwd": "/path/to/unifi-mcp-server"
    }
  }
}
```

## Example Queries

### Get Infrastructure Overview
```
Use the 'sm_get_infrastructure_overview' tool
```

### Search for Specific Devices
```
Use 'sm_search_devices' with name_filter="living room"
```

### List All Hosts
```
Access resource: sitemanager://hosts
```

### Get Device Details
```
Access resource: sitemanager://devices/{device_id}
```

## API Requirements

### Site Manager API Access
This server requires a valid UniFi Site Manager API key with read access to:
- Hosts endpoint (`/v1/hosts`)
- Sites endpoint (`/v1/sites`)  
- Devices endpoint (`/v1/devices`)

### Permissions
The API key needs permissions to access your UniFi infrastructure. The server will only work with data accessible to your UniFi account.

## Limitations

This server is optimized for basic Site Manager functionality. The following features are **not currently supported**:

- **ISP Metrics** - Requires specific UniFi subscription/plan
- **Local Network Control** - Requires local controller API access
- **UniFi Protect** - Requires Protect system and additional permissions
- **Advanced Analytics** - May require premium Site Manager features
- **Real-time Events** - Limited to polling-based data

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

**Connection Timeouts**
- Check internet connectivity
- Increase timeout value in secrets.env
- Verify Site Manager service status

### Debug Information
```bash
# Test endpoint connectivity
uv run test_working_features.py

# Get detailed site/host information
uv run get_site_host_ids.py
```

## Development

### Project Structure
```
unifi-mcp-server/
├── main.py              # Main MCP server
├── secrets.env          # Configuration (not in git)
├── test_working_features.py  # Endpoint testing
├── get_site_host_ids.py # ID discovery utility
└── README.md           # This file
```

### Adding Features
The server is designed to be extended as additional Site Manager endpoints become available. To add new functionality:

1. Add new resources in the Site Manager section
2. Create corresponding tools if needed
3. Add prompts for guided workflows
4. Test endpoint availability first

## Security

- Store API keys in `secrets.env` (not committed to git)
- Use HTTPS for all API communications
- API keys should be treated as sensitive credentials
- Consider rotating API keys periodically

## License

[Add your license information here]

## Contributing

[Add contributing guidelines here]

## Support

For UniFi-specific issues:
- [UniFi Community Forums](https://community.ui.com/)
- [Ubiquiti Support](https://help.ui.com/)

For MCP-related questions:
- [MCP Documentation](https://modelcontextprotocol.io/)

## Changelog

### Version 1.0
- Initial release with Site Manager support
- Infrastructure monitoring capabilities
- Device search and filtering
- Host and site management
