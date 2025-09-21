# MCP Server UniFi

A server implementation for managing and controlling UniFi network devices through MCP (Management Control Protocol). This server enables natural language interactions with your UniFi network using AI agents like Goose and Claude by wrapping the UniFi Network, Access, and Protect APIs.

## Features

- Query UniFi **sites, devices, and clients** using natural language through AI agents
- Manage UniFi **Access** (doors, readers, users, events)
- Manage UniFi **Protect** (cameras, events, streams, camera actions)
- Supports both the **Integration API** (modern, key-based) and **Legacy API** (session login)  
- Local server implementation that connects directly to your UniFi console
- Compatible with both Goose AI and Claude Desktop
- Secure API key-based authentication with optional legacy fallback

## Prerequisites

- Python 3.8 or higher
- `uv` package manager
- UniFi Network application (running locally or on UniFi OS)
- UniFi API key (obtained from UniFi console)

## Setup

1. **Create an API key:**
   - Go to your UniFi console at https://unifi.ui.com
   - Navigate to **Settings » Control Plane » Integrations**
   - Click **Create API Key**

2. **Clone and set up the repository:**
   ```bash
   git clone https://github.com/yourusername/mcp-server-unifi
   cd mcp-server-unifi
   uv venv
   source .venv/bin/activate  # On Unix/macOS
   # or
   .venv\Scripts\activate  # On Windows
````

3. **Install dependencies:**

   ```bash
   uv sync
   ```

4. **Configure environment variables:**

   ```bash
   export UNIFI_API_KEY="your_api_key_here"
   export UNIFI_GATEWAY_HOST="192.168.1.1"
   export UNIFI_GATEWAY_PORT="443"
   export UNIFI_VERIFY_TLS=false   # set to true if you use a valid TLS cert
   ```

   *(Optional)* If you want to enable legacy features (WLAN config, Protect fallback):

   ```bash
   export UNIFI_USERNAME="admin"
   export UNIFI_PASSWORD="your_password"
   ```

   *(Optional)* For Site Manager (cloud API):

   ```bash
   export UNIFI_SITEMGR_BASE="https://unifi.ui.com"
   export UNIFI_SITEMGR_TOKEN="Bearer <your_token>"
   ```

## Running the Server

Start the MCP development server:

```bash
uv run mcp dev main.py
```

The MCP Inspector will be available at [http://localhost:5173](http://localhost:5173) for testing and debugging.

## AI Agent Integration

### Goose AI Setup

1. Open Goose and go to **Settings » Extensions » Add custom extension**
2. Configure the extension:

   * **ID:** unifi
   * **Name:** unifi
   * **Description:** Get information about your UniFi network
   * **Command:**
     `/Users/username/.local/bin/uv --directory /path/to/mcp-server-unifi run main.py`
   * **Environment Variables:** Set `UNIFI_API_KEY` to your API key

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

---

## UniFi API Capability Matrix

| API                                   | Base Path                                             | Auth                                           | Read Coverage (✅)                                              | Write/Config (✍️)                                                       | Typical Gaps / 404s                                       | In This MCP                                                                                                                                             |
| ------------------------------------- | ----------------------------------------------------- | ---------------------------------------------- | -------------------------------------------------------------- | ----------------------------------------------------------------------- | --------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Network Integration API**           | `https://<host>:<port>/proxy/network/integrations/v1` | `X-API-Key`                                    | Sites, Devices, Clients (incl. `/clients/active`), some Events | Limited actions (kick/block client, locate device)                      | WLAN/SSID config, Networks/VLANs, firewall, many settings | Resources: `sites://`, `.../devices`, `.../clients` • Tools: `block_client`, `unblock_client`, `kick_client`, `locate_device`                           |
| **Legacy Network API**                | `https://<host>:<port>/proxy/network/api`             | Cookie session (`/api/auth/login`)             | Broad stats + inventory, historical data                       | Full controller config: WLANs, networks, port overrides, firewall, etc. | Requires credentials; shapes differ by version            | Fallback for `sites://{site_id}/wlans` • Tool: `wlan_set_enabled_legacy`                                                                                |
| **UniFi Access API**                  | `https://<host>:<port>/proxy/access/api/v1`           | `X-API-Key`                                    | Doors, Readers, Users, Events                                  | Door unlock (if supported)                                              | Actions depend on controller build                        | Resources: `access://doors`, `.../readers`, `.../users`, `.../events` • Tool: `access_unlock_door`                                                      |
| **UniFi Protect API**                 | `https://<host>:<port>/proxy/protect/api`             | API Key first, fallback to cookie              | NVR bootstrap, Cameras, Events, Streams                        | Camera reboot, LED toggle, privacy mode                                 | Some mutations require exact payloads per firmware/model  | Resources: `protect://nvr`, `.../cameras`, `.../events`, `.../streams` • Tools: `protect_camera_reboot`, `protect_camera_led`, `protect_toggle_privacy` |
| **Site Manager (Cloud)** *(optional)* | `https://unifi.ui.com`                                | Bearer token (`Authorization: Bearer <token>`) | Org-wide inventory, site metadata                              | Varies by account/role                                                  | Endpoints not consistently documented                     | Capability probe included                                                                                                                               |

---

## License

MIT

```

---

Do you want me to also generate a **`docs/` folder** with a more detailed breakdown per API (with example request/response payloads), or just keep this README as the primary documentation?
```
