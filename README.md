<img src="https://github.com/ry-ops/unifi-mcp-server/blob/main/unifi-mcp-server.png" width="100%">

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/badge/uv-latest-green.svg)](https://github.com/astral-sh/uv)
[![MCP](https://img.shields.io/badge/MCP-1.0-purple.svg)](https://modelcontextprotocol.io/)
[![A2A](https://img.shields.io/badge/A2A-enabled-orange.svg)](https://modelcontextprotocol.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
![CodeRabbit Pull Request Reviews](https://img.shields.io/coderabbit/prs/github/ry-ops/unifi-mcp-server?utm_source=oss&utm_medium=github&utm_campaign=ry-ops%2Funifi-mcp-server&labelColor=171717&color=FF570A&link=https%3A%2F%2Fcoderabbit.ai&label=CodeRabbit+Reviews)

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
Built-in A2A protocol enables AI agents to understand and execute complex UniFi operations through structured prompt playbooks and a comprehensive Agent Card:

**Agent Card**: [`agent-card.json`](agent-card.json) - Full A2A protocol specification including:
- 9 specialized skills (system health, device management, client monitoring, etc.)
- 30+ MCP tools mapped to agent capabilities
- 15+ resource URIs for data access
- Safety requirements and confirmation workflows
- Multi-API authentication support (local + cloud)
- Integration examples and usage patterns

**Available A2A Skills:**
1. **System Health Monitoring** - Controller health checks, comprehensive status, diagnostics
2. **Device Management** - Monitor network devices, locate with LED flash, track uptime
3. **Client Monitoring** - Track bandwidth, connection status, device activity
4. **Client Blocking** - Safely block/unblock/disconnect clients with confirmation
5. **WLAN Management** - Enable/disable wireless networks with automatic API fallback
6. **Protect Camera Management** - Control cameras, LEDs, privacy mode, reboots
7. **Access Door Control** - Unlock doors with timed duration
8. **Multi-Site Host Discovery** - List hosts across local and cloud with auto-discovery
9. **API Troubleshooting** - Debug connectivity, discover sites, validate config

**A2A Prompt Playbooks:**
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

For agent-to-agent communication, agents can:
1. Read the `agent-card.json` to discover capabilities
2. Use prompt playbooks to understand workflows
3. Execute tools with proper safety confirmations
4. Access resources via standardized URIs
5. Handle multi-API fallback automatically

## Prerequisites

- Python 3.10 or higher
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

## Agent-to-Agent (A2A) Protocol Integration

### Overview

This server fully implements the A2A protocol through a standardized Agent Card (`agent-card.json`) that enables AI agents to discover capabilities, understand workflows, and execute complex UniFi operations safely.

### Agent Card Location

The Agent Card is located at the repository root: [`agent-card.json`](agent-card.json)

### Discovering Agent Capabilities

AI agents can read the Agent Card to discover:

```json
{
  "name": "UniFi MCP Server",
  "version": "0.1.1",
  "capabilities": {
    "streaming": false,
    "tasks": true,
    "resources": true,
    "tools": true,
    "prompts": true
  },
  "skills": [
    {
      "name": "system_health_monitoring",
      "category": "monitoring",
      "prompts": ["how_to_check_unifi_health", "how_to_check_system_status"],
      "tools": ["unifi_health", "get_system_status", "get_quick_status"],
      "resources": ["health://unifi", "status://system"]
    }
    // ... 8 more skills
  ]
}
```

### A2A Skill Categories

The server provides 9 specialized skills organized by category:

**Monitoring Skills:**
- `system_health_monitoring` - Controller and infrastructure health
- `device_management` - Network device monitoring and control
- `client_monitoring` - Client activity and bandwidth tracking

**Control Skills:**
- `client_blocking` - Network access control (block/unblock/kick)
- `wlan_management` - Wireless network on/off control
- `protect_camera_management` - Camera control and privacy
- `access_door_control` - Physical access control

**Diagnostic Skills:**
- `multi_site_host_discovery` - Cross-site device discovery
- `api_troubleshooting` - Configuration and connectivity debugging

### Mapping Prompts to Skills

Each A2A prompt playbook maps to specific skills and workflows:

| Prompt | Skills | Tools Used | Safety Level |
|--------|--------|-----------|--------------|
| `how_to_check_unifi_health` | system_health_monitoring | unifi_health, debug_api_connectivity | Read-only |
| `how_to_check_system_status` | system_health_monitoring | get_system_status, get_quick_status | Read-only |
| `how_to_monitor_devices` | device_management | get_device_health, locate_device | Safe (LED flash) |
| `how_to_check_network_activity` | client_monitoring | get_client_activity, list_active_clients | Read-only |
| `how_to_find_device` | device_management | locate_device, find_device_by_mac | Safe (LED flash) |
| `how_to_block_client` | client_blocking | block_client, unblock_client | Requires confirmation |
| `how_to_toggle_wlan` | wlan_management | wlan_set_enabled_legacy | Requires confirmation |
| `how_to_list_hosts` | multi_site_host_discovery | working_list_hosts_example, discover_sites | Read-only |
| `how_to_debug_api_issues` | api_troubleshooting | debug_api_connectivity, discover_sites | Read-only |

### Using A2A for Agent-to-Agent Communication

**Example 1: Agent discovers and uses health monitoring**

```python
# Agent reads agent-card.json
agent_card = read_json("agent-card.json")

# Discovers system_health_monitoring skill
skill = agent_card["skills"][0]  # system_health_monitoring
prompt_name = skill["prompts"][0]  # how_to_check_unifi_health

# Executes prompt to get workflow
workflow = execute_prompt(prompt_name)
# Returns: "Call 'health://unifi' resource or 'unifi_health' tool"

# Executes recommended tool
result = execute_tool("unifi_health")
```

**Example 2: Agent safely blocks a client with confirmation**

```python
# Agent reads agent-card.json
skill = find_skill("client_blocking")

# Checks safety requirements
assert skill["safety"]["requires_confirmation"] == true
assert skill["safety"]["reversible"] == true

# Follows prompt playbook
workflow = execute_prompt("how_to_block_client")
# Returns: "List clients, match MAC, confirm with user, call block_client"

# Agent executes workflow:
# 1. List active clients
clients = read_resource("sites/{site_id}/clients/active")

# 2. Match client by MAC/hostname
target = match_client(clients, user_query)

# 3. Confirm with user (required by safety policy)
confirmed = confirm_with_user(f"Block {target['hostname']}?")

# 4. Execute if confirmed
if confirmed:
    result = execute_tool("block_client", site_id, target["mac"])
    # 5. Offer reversal
    inform_user("Use 'unblock_client' to reverse this action")
```

### A2A Safety Model

The Agent Card specifies safety requirements for each skill:

```json
{
  "skill": "client_blocking",
  "safety": {
    "requires_confirmation": true,
    "reversible": true,
    "description": "Always confirm client identity before blocking. Offer unblock_client as reversal option."
  }
}
```

**Safety Levels:**
- **Read-only** - No confirmation required (monitoring, discovery, health checks)
- **Safe actions** - Minor impact, no confirmation (LED flash, device locate)
- **Reversible actions** - Requires confirmation, can be undone (block client, toggle WLAN)
- **Irreversible actions** - Requires confirmation, auto-reverts (unlock door with timeout)

### Authentication for A2A

The Agent Card documents all authentication methods:

```json
{
  "authentication": {
    "required": true,
    "methods": [
      {
        "type": "api_key",
        "name": "local_controller",
        "env_vars": ["UNIFI_API_KEY", "UNIFI_GATEWAY_HOST", "UNIFI_GATEWAY_PORT"]
      },
      {
        "type": "api_key",
        "name": "site_manager",
        "env_vars": ["UNIFI_SITEMGR_TOKEN", "UNIFI_SITEMGR_BASE"]
      },
      {
        "type": "credentials",
        "name": "legacy_api",
        "env_vars": ["UNIFI_USERNAME", "UNIFI_PASSWORD"]
      }
    ],
    "fallback": "Server intelligently falls back between APIs based on availability"
  }
}
```

Agents can discover which authentication methods are available and required for different operations.

### Resource URI Patterns

The Agent Card documents standardized resource URI patterns for discovery:

**System Status:**
- `status://system` - Comprehensive system health
- `status://devices` - Device health summary
- `status://clients` - Client activity summary
- `health://unifi` - Quick controller health check

**Site-based Resources:**
- `sites://{site_id}/devices` - List all devices
- `sites://{site_id}/clients` - List all clients (historical)
- `sites://{site_id}/clients/active` - Currently connected clients only
- `sites://{site_id}/wlans` - Wireless network configuration

**Search Resources:**
- `sites://{site_id}/search/clients/{query}` - Search clients
- `sites://{site_id}/search/devices/{query}` - Search devices

**Cloud Resources:**
- `sitemanager://hosts` - List all UniFi OS consoles
- `sitemanager://sites` - List all network sites
- `sitemanager://devices` - List devices across infrastructure

### Example A2A Integration Workflows

**Workflow 1: Health Check and Report**
```
1. Agent reads agent-card.json
2. Identifies "system_health_monitoring" skill
3. Executes prompt "how_to_check_system_status"
4. Calls tool "get_system_status"
5. Reads resources: status://system, status://devices, status://clients
6. Generates comprehensive report
```

**Workflow 2: Find and Locate Device**
```
1. Agent receives request: "Find the bedroom access point"
2. Reads agent-card.json, identifies "device_management" skill
3. Executes prompt "how_to_find_device"
4. Searches: sites/{site_id}/search/devices/bedroom
5. Confirms device with user
6. Calls tool "locate_device" to flash LEDs for 30s
```

**Workflow 3: Multi-Site Discovery**
```
1. Agent needs to list all infrastructure
2. Reads agent-card.json, identifies "multi_site_host_discovery" skill
3. Executes prompt "how_to_list_hosts"
4. Calls tool "working_list_hosts_example" (combines local + cloud)
5. Falls back to "discover_sites" if site IDs unknown
6. Returns unified host list across all sites
```

### Benefits of A2A Protocol Support

1. **Discoverability** - Agents can introspect capabilities without documentation
2. **Safety** - Structured confirmation workflows prevent accidents
3. **Consistency** - Standardized skill definitions across all agents
4. **Composability** - Skills can be combined for complex workflows
5. **Fallback handling** - Multi-API support with automatic fallback
6. **Documentation** - Agent Card serves as both spec and documentation

### For Agent Developers

To integrate with this A2A-enabled UniFi server:

1. **Read the Agent Card**: Parse `agent-card.json` to discover all capabilities
2. **Map user intents to skills**: Match user requests to skill categories
3. **Follow prompt playbooks**: Use prompts to understand multi-step workflows
4. **Respect safety requirements**: Always confirm before executing operations marked `requires_confirmation: true`
5. **Handle authentication**: Support multiple auth methods (local + cloud)
6. **Use resource URIs**: Access data through standardized resource patterns
7. **Provide reversibility**: Offer reversal options for reversible operations

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
