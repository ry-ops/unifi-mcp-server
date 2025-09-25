<img src="https://github.com/ry-ops/unifi-mcp-server/blob/main/UniFi-MCP-Server.png" width="100%">

<p align="center">
  <a href="#-features"><img alt="Status" src="https://img.shields.io/badge/Status-Active-brightgreen"></a>
  <a href="#-setup"><img alt="uv" src="https://img.shields.io/badge/Runtime-uv-blue"></a>
  <a href="LICENSE"><img alt="License" src="https://img.shields.io/badge/License-MIT-informational"></a>
</p>

# UniFi MCP Server

A server implementation for managing and controlling UniFi network devices through MCP (Management Control Protocol). This server enables natural language interactions with your UniFi network using AI agents like Goose and Claude by wrapping the UniFi Network Integration API with Legacy API fallback.

## Features

- Query UniFi **sites, devices, and clients** using natural language through AI agents
- Search functionality for finding specific devices and clients
- WLAN management with graceful fallback to Legacy API when needed
- Health monitoring and capability probing
- Supports both the **Integration API** (modern, key-based) and **Legacy API** (session login fallback)  
- Local server implementation that connects directly to your UniFi console
- Compatible with Claude Desktop and other MCP clients
- Secure API key-based authentication with optional legacy fallback

## Prerequisites

- Python 3.8 or higher
- Install <a href="https://docs.astral.sh/uv/getting-started/" rel>`uv`</a> which we'll use for managing the Python project.
- UniFi Network application (running locally or on UniFi OS)
- UniFi API key (obtained from UniFi console)

## Setup

1. **Create an API key:**
   - Go to your UniFi console at https://unifi.ui.com
   - Navigate to **Settings » Control Plane » Integrations**
   - Click **Create API Key**

2. Clone and set up the repository:
```bash
git clone https://github.com/zcking/mcp-server-unifi
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

```bash
# UniFi Controller Settings
UNIFI_API_KEY=your_actual_api_key_here
UNIFI_GATEWAY_HOST=192.168.1.1
UNIFI_GATEWAY_PORT=443
UNIFI_VERIFY_TLS=false

# Legacy credentials (optional - for WLAN management fallback)
UNIFI_USERNAME=admin
UNIFI_PASSWORD="your_password_with_special_chars!"
```

## Running the Server

Start the MCP development server:

```bash
uv run mcp dev main.py
```
The MCP Inspector will be available at [http://localhost:5173](http://localhost:5173) with a randomly assigned port (typically 5173+) and will automatically launch in a new browser window for testing and debugging.

## AI Agent Integration

### Goose AI Setup

1. Open Goose and go to **Settings » Extensions » Add custom extension**
2. Configure the extension:

   * **ID:** unifi
   * **Name:** unifi
   * **Description:** Get information about your UniFi network
   * **Command:**
```bash
     `/Users/username/.local/bin/uv --directory /path/to/mcp-server-unifi run main.py`
```
   * **Environment Variables:** Configure using `secrets.env` file as shown above

### Claude Desktop Setup

1. Open Claude and go to **Settings » Developer » Edit Config**
2. Add to your `claude_desktop_config.json`:

```json
   {
       "mcpServers": {
           "unifi": {
               "command": "/Users/username/.local/bin/uv",
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

## Current Resources

| Resource | Description |
|----------|-------------|
| `health://unifi` | Health check and controller connectivity status |
| `unifi://capabilities` | Probe available API endpoints and their status |
| `sites://{site_id}/devices` | List all network devices for a site |
| `sites://{site_id}/clients` | List all clients for a site |
| `sites://{site_id}/clients/active` | List only active/connected clients |
| `sites://{site_id}/wlans` | WLAN configurations (Integration API → Legacy fallback) |
| `sites://{site_id}/search/clients/{query}` | Search clients by hostname, MAC, IP, etc. |
| `sites://{site_id}/search/devices/{query}` | Search devices by name, model, MAC, IP |

## Available Tools

| Tool | Description |
|------|-------------|
| `unifi_health` | Check controller connectivity and status |
| `debug_registry` | List all registered resources, tools, and prompts |
| `block_client` | Block a client by MAC address |
| `unblock_client` | Unblock a previously blocked client |
| `kick_client` | Disconnect a client from the network |
| `locate_device` | Flash LEDs on a device to locate it physically |
| `wlan_set_enabled_legacy` | Enable/disable WLAN using Legacy API |

## API Authentication

The server uses a dual-authentication approach:

1. **Primary**: Integration API with `X-API-Key` header (modern, recommended)
2. **Fallback**: Legacy cookie-based session authentication (for WLAN management and older features)

The server automatically falls back to legacy authentication when the Integration API doesn't support a feature (like WLAN configuration).

## Troubleshooting

**Check connectivity:**
```bash
# Use the health check resource
curl -X POST http://localhost:5173/health://unifi

# Or check capabilities
curl -X POST http://localhost:5173/unifi://capabilities
```

**Common issues:**
- Ensure your API key has sufficient permissions
- Verify `UNIFI_GATEWAY_HOST` can reach your UniFi controller
- For WLAN management, legacy credentials (`UNIFI_USERNAME`/`UNIFI_PASSWORD`) are required
- Set `UNIFI_VERIFY_TLS=false` if using self-signed certificates

## API Coverage

| API Component | Read Support | Write Support | Notes |
|---------------|--------------|---------------|-------|
| **Network Integration** | ✅ Sites, Devices, Clients | ✅ Limited actions | No WLAN config support |
| **Legacy Network** | ✅ WLAN configurations | ✅ WLAN enable/disable | Requires username/password |

**Integration API Gaps:** WLAN/SSID configuration, network settings, firewall rules
**Solution:** Automatic fallback to Legacy API for unsupported features

## 📌 Roadmap

The UniFi MCP Server is under active development. Future phases may include:

- UniFi Access integration (doors, readers, events)
- UniFi Protect integration (cameras, events, streams)  
- Site Manager cloud API integration
- Additional network configuration tools
- Enhanced search and filtering capabilities

Check out the [roadmap.md](./roadmap.md) for the full development plan.
