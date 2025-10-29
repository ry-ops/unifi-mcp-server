<img src="https://github.com/ry-ops/unifi-mcp-server/blob/main/unifi-mcp-server.png" width="100%">

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/badge/uv-latest-green.svg)](https://github.com/astral-sh/uv)
[![MCP](https://img.shields.io/badge/MCP-1.0-purple.svg)](https://modelcontextprotocol.io/)
[![A2A](https://img.shields.io/badge/A2A-enabled-orange.svg)](https://modelcontextprotocol.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

# UniFi MCP Server - Comprehensive Infrastructure Management

A Model Context Protocol (MCP) server for comprehensive UniFi infrastructure monitoring and management. This server enables natural language interactions with your UniFi network using AI agents like Claude by integrating with both local UniFi controllers and the cloud-based Site Manager API.

**✨ Features Agent-to-Agent (A2A) Protocol** for intelligent, multi-step network operations with built-in safety checks and guided workflows.

## Features

### 🌐 **Dual API Support**
- **Local Controller Integration** - Direct access to your UniFi controller via Integration API
- **Cloud Site Manager** - Monitor infrastructure via UniFi Site Manager API
- **Smart Fallback** - Automatically discovers correct site IDs and switches between APIs

### 📊 **Comprehensive Monitoring**
- Real-time device health and status monitoring
- Client activity tracking and bandwidth analysis
- Network performance insights and uptime statistics
- Comprehensive system health overview with issue detection

### 🔧 **Full UniFi Ecosystem Support**
- **Network Controller** - Complete network management
- **UniFi Protect** - Camera and security system integration
- **UniFi Access** - Door and access control management
- **UniFi Talk** - VoIP system monitoring
- **Additional Apps** - Connect, Innerspace, and more

### 🤖 **AI-Powered Management**
- Natural language queries for complex network operations
- Intelligent device discovery and management
- Automated troubleshooting and diagnostics
- Smart status reporting and alerting

### 🔗 **Agent-to-Agent (A2A) Protocol**
Built-in A2A protocol enables AI agents to understand and execute complex UniFi operations through structured prompt playbooks:

**Available A2A Prompts:**
- **`how_to_check_unifi_health`** - Check controller health and connectivity
- **`how_to_check_system_status`** - Get comprehensive system health overview
- **`how_to_monitor_devices`** - Monitor device health and identify issues
- **`how_to_check_network_activity`** - Check client activity and bandwidth usage
- **`how_to_find_device`** - Search devices and flash LEDs for identification
- **`how_to_block_client`** - Safely block/unblock network clients
- **`how_to_toggle_wlan`** - Enable/disable wireless networks
- **`how_to_list_hosts`** - List all hosts across local and cloud APIs
- **`how_to_debug_api_issues`** - Debug API connectivity problems

These prompts guide AI agents through multi-step workflows, ensuring safe and correct execution of network operations. Each prompt includes:
- Clear step-by-step instructions
- Required tool calls and resource queries
- Safety checks and user confirmations
- Fallback strategies for error handling

## Prerequisites

- Python 3.8 or higher
- `uv` package manager
- UniFi controller (Dream Machine, Cloud Key, etc.) OR UniFi Site Manager account
- API access configured (local API key and/or Site Manager API key)

## Setup

### 1. **API Key Configuration**

#### **For Local Controller Access:**
- Access your UniFi controller web interface
- Go to Settings > Admins > Add Admin (or create API key in newer versions)
- Note your controller IP address and port (typically 443)

#### **For Cloud Site Manager Access:**
- Go to [UniFi Site Manager](https://unifi.ui.com)
- Navigate to API section from the left navigation bar
- Click "Create API Key"
- Copy the generated key (it will only be displayed once)

### 2. **Installation**

```bash
git clone https://github.com/ry-ops/unifi-mcp-server.git
cd unifi-mcp-server
uv venv
source .venv/bin/activate  # On Unix/macOS
# or
.venv\Scripts\activate  # On Windows
uv sync
```

### 3. **Configuration**

Create a `secrets.env` file in the project root:

```env
# Local Controller Configuration
UNIFI_API_KEY=your_local_controller_api_key_here
UNIFI_GATEWAY_HOST=10.88.140.144
UNIFI_GATEWAY_PORT=443
UNIFI_VERIFY_TLS=false

# Legacy API (optional, for WLANs and advanced config)
UNIFI_USERNAME=your_unifi_username
UNIFI_PASSWORD=your_unifi_password

# Cloud Site Manager Configuration
UNIFI_SITEMGR_BASE=https://api.ui.com
UNIFI_SITEMGR_TOKEN=your_site_manager_api_key_here

# Optional Settings
UNIFI_TIMEOUT_S=15
```

## Running the Server

### **Development Mode**
```bash
uv run mcp dev main.py
```
The MCP Inspector will be available at http://localhost:5173 for testing and debugging.

### **Production Mode**
```bash
uv run main.py
```

## Testing Your Setup

Verify your configuration with these commands:

```bash
# Test all API connectivity
uv run python -c "
from main import debug_api_connectivity, working_list_hosts_example, get_system_status
print('=== API Connectivity Test ===')
print(debug_api_connectivity())
print('\n=== Working Host List Example ===')
print(working_list_hosts_example())
print('\n=== System Status ===')
print(get_system_status())
"
```

## AI Agent Integration

### **Claude Desktop Setup**

Add to your `claude_desktop_config.json`:

```json
{
    "mcpServers": {
        "unifi": {
            "command": "uv",
            "args": [
                "--directory",
                "/path/to/unifi-mcp-server",
                "run",
                "main.py"
            ]
        }
    }
}
```

### **Environment Variable Alternative**
```json
{
    "mcpServers": {
        "unifi": {
            "command": "uv",
            "args": [
                "--directory",
                "/path/to/unifi-mcp-server",
                "run",
                "main.py"
            ],
            "env": {
                "UNIFI_API_KEY": "your_local_api_key",
                "UNIFI_SITEMGR_TOKEN": "your_cloud_api_key"
            }
        }
    }
}
```

## Available Resources

### **System Status**
- `status://system` - Comprehensive system health overview
- `status://devices` - Device health and uptime monitoring
- `status://clients` - Client activity and bandwidth analysis
- `health://unifi` - Quick controller health check

### **Network Infrastructure**
- `sites://{site_id}/devices` - List all network devices
- `sites://{site_id}/clients` - List all network clients
- `sites://{site_id}/clients/active` - Currently connected clients only
- `sites://{site_id}/wlans` - Wireless network configuration

### **Search and Discovery**
- `sites://{site_id}/search/clients/{query}` - Search clients by name/MAC/IP
- `sites://{site_id}/search/devices/{query}` - Search devices by name/model/MAC

### **Cloud Resources**
- `sitemanager://hosts` - List all UniFi OS consoles
- `sitemanager://sites` - List all network sites
- `sitemanager://devices` - List all devices across infrastructure

### **Capabilities**
- `unifi://capabilities` - System capability assessment

## Available Tools

### **System Monitoring**
- `get_system_status()` - Complete system health overview
- `get_device_health()` - Device uptime and status analysis
- `get_client_activity()` - Network usage and bandwidth monitoring
- `get_quick_status()` - Fast health check

### **Host and Device Management**
- `working_list_hosts_example()` - Comprehensive host listing (cloud + local)
- `list_hosts_api_format()` - Cloud API host listing
- `list_hosts_fixed()` - Local API with auto-discovered site IDs
- `find_device_by_mac(mac)` - Locate device by MAC address
- `find_host_everywhere(identifier)` - Search across all sources

### **Network Operations**
- `block_client(site_id, mac)` - Block a network client
- `unblock_client(site_id, mac)` - Unblock a network client
- `kick_client(site_id, mac)` - Disconnect a client
- `locate_device(site_id, device_id)` - Flash device LEDs for identification

### **UniFi Protect**
- `protect_camera_reboot(camera_id)` - Reboot security camera
- `protect_camera_led(camera_id, enabled)` - Control camera LED
- `protect_toggle_privacy(camera_id, enabled)` - Toggle privacy mode

### **UniFi Access**
- `access_unlock_door(door_id, seconds)` - Unlock access-controlled door

### **Troubleshooting**
- `debug_api_connectivity()` - Comprehensive API testing
- `discover_sites()` - Find valid site IDs
- `debug_registry()` - Show all registered resources and tools
- `unifi_health()` - Basic controller connectivity test

## Example Usage

Once integrated with Claude Desktop, you can ask natural language questions like:

### **Network Overview**
- *"Tell me about my UniFi network"*
- *"Give me a comprehensive overview of my infrastructure"*
- *"What's the current health status of my network?"*

### **Device Management**
- *"Show me all offline devices"*
- *"Find devices with 'bedroom' in the name"*
- *"What's the uptime of my access points?"*
- *"Flash the LEDs on the living room access point"*

### **Client Monitoring**
- *"Who's using the most bandwidth right now?"*
- *"Show me all wireless clients"*
- *"Block the device with MAC address XX:XX:XX:XX:XX:XX"*

### **Security and Access**
- *"Unlock the front door for 10 seconds"*
- *"Reboot the camera in the hallway"*
- *"Turn on privacy mode for all cameras"*

### **Troubleshooting**
- *"Why can't I see my devices?"*
- *"Test all my API connections"*
- *"What sites are available on my controller?"*

## Architecture

### **Multi-API Design**
The server intelligently manages multiple UniFi APIs:

1. **Integration API** (Local) - Primary for real-time network operations
2. **Legacy API** (Local) - Fallback for WLAN management and older features  
3. **Site Manager API** (Cloud) - Infrastructure overview and remote monitoring
4. **Protect API** - Camera and security system integration
5. **Access API** - Door and access control management

### **Smart Fallback Logic**
- Automatically discovers correct site IDs (no more "default" errors)
- Falls back between cloud and local APIs based on availability
- Handles authentication failures gracefully
- Provides detailed error messages for troubleshooting

### **Caching and Performance**
- 5-minute caching for status data to reduce API load
- Pagination support for large device lists
- Efficient bulk operations for comprehensive reporting

## Troubleshooting

### **Common Issues**

#### **Site ID Errors**
```
Error: 'default' is not a valid 'siteId' value
```
**Solution:** Run `discover_sites()` tool to find correct site IDs. The server now handles this automatically.

#### **Authentication Issues**
```
Error: 401 Unauthorized or 2FA Required
```
**Solutions:**
- Verify API keys are correct and not expired
- For local controller: Check if 2FA is enabled (may require app-specific passwords)
- For cloud: Regenerate Site Manager API key

#### **Connection Issues**
```
Error: Connection timeout or unreachable
```
**Solutions:**
- Verify controller IP address and port in `secrets.env`
- Check firewall rules and network connectivity
- Test with `debug_api_connectivity()` tool

### **Debug Commands**

```bash
# Comprehensive API testing
python -c "from main import debug_api_connectivity; print(debug_api_connectivity())"

# Discover site IDs
python -c "from main import discover_sites; print(discover_sites())"

# Test working host listing
python -c "from main import working_list_hosts_example; print(working_list_hosts_example())"

# System health check
python -c "from main import get_system_status; print(get_system_status())"
```

## Security Best Practices

- **Store credentials securely** - Use `secrets.env` (excluded from version control)
- **Use HTTPS** - All API communications are encrypted
- **Rotate API keys regularly** - Especially for production environments
- **Principle of least privilege** - Create dedicated API users with minimal required permissions
- **Monitor access logs** - Review API usage in UniFi controller logs

## Supported UniFi Hardware

### **Controllers**
- UniFi Dream Machine (UDM)
- UniFi Dream Machine Pro (UDM-Pro)
- UniFi Dream Machine SE (UDM-SE)
- UniFi Cloud Key Gen2/Gen2 Plus
- UniFi Network Application (self-hosted)

### **Applications**
- **Network** - All UniFi networking equipment
- **Protect** - Security cameras and NVRs
- **Access** - Door controllers and readers
- **Talk** - VoIP phones and controllers
- **Connect** - SD-WAN and remote connectivity

## Limitations

### **Current Limitations**
- **2FA Handling** - Legacy API requires manual 2FA bypass or app passwords
- **Bulk Operations** - Some operations limited by UniFi API rate limits
- **Real-time Events** - No WebSocket support (polling-based monitoring)

### **Planned Features**
- WebSocket support for real-time events
- Enhanced Protect integration (video streams, motion detection)
- Advanced analytics and reporting
- Automated network optimization suggestions

## Contributing

### **Development Setup**
1. Fork the repository
2. Create a feature branch
3. Test with multiple UniFi configurations
4. Update documentation for new features
5. Submit pull request

### **Testing Guidelines**
- Test with both local and cloud APIs
- Verify functionality across different UniFi hardware
- Include error handling and edge cases
- Update example usage for new features

## License

MIT License - see LICENSE file for details.

## Support

- **Issues:** GitHub Issues for bug reports and feature requests
- **Documentation:** Check the troubleshooting section first
- **Community:** UniFi community forums for general UniFi questions

---

**Note:** This server provides comprehensive UniFi infrastructure management through AI-powered natural language interactions. It's designed for both home labs and enterprise environments with robust error handling and multi-API support.
