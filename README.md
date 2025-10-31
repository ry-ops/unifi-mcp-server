# UniFi MCP Server

A Model Context Protocol (MCP) server that integrates UniFi network equipment with AI assistants, exposing UniFi Network, Access, and Protect APIs through a standardized interface.

## Overview

This MCP server enables AI assistants to interact with UniFi controllers, providing:

- **Resources** (read-only): Sites, devices, clients, networks, cameras, access control
- **Tools** (safe write operations): Block/kick clients, locate devices, unlock doors, reboot cameras
- **Prompts** (AI guidance): Step-by-step workflows for common tasks

### Supported UniFi Products

- UniFi Network (switches, access points, gateways)
- UniFi Access (door locks, readers)
- UniFi Protect (cameras, NVR)

## Features

- Dual authentication (API key + legacy cookie fallback)
- Automatic pagination for large datasets
- Health check endpoints for monitoring
- Safe operation design (confirmation required for destructive actions)
- TLS verification configurable for self-signed certificates

## Prerequisites

- Python 3.12 or higher
- UniFi Controller/Gateway (Cloud Key, Dream Machine, or self-hosted)
- UniFi API key (recommended) or username/password (legacy)
- Network access to UniFi controller

## Installation

### 1. Clone or download this repository

```bash
git clone <repository-url>
cd mcp-server-unifi
```

### 2. Install uv package manager (if not already installed)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 3. Create virtual environment and install dependencies

```bash
uv venv
uv pip install -e .
```

### 4. Configure credentials

Create a `secrets.env` file in the project root:

```bash
# UniFi Controller Settings
UNIFI_API_KEY=your_actual_api_key_here
UNIFI_GATEWAY_HOST=192.168.1.1
UNIFI_GATEWAY_PORT=443
UNIFI_VERIFY_TLS=false

# Legacy credentials (optional, for endpoints not in Integration API)
UNIFI_USERNAME=admin
UNIFI_PASSWORD=your_password

# Site Manager Settings (optional, for cloud API)
UNIFI_SITEMGR_BASE=https://api.ui.com
UNIFI_SITEMGR_TOKEN=your_site_manager_api_key
UNIFI_SITEMGR_PREFIX=/v1

# Request timeout (optional, default 15 seconds)
UNIFI_TIMEOUT_S=15
```

**Important:** Never commit `secrets.env` to version control. This file is excluded in `.gitignore`.

## Getting Your UniFi API Key

### Method 1: UniFi OS Console (Recommended)

1. Log into your UniFi controller web interface
2. Navigate to **Settings** > **System** > **API**
3. Click **Create New API Key**
4. Give it a name (e.g., "MCP Server")
5. Copy the generated key immediately (it won't be shown again)

### Method 2: Legacy Username/Password

If your controller doesn't support API keys, you can use username/password authentication:

1. Use your existing UniFi admin username and password
2. Set `UNIFI_USERNAME` and `UNIFI_PASSWORD` in `secrets.env`
3. The server will automatically use cookie-based authentication

**Note:** API key authentication is more secure and recommended for production use.

## Usage

### Running the Server

```bash
python main.py
```

The server runs on stdio transport, suitable for integration with MCP clients.

### Testing Connection

Use the health check to verify connectivity:

```python
# Resource endpoints:
# - unifi://health
# - health://unifi
# - status://unifi

# Or use the tool:
unifi_health()
```

### Available Resources

Resources are read-only data endpoints:

```
sites://                              # List all sites
sites://{site_id}/devices             # List devices
sites://{site_id}/clients             # List all clients
sites://{site_id}/clients/active      # List active clients only
sites://{site_id}/wlans               # List wireless networks
sites://{site_id}/search/devices/{query}   # Search devices
sites://{site_id}/search/clients/{query}   # Search clients

access://doors                        # List access control doors
access://readers                      # List access control readers
access://users                        # List access control users
access://events                       # List access control events

protect://nvr                         # Get NVR status
protect://cameras                     # List all cameras
protect://camera/{camera_id}          # Get specific camera
protect://events                      # List motion/smart detection events
protect://events/range/{start}/{end}  # Get events in time range
protect://streams/{camera_id}         # Get camera stream URLs

unifi://capabilities                  # Test all API endpoints
```

### Available Tools

Tools perform safe write operations:

#### Network Tools
- `block_client(site_id, mac)` - Block a client from the network
- `unblock_client(site_id, mac)` - Unblock a previously blocked client
- `kick_client(site_id, mac)` - Force disconnect a client
- `locate_device(site_id, device_id, seconds=30)` - Flash device LEDs

#### Legacy Network Tools
- `wlan_set_enabled_legacy(site_id, wlan_id, enabled)` - Toggle wireless network

#### Access Control Tools
- `access_unlock_door(door_id, seconds=5)` - Momentarily unlock a door

#### Protect Tools
- `protect_camera_reboot(camera_id)` - Reboot a camera
- `protect_camera_led(camera_id, enabled)` - Toggle camera LED
- `protect_toggle_privacy(camera_id, enabled)` - Toggle privacy mode

#### Utility Tools
- `unifi_health()` - Check controller connectivity
- `debug_registry()` - List all registered resources/tools/prompts

### Available Prompts

Prompts guide AI assistants through common workflows:

- `how_to_check_unifi_health` - Verify controller connectivity
- `how_to_find_device` - Search and locate a network device
- `how_to_block_client` - Find and block a problematic client
- `how_to_toggle_wlan` - Enable/disable a wireless network
- `how_to_manage_access` - Control door access
- `how_to_find_camera` - Find camera streams
- `how_to_review_motion` - Review motion detection events
- `how_to_reboot_camera` - Safely reboot a camera

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `UNIFI_API_KEY` | Yes* | - | Integration API key from controller |
| `UNIFI_GATEWAY_HOST` | Yes | - | Controller IP address or hostname |
| `UNIFI_GATEWAY_PORT` | No | 443 | Controller HTTPS port |
| `UNIFI_VERIFY_TLS` | No | false | Verify TLS certificates |
| `UNIFI_USERNAME` | No** | - | Legacy username for cookie auth |
| `UNIFI_PASSWORD` | No** | - | Legacy password for cookie auth |
| `UNIFI_TIMEOUT_S` | No | 15 | HTTP request timeout in seconds |
| `UNIFI_SITEMGR_BASE` | No | - | Site Manager cloud API base URL |
| `UNIFI_SITEMGR_TOKEN` | No | - | Site Manager API token |

\* Either `UNIFI_API_KEY` or `UNIFI_USERNAME`/`UNIFI_PASSWORD` required
\*\* Required if API key not available or for legacy endpoints

### TLS Certificate Verification

By default, TLS verification is disabled (`UNIFI_VERIFY_TLS=false`) to support self-signed certificates common in UniFi deployments. For production environments with valid certificates, set:

```bash
UNIFI_VERIFY_TLS=true
```

## Architecture

### Authentication Strategy

The server uses a dual-mode authentication approach:

1. **Primary: API Key** - Modern Integration API endpoints
2. **Fallback: Cookie Auth** - Legacy endpoints and older controllers

The server automatically tries API key first, then falls back to cookie authentication if needed.

### API Coverage

- **Integration API** (`/proxy/network/integrations/v1/...`) - Primary interface for sites, devices, clients
- **Legacy API** (`/proxy/network/api/s/{site}/...`) - Fallback for WLANs, firewall rules
- **Access API** (`/proxy/access/api/v1/...`) - Door locks and access control
- **Protect API** (`/proxy/protect/api/...`) - Cameras and NVR

### URL Building

All URLs are built using safe joining to prevent line-wrap identifier breaks:

```python
url = "/".join([base, "path", "component"])
```

## Security Best Practices

### Credential Management

1. **Never commit secrets**: The `secrets.env` file is git-ignored
2. **Use API keys**: Preferred over username/password for better security
3. **Restrict API key permissions**: Create keys with minimal required permissions
4. **Rotate credentials regularly**: Update API keys periodically
5. **Use environment isolation**: Keep production and development credentials separate

### Network Security

1. **Use TLS verification**: Enable `UNIFI_VERIFY_TLS=true` with valid certificates
2. **Restrict network access**: Run server on trusted networks only
3. **Firewall rules**: Limit controller access to authorized IPs
4. **VPN recommended**: Access controllers through VPN when possible

### Operational Security

1. **Confirm destructive actions**: Tools require explicit confirmation
2. **Monitor audit logs**: Review UniFi controller logs regularly
3. **Limit tool usage**: Only enable tools your workflow requires
4. **Test in staging**: Verify operations in non-production environment first

## Troubleshooting

### Connection Issues

**Problem:** Server can't connect to controller

```bash
# Check controller is reachable
ping <UNIFI_GATEWAY_HOST>

# Check port is open
nc -zv <UNIFI_GATEWAY_HOST> 443

# Verify API key/credentials
# Run health check: unifi_health()
```

**Problem:** TLS certificate errors

```bash
# Temporarily disable verification for self-signed certs
UNIFI_VERIFY_TLS=false
```

### Authentication Issues

**Problem:** 401 Unauthorized errors

- Verify API key is correct and active
- Check API key hasn't expired
- Ensure API key has required permissions
- Try legacy username/password as fallback

**Problem:** 403 Forbidden errors

- API key may lack permissions for specific endpoint
- Check UniFi controller user role and permissions
- Some endpoints require admin-level access

### Resource Not Found

**Problem:** Resource shows as unavailable

```bash
# Check what's registered
debug_registry()

# Test API endpoint availability
# Access: unifi://capabilities
```

### Legacy API Fallback

**Problem:** WLANs or other features not working

- Ensure `UNIFI_USERNAME` and `UNIFI_PASSWORD` are set
- Legacy credentials required for endpoints not in Integration API
- Check controller version supports required endpoints

## Development

### Project Structure

```
mcp-server-unifi/
   main.py              # Main server implementation
   secrets.env          # Credentials (not in git)
   pyproject.toml       # Python dependencies
   uv.lock              # Locked dependency versions
   .gitignore           # Git exclusions
   .python-version      # Python version specification
   README.md            # This file
   CLAUDE.md            # Development guidance for AI assistants
```

### Adding New Features

#### Adding a Resource

```python
@mcp.resource("custom://resource/{param}")
async def my_resource(param: str) -> Dict[str, Any]:
    # Fetch data from UniFi API
    return data
```

#### Adding a Tool

```python
@mcp.tool()
def my_tool(param: str) -> Dict[str, Any]:
    """Clear description of what this tool does."""
    # Validate inputs
    # Perform operation
    # Return structured response
    return {"success": True, "message": "Operation completed"}
```

#### Adding a Prompt

```python
@mcp.prompt("how_to_do_something")
def my_prompt():
    return {
        "description": "Brief description",
        "messages": [{
            "role": "system",
            "content": "Step-by-step workflow instructions"
        }]
    }
```

### Code Quality

```bash
# Format code
black main.py

# Lint
ruff check main.py

# Type check
mypy main.py
```

## Known Limitations

1. **No automated tests**: Testing framework not yet implemented
2. **Single-file architecture**: May need refactoring for large-scale features
3. **Limited Protect support**: Basic camera operations only
4. **Site Manager stub**: Cloud API not fully implemented
5. **No CI/CD**: Manual deployment required

## Roadmap

### Week 1 (Critical Fixes) - COMPLETED
- [x] Fix filename typo (secreds.ev ’ secrets.env)
- [x] Update .gitignore for credential files
- [x] Create comprehensive README
- [ ] Add input validation for tool parameters

### Week 2-4 (Security & Quality)
- [ ] Add comprehensive input validation and sanitization
- [ ] Implement rate limiting for API calls
- [ ] Add logging and audit trail
- [ ] Security vulnerability scanning
- [ ] Implement pytest test suite
- [ ] Add error handling improvements
- [ ] Create example configurations

### Future Enhancements
- [ ] Support for UniFi Talk (VoIP)
- [ ] Advanced Protect features (video clips, timelapse)
- [ ] Firewall rule management
- [ ] Network topology mapping
- [ ] Real-time event streaming
- [ ] Multi-controller support
- [ ] Web dashboard for monitoring

## Contributing

Contributions welcome! Please:

1. Follow existing code style
2. Add tests for new features
3. Update documentation
4. Never commit secrets or credentials
5. Test against real UniFi hardware if possible

## License

[Specify your license here]

## Support

For issues, questions, or contributions:

- Open an issue on GitHub
- Check UniFi documentation: https://help.ui.com
- Review MCP specification: https://modelcontextprotocol.io

## Acknowledgments

- Built with [FastMCP](https://github.com/jlowin/fastmcp)
- UniFi API documentation and community
- Model Context Protocol specification

---

**Security Notice:** This server provides direct access to your UniFi network infrastructure. Use appropriate security measures and only run in trusted environments.
