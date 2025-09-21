<p align="center">
  <svg width="1200" height="420" viewBox="0 0 1200 420" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="UniFi MCP Server: Intelligent Network Management Through AI">
    <defs>
      <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stop-color="#667eea"/>
        <stop offset="100%" stop-color="#764ba2"/>
      </linearGradient>
      <filter id="soft" x="-20%" y="-20%" width="140%" height="140%">
        <feGaussianBlur stdDeviation="8" />
      </filter>
    </defs>

    <!-- Background -->
    <rect width="1200" height="420" rx="28" fill="url(#bg)"/>
    
    <!-- Left: Title & subtitle -->
    <g transform="translate(60,70)">
      <text x="0" y="0" fill="#fff" font-size="56" font-weight="800">UniFi</text>
      <text x="0" y="56" fill="#fff" font-size="56" font-weight="800">MCP Server</text>
      <text x="0" y="110" fill="rgba(255,255,255,0.9)" font-size="22">Intelligent Network Management Through AI</text>

      <!-- API chips -->
      <g transform="translate(0,150)">
        <g>
          <rect width="150" height="56" rx="14" fill="rgba(255,255,255,0.18)" stroke="rgba(255,255,255,0.4)" />
          <text x="20" y="36" fill="#fff" font-size="20">🌐 Network</text>
        </g>
        <g transform="translate(170,0)">
          <rect width="150" height="56" rx="14" fill="rgba(255,255,255,0.18)" stroke="rgba(255,255,255,0.4)" />
          <text x="20" y="36" fill="#fff" font-size="20">🛡️ Protect</text>
        </g>
        <g transform="translate(340,0)">
          <rect width="150" height="56" rx="14" fill="rgba(255,255,255,0.18)" stroke="rgba(255,255,255,0.4)" />
          <text x="20" y="36" fill="#fff" font-size="20">🔑 Access</text>
        </g>
      </g>
    </g>

    <!-- Integration arrow -->
    <g transform="translate(640,210)">
      <text x="0" y="10" fill="#fff" font-size="40">→</text>
    </g>

    <!-- Right: Claude image -->
    <g transform="translate(870,110)">
      <circle cx="100" cy="100" r="100" fill="#fff" opacity="0.15" filter="url(#soft)"/>
      <circle cx="100" cy="100" r="90" fill="url(#bg)"/>
      <!-- Replace orb with image -->
      <image href="https://github.com/ry-ops/mcp-server-unifi/blob/main/claude-ai-icon-65aa.png?raw=true"
             x="35" y="35" width="130" height="130" clip-path="circle(65px at 65px 65px)" />
    </g>

    <!-- Badge -->
    <g transform="translate(980,30)">
      <rect width="180" height="36" rx="18" fill="rgba(0,0,0,0.35)" stroke="rgba(255,255,255,0.35)"/>
      <text x="90" y="24" text-anchor="middle" fill="#fff" font-size="16" font-weight="600">🚀 Open Source</text>
    </g>
  </svg>
</p>

<p align="center">
  <strong>Network</strong> &nbsp;→&nbsp; <em>Claude</em>
</p>

<p align="center">
  <a href="#-features"><img alt="Status" src="https://img.shields.io/badge/Status-Active-brightgreen"></a>
  <a href="#-setup"><img alt="uv" src="https://img.shields.io/badge/Runtime-uv-blue"></a>
  <a href="LICENSE"><img alt="License" src="https://img.shields.io/badge/License-MIT-informational"></a>
</p>


# MCP Server UniFi

A server implementation for managing and controlling UniFi network devices through MCP (Management Control Protocol). This server enables natural language interactions with your UniFi network using AI agents like Goose and Claude by wrapping the UniFi Network, Access, and Protect APIs.

## Features

- Query UniFi **sites, devices, and clients** using natural language through AI agents
- Manage UniFi **Access** (doors, readers, users, events)
- Manage UniFi **Protect** (cameras, events, streams, camera actions)
- Supports both the **Integration API** (modern, key-based) and **Legacy API** (session login)  
- Local server implementation that connects directly to your UniFi console
- Compatible with both Claude Desktop
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
```bash
     `/Users/username/.local/bin/uv --directory /path/to/mcp-server-unifi run main.py`
   * **Environment Variables:** Set `UNIFI_API_KEY` to your API key
```
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
# UniFi API Capability Matrix (at a glance)

| API                  | Read (✅) | Write (✍️) | Notes / Typical Gaps             |
| -------------------- | --------- | ---------- | -------------------------------- |
| **Network Integration** | ✅ Sites, Devices, Clients | ✍️ Limited (kick/block, locate) | No WLAN/SSID, Networks, firewall |
| **Legacy Network**   | ✅ Broad stats, inventory | ✍️ Full config (WLANs, networks) | Requires user/pass; version quirks |
| **UniFi Access**     | ✅ Doors, Readers, Users | ✍️ Unlock door (momentary) | Some model/firmware-dependent gaps |
| **UniFi Protect**    | ✅ NVR, Cameras, Events | ✍️ Camera reboot, LED, privacy | Mutations vary by firmware |
| **Site Manager (Cloud)** *(opt)* | ✅ Org-wide metadata | ✍️ Limited, role-based | Endpoints inconsistent by account |

# UniFi API (Full) Capability Matrix

| API                                   | Base Path                                             | Auth                                              | Read Coverage (✅)                                              | Write/Config (✍️)                                                                    | Typical Gaps / 404s                                           | In Your MCP (resources & tools)                                                                                                                                                                           |
| ------------------------------------- | ----------------------------------------------------- | ------------------------------------------------- | -------------------------------------------------------------- | ------------------------------------------------------------------------------------ | ------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Network Integration API**           | `https://<host>:<port>/proxy/network/integrations/v1` | `X-API-Key`                                       | Sites, Devices, Clients (incl. `/clients/active`), some Events | Limited actions (kick/block client, locate device)                                   | WLAN/SSID config, Networks/VLANs, firewall, many settings     | Resources: `sites://`, `sites://{site_id}/devices`, `.../clients`, `.../clients/active`<br>Tools: `block_client`, `unblock_client`, `kick_client`, `locate_device`                                         |
| **Legacy Network API**                | `https://<host>:<port>/proxy/network/api`             | Cookie session (`/api/auth/login` with user/pass) | Broad stats + inventory, historical data                       | **Full controller config**: WLANs (`/rest/wlanconf`), networks, port overrides, more | Requires credentials; shapes differ by version                | Used as **fallback**: `sites://{site_id}/wlans` (when Integration lacks WLANs)<br>Tool: `wlan_set_enabled_legacy`                                                                                          |
| **UniFi Access API**                  | `https://<host>:<port>/proxy/access/api/v1`           | `X-API-Key`                                       | Doors, Readers, Users, Events                                  | Momentary door unlock (where supported)                                              | Some actions model/firmware-dependent                         | Resources: `access://doors`, `.../readers`, `.../users`, `.../events`<br>Tool: `access_unlock_door`                                                                                                        |
| **UniFi Protect API**                 | `https://<host>:<port>/proxy/protect/api`             | `X-API-Key` **then** legacy cookie fallback       | NVR bootstrap, Cameras, Events, Streams info                   | Camera reboot, LED toggle, privacy mode (varies by model/fw)                         | Some mutations need exact payloads per firmware               | Resources: `protect://nvr`, `.../cameras`, `.../camera/{id}`, `.../events`, `.../events/range/{...}`, `.../streams/{id}`<br>Tools: `protect_camera_reboot`, `protect_camera_led`, `protect_toggle_privacy` |
| **Site Manager (Cloud)** *(optional)* | `https://unifi.ui.com` (or org-specific)              | `Authorization: Bearer <token>`                   | Org-wide inventory, site metadata (varies by role)             | Varies; often management & view ops                                                  | Endpoints aren’t consistently public; depends on your account | Generic bearer stubs (capability probe only in current file)                                                                                                                                              |

## Quick Reference

**Env vars:**
- Integration/Access/Protect: `UNIFI_API_KEY`, `UNIFI_GATEWAY_HOST`, `UNIFI_GATEWAY_PORT`, `UNIFI_VERIFY_TLS`
- Legacy fallback: `UNIFI_USERNAME`, `UNIFI_PASSWORD`
- Site Manager (optional): `UNIFI_SITEMGR_BASE`, `UNIFI_SITEMGR_TOKEN`

**Where you’ll see 404s:**  
- WLANs/SSIDs on **Integration** → use legacy fallback.

**Start here to verify:**  
- Call `unifi://capabilities` in MCP Inspector.




