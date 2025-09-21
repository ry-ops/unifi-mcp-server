<img src="https://github.com/ry-ops/mcp-server-unifi/blob/main/unifi-mcp-server.png" width="800">


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
- Compatible with Claude Desktop
- Secure API key-based authentication with optional legacy fallback

## Prerequisites

- Python 3.8 or higher
- Install <a href="https://docs.astral.sh/uv/getting-started/" rel>`uv`</a> which we’ll use for managing the Python project.
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

---

## 📌 Roadmap

The UniFi MCP Server is under active development, with new features and API integrations planned.  

Check out the [ROADMAP.md](./ROADMAP.md) for the full list of planned resources, tools, and prompts, organized by phase.  


