# 📚 UniFi MCP Server - Network Prompt Playbook

A comprehensive guide to network operations, commands, and AI-powered workflows for managing your UniFi infrastructure.

---

## Table of Contents
- [Getting Started](#getting-started)
- [General Commands](#-general-commands-beginner)
- [Intermediate Commands](#-intermediate-commands)
- [Advanced Commands](#-advanced-commands)
- [A2A Prompt Playbooks](#-a2a-prompt-playbooks)
- [Quick Reference](#quick-reference)

---

## Getting Started

This playbook provides natural language commands and structured operations for managing UniFi networks through the MCP server. Each command includes:
- **Description**: What the command does
- **Function**: The underlying tool/resource
- **A2A Prompt**: Related Agent-to-Agent workflow (if available)
- **Example**: Sample usage

---

## 🟢 General Commands (Beginner)

### Health & Status Monitoring

#### Check Overall Network Health
**Description**: Get a quick health check of your UniFi controller
**Function**: `unifi_health()`
**Resource**: `health://unifi`, `unifi://health`, `status://unifi`
**A2A Prompt**: `how_to_check_unifi_health`
**Example**:
```
"What's the health status of my UniFi network?"
"Is my UniFi controller responding?"
```

**Response includes**:
- Integration API availability
- Base URL and configuration
- TLS verification status

---

#### Get System Status Overview
**Description**: Comprehensive system health across all services
**Function**: `get_system_status(site_id?)`
**Resource**: `status://system`
**A2A Prompt**: `how_to_check_system_status`
**Example**:
```
"Show me the complete system status"
"Give me a comprehensive overview of my network health"
```

**Response includes**:
- Overall health status
- Service status (Integration, Devices, Clients, Access, Protect)
- Total devices, online/offline counts
- Total clients, active client counts
- Issues detected

---

#### Get Quick Status
**Description**: Fast overview of critical components
**Function**: `get_quick_status()`
**Example**:
```
"Quick status check"
"Fast network overview"
```

**Response includes**:
- Integration API status
- Device counts (total, online)
- Active client count
- Site ID

---

### Device Monitoring

#### List All Network Devices
**Description**: Display all UniFi network infrastructure
**Function**: `paginate_integration("/sites/{site_id}/devices")`
**Resource**: `sites://{site_id}/devices`
**A2A Prompt**: `how_to_monitor_devices`
**Example**:
```
"Show me all my network devices"
"List all switches and access points"
```

**Response includes**:
- Device name and model
- IP address and MAC address
- State (ONLINE/OFFLINE)
- Device type/features

---

#### Get Device Health Summary
**Description**: Detailed device health with uptime statistics
**Function**: `get_device_health(site_id?)`
**Resource**: `status://devices`
**A2A Prompt**: `how_to_monitor_devices`
**Example**:
```
"What's the health status of my devices?"
"Show me device uptime statistics"
```

**Response includes**:
- Total device count
- Devices by state (online/offline)
- Devices by type
- Uptime statistics (min/max/avg)
- List of offline devices (if any)

---

### Client Monitoring

#### List All Connected Clients
**Description**: Display all network clients
**Function**: `list_hosts(site_id?)`
**Resource**: `sites://{site_id}/clients`
**A2A Prompt**: `how_to_list_hosts`
**Example**:
```
"Who's connected to my network?"
"Show me all network clients"
```

**Response includes**:
- Client name/hostname
- IP address and MAC address
- Connection type (WIRED/WIRELESS)
- Connected timestamp

---

#### List Active Clients Only
**Description**: Show only currently connected clients
**Function**: `list_active_clients(site_id?)`
**Resource**: `sites://{site_id}/clients/active`
**Example**:
```
"Show me active clients"
"Who's currently connected?"
```

---

#### Get Client Activity Summary
**Description**: Client activity with bandwidth usage
**Function**: `get_client_activity(site_id?)`
**Resource**: `status://clients`
**A2A Prompt**: `how_to_check_network_activity`
**Example**:
```
"What's the current network activity?"
"Show me bandwidth usage by client"
```

**Response includes**:
- Active client count
- Connection types (wired vs wireless)
- Total bandwidth (RX/TX)
- Top bandwidth users

---

## 🟡 Intermediate Commands

### Search & Discovery

#### Search for Clients
**Description**: Find clients by name, MAC, or IP
**Resource**: `sites://{site_id}/search/clients/{query}`
**Example**:
```
"Find client with name 'iPhone'"
"Search for MAC address aa:bb:cc:dd:ee:ff"
```

**Query matches**:
- Client name (case-insensitive)
- Hostname
- MAC address (partial match)
- IP address

---

#### Search for Devices
**Description**: Find devices by name, model, or MAC
**Resource**: `sites://{site_id}/search/devices/{query}`
**A2A Prompt**: `how_to_find_device`
**Example**:
```
"Find my U7 Pro access point"
"Search for Dream Machine"
```

**Query matches**:
- Device name/hostname
- Model name
- MAC address

---

#### Find Device by MAC Address
**Description**: Locate specific device by MAC
**Function**: `find_device_by_mac(mac, site_id?)`
**Example**:
```python
find_device_by_mac("aa:bb:cc:dd:ee:ff")
```

---

#### Find Host Everywhere
**Description**: Search across local and cloud APIs
**Function**: `find_host_everywhere(identifier, site_id?)`
**Example**:
```python
find_host_everywhere("iPhone")
find_host_everywhere("aa:bb:cc:dd:ee:ff")
```

---

### Network Operations

#### Block Network Client
**Description**: Block a client from accessing the network
**Function**: `block_client(site_id, mac)`
**A2A Prompt**: `how_to_block_client`
**Example**:
```
"Block client with MAC aa:bb:cc:dd:ee:ff"
"Prevent device from connecting"
```

**⚠️ Warning**: This prevents the client from connecting until unblocked

---

#### Unblock Network Client
**Description**: Remove block from previously blocked client
**Function**: `unblock_client(site_id, mac)`
**A2A Prompt**: `how_to_block_client`
**Example**:
```
"Unblock client with MAC aa:bb:cc:dd:ee:ff"
"Restore network access for device"
```

---

#### Kick Client (Disconnect)
**Description**: Temporarily disconnect a client
**Function**: `kick_client(site_id, mac)`
**Example**:
```
"Disconnect client aa:bb:cc:dd:ee:ff"
"Kick device off the network"
```

**Note**: Client can reconnect immediately unless blocked

---

### WLAN Management

#### List Wireless Networks
**Description**: Display all configured WLANs
**Resource**: `sites://{site_id}/wlans`
**A2A Prompt**: `how_to_toggle_wlan`
**Example**:
```
"Show me all wireless networks"
"List configured SSIDs"
```

**Note**: Falls back to Legacy API if Integration API doesn't expose WLANs

---

#### Toggle WLAN (Enable/Disable)
**Description**: Enable or disable a wireless network
**Function**: `wlan_set_enabled_legacy(site_id, wlan_id, enabled)`
**A2A Prompt**: `how_to_toggle_wlan`
**Example**:
```python
wlan_set_enabled_legacy("site-id", "wlan-id", False)  # Disable
wlan_set_enabled_legacy("site-id", "wlan-id", True)   # Enable
```

**⚠️ Requires**: Legacy API credentials (username/password)

---

## 🔴 Advanced Commands

### Multi-API Operations

#### List Hosts (Cloud API Format)
**Description**: List hosts using Site Manager cloud API
**Function**: `list_hosts_api_format()`
**A2A Prompt**: `how_to_list_hosts`
**Example**:
```python
list_hosts_api_format()
```

**Returns**: Data in UniFi cloud API format

---

#### List Hosts (Auto Site Discovery)
**Description**: List hosts with automatic site ID discovery
**Function**: `list_hosts_fixed()`
**A2A Prompt**: `how_to_list_hosts`
**Example**:
```python
list_hosts_fixed()
```

**Features**:
- Auto-discovers correct site IDs
- No "default" site errors
- Uses Integration API

---

#### Working List Hosts (Recommended)
**Description**: Comprehensive host listing with cloud + local fallback
**Function**: `working_list_hosts_example()`
**A2A Prompt**: `how_to_list_hosts`
**Example**:
```python
working_list_hosts_example()
```

**Features**:
- Tries cloud API first
- Falls back to local Integration API
- Auto site discovery
- Best reliability

---

#### List All Hosts (Comprehensive)
**Description**: Full host listing from local + optional cloud
**Function**: `list_all_hosts(site_id?, include_cloud=False)`
**Example**:
```python
list_all_hosts(include_cloud=True)
```

**Returns**: Combined results from all sources

---

#### List Cloud Hosts Only
**Description**: List hosts via Site Manager cloud API
**Function**: `list_hosts_cloud(page_size=100)`
**Example**:
```python
list_hosts_cloud(page_size=50)
```

---

### Troubleshooting & Diagnostics

#### Debug API Connectivity
**Description**: Comprehensive API testing and diagnostics
**Function**: `debug_api_connectivity()`
**A2A Prompt**: `how_to_debug_api_issues`
**Example**:
```
"Test all API connections"
"Debug UniFi API issues"
"Why can't I see my devices?"
```

**Tests performed**:
- Cloud API connectivity
- Local controller reachability
- Integration API authentication
- Site discovery
- Environment configuration

**Returns**:
- Status of each test
- Error messages (if any)
- Configuration details
- Troubleshooting recommendations

---

#### Discover Sites
**Description**: Find valid site IDs on your controller
**Function**: `discover_sites()`
**A2A Prompt**: `how_to_debug_api_issues`
**Example**:
```python
discover_sites()
```

**Returns**: List of valid site IDs

---

#### Debug Registry
**Description**: Show all registered MCP resources and tools
**Function**: `debug_registry()`
**Example**:
```python
debug_registry()
```

**Returns**:
- All registered resources
- All registered tools
- Resource/tool metadata

---

#### Check Capabilities
**Description**: Show what APIs and features are available
**Resource**: `unifi://capabilities`
**Example**:
```
"What capabilities does the controller support?"
```

**Returns**:
- Integration API capabilities
- Access API availability
- Protect API availability
- Legacy API status
- Site Manager API status

---

### UniFi Protect (Camera Management)

#### Reboot Security Camera
**Description**: Restart a UniFi Protect camera
**Function**: `protect_camera_reboot(camera_id)`
**Example**:
```python
protect_camera_reboot("camera-12345")
```

**⚠️ Requires**: Protect API access (may require 2FA bypass)

---

#### Toggle Camera LED
**Description**: Turn camera LED on/off
**Function**: `protect_camera_led(camera_id, enabled)`
**Example**:
```python
protect_camera_led("camera-12345", False)  # Turn off
protect_camera_led("camera-12345", True)   # Turn on
```

---

#### Toggle Privacy Mode
**Description**: Enable/disable camera privacy mode
**Function**: `protect_toggle_privacy(camera_id, enabled)`
**Example**:
```python
protect_toggle_privacy("camera-12345", True)   # Enable privacy
protect_toggle_privacy("camera-12345", False)  # Disable privacy
```

---

### UniFi Access (Door Control)

#### Unlock Door
**Description**: Temporarily unlock an access-controlled door
**Function**: `access_unlock_door(door_id, seconds=5)`
**Example**:
```python
access_unlock_door("door-123", 10)  # Unlock for 10 seconds
```

**Default**: Unlocks for 5 seconds

---

### Device Identification

#### Locate Device (Flash LED)
**Description**: Flash LED on device for identification
**Function**: `locate_device(site_id, device_id, seconds=30)`
**A2A Prompt**: `how_to_find_device`
**Example**:
```python
locate_device("site-id", "device-id", 60)  # Flash for 60 seconds
```

**⚠️ Note**: May not be supported by Integration API (controller version dependent)

---

## 🤖 A2A Prompt Playbooks

Agent-to-Agent prompts provide guided workflows for complex operations.

### how_to_check_unifi_health
**Purpose**: Check UniFi controller health
**Workflow**:
1. Call `health://unifi` resource (or alternatives)
2. If unavailable, fall back to `unifi_health()` tool

**Use when**: Quick connectivity check needed

---

### how_to_check_system_status
**Purpose**: Get comprehensive system health overview
**Workflow**:
1. Use `get_system_status()` tool
2. Or query `status://system` resource

**Returns**: Complete health info for all services

---

### how_to_monitor_devices
**Purpose**: Monitor device health and identify issues
**Workflow**:
1. Use `get_device_health()` tool
2. Or query `status://devices` resource

**Returns**: Device counts, uptime stats, offline devices

---

### how_to_check_network_activity
**Purpose**: Check current network activity and client usage
**Workflow**:
1. Use `get_client_activity()` tool
2. Or query `status://clients` resource

**Returns**: Active clients, bandwidth usage, connection types

---

### how_to_find_device
**Purpose**: Find and physically locate a network device
**Workflow**:
1. Search via `sites://{site_id}/search/devices/{query}`
2. Confirm device with user
3. Call `locate_device()` to flash LED for ~30 seconds

**Safety**: Requires user confirmation before flashing LED

---

### how_to_block_client
**Purpose**: Safely block a network client
**Workflow**:
1. List clients via `sites://{site_id}/clients/active`
2. Match by MAC address or hostname
3. **Confirm with user** before blocking
4. Call `block_client()` to block
5. Offer `unblock_client()` as reversal option

**Safety**: Always confirms with user before blocking

---

### how_to_toggle_wlan
**Purpose**: Enable/disable wireless networks
**Workflow**:
1. Fetch WLANs via `sites://{site_id}/wlans`
2. If returns error (Integration API doesn't support):
   - Request legacy credentials from user
   - Call `wlan_set_enabled_legacy()`

**Fallback**: Automatically uses Legacy API when needed

---

### how_to_list_hosts
**Purpose**: List all hosts using multiple APIs
**Workflow Options**:
- `working_list_hosts_example()` - Complete working implementation
- `list_hosts_api_format()` - Cloud API format
- `list_hosts_fixed()` - Local API with site discovery
- `discover_sites()` - Find valid site IDs first (if needed)

**Recommendation**: Use `working_list_hosts_example()` for best results

---

### how_to_debug_api_issues
**Purpose**: Debug UniFi API connectivity problems
**Workflow**:
1. Use `debug_api_connectivity()` for comprehensive testing
2. Review error messages and recommendations
3. Check environment configuration
4. Verify API keys and credentials

**Returns**: Detailed diagnostics and troubleshooting steps

---

## Quick Reference

### Resource URI Patterns

| Resource | Pattern | Description |
|----------|---------|-------------|
| Health Check | `health://unifi` | Controller health |
| System Status | `status://system` | Complete system health |
| Device Status | `status://devices` | Device health summary |
| Client Status | `status://clients` | Client activity summary |
| Capabilities | `unifi://capabilities` | Available features |
| Devices | `sites://{site_id}/devices` | All network devices |
| Clients | `sites://{site_id}/clients` | All network clients |
| Active Clients | `sites://{site_id}/clients/active` | Connected clients |
| WLANs | `sites://{site_id}/wlans` | Wireless networks |
| Search Clients | `sites://{site_id}/search/clients/{query}` | Find clients |
| Search Devices | `sites://{site_id}/search/devices/{query}` | Find devices |

---

### Tool Categories

#### 🏥 Health & Monitoring
- `unifi_health()`
- `get_system_status()`
- `get_device_health()`
- `get_client_activity()`
- `get_quick_status()`

#### 👥 Client Management
- `list_hosts()`
- `list_active_clients()`
- `block_client()`
- `unblock_client()`
- `kick_client()`

#### 🔍 Search & Discovery
- `find_device_by_mac()`
- `find_host_everywhere()`
- `discover_sites()`

#### 📡 Multi-API Operations
- `list_hosts_api_format()`
- `list_hosts_fixed()`
- `working_list_hosts_example()`
- `list_all_hosts()`
- `list_hosts_cloud()`

#### 🛠️ Network Operations
- `locate_device()`
- `wlan_set_enabled_legacy()`

#### 📹 UniFi Protect
- `protect_camera_reboot()`
- `protect_camera_led()`
- `protect_toggle_privacy()`

#### 🚪 UniFi Access
- `access_unlock_door()`

#### 🔧 Troubleshooting
- `debug_api_connectivity()`
- `debug_registry()`

---

## Best Practices

### 🔒 Security
1. **Always confirm** before blocking clients
2. **Verify** device identity before operations
3. **Use read-only** operations when possible
4. **Store credentials** in `secrets.env` (never commit)

### ⚡ Performance
1. **Use caching** - Status data cached for 5 minutes
2. **Prefer Integration API** - Faster than Legacy API
3. **Pagination** - Automatic for large datasets
4. **Quick status** - Use `get_quick_status()` for fast checks

### 🎯 Reliability
1. **Auto site discovery** - Use tools that discover site IDs
2. **Fallback logic** - Tools automatically try multiple APIs
3. **Error handling** - All tools provide clear error messages
4. **A2A prompts** - Use guided workflows for complex operations

---

## Troubleshooting Common Issues

### "Site ID 'default' not valid"
**Solution**: Use `discover_sites()` or tools with auto-discovery
```python
discover_sites()  # Find correct site IDs
# Or use
working_list_hosts_example()  # Auto-discovers sites
```

### "401 Unauthorized"
**Solution**: Check API key configuration
```python
debug_api_connectivity()  # Full diagnostics
```

### "2FA Required" (Legacy API)
**Solutions**:
1. Use Integration API instead (preferred)
2. Create local admin without 2FA
3. Use app-specific passwords (if available)

### "Cannot locate device"
**Issue**: Integration API may not support LED locate
**Workaround**: Use UniFi controller web UI manually

---

## Examples by Use Case

### Morning Network Check
```
"What's the health status of my network?"
"Show me all connected devices"
"Are there any offline devices?"
```

### Troubleshooting Slow Network
```
"Who's using the most bandwidth?"
"Show me all active wireless clients"
"Which clients are connected to the IoT network?"
```

### Finding a Device
```
"Find my U7 Pro access point"
"Search for device with MAC aa:bb:cc:dd:ee:ff"
"Locate the bedroom access point"
```

### Guest Network Management
```
"Show me all wireless networks"
"Disable the guest network"
"Block unknown device with MAC xx:xx:xx:xx:xx:xx"
```

### Security Operations
```
"Block suspicious client"
"Show me all connected clients"
"Kick device off the network"
```

---

## Need Help?

- 📖 See [README.md](README.md) for installation and setup
- 🐛 Report issues at [GitHub Issues](https://github.com/ry-ops/unifi-mcp-server/issues)
- 🔧 Check [commands.md](commands.md) for additional examples
- 🗺️ See [roadmap.md](roadmap.md) for planned features

---

**Last Updated**: October 28, 2025
**MCP Version**: 1.0
**A2A Protocol**: Enabled
