<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UniFi MCP Server</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap');
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
        }
        
        .container {
            width: 1200px;
            height: 600px;
            position: relative;
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            border-radius: 24px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 60px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        .left-section {
            flex: 1;
            z-index: 2;
        }
        
        .title {
            font-size: 4rem;
            font-weight: 800;
            color: white;
            margin-bottom: 20px;
            text-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            line-height: 1.1;
        }
        
        .subtitle {
            font-size: 1.4rem;
            color: rgba(255, 255, 255, 0.8);
            margin-bottom: 40px;
            font-weight: 300;
        }
        
        .apis-container {
            display: flex;
            gap: 30px;
            margin-bottom: 40px;
        }
        
        .api-item {
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 20px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            backdrop-filter: blur(10px);
            transition: all 0.3s ease;
            min-width: 120px;
        }
        
        .api-item:hover {
            transform: translateY(-5px);
            background: rgba(255, 255, 255, 0.15);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        }
        
        .api-icon {
            width: 60px;
            height: 60px;
            background: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 15px;
            font-size: 24px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        }
        
        .api-name {
            color: white;
            font-weight: 600;
            font-size: 1rem;
            text-align: center;
        }
        
        .integration-arrow {
            font-size: 3rem;
            color: white;
            margin: 0 30px;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 0.6; transform: scale(1); }
            50% { opacity: 1; transform: scale(1.1); }
        }
        
        .right-section {
            flex: 1;
            display: flex;
            justify-content: center;
            align-items: center;
            position: relative;
        }
        
        .claude-container {
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .claude-core {
            width: 200px;
            height: 200px;
            background: linear-gradient(45deg, #ff6b6b, #ffa726, #42a5f5, #ab47bc);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
            animation: rotate 20s linear infinite;
            box-shadow: 0 0 60px rgba(255, 107, 107, 0.4);
        }
        
        .claude-inner {
            width: 160px;
            height: 160px;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2.5rem;
            font-weight: 800;
            color: #333;
            box-shadow: inset 0 0 30px rgba(0, 0, 0, 0.1);
        }
        
        .claude-ray {
            position: absolute;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.6), transparent);
            border-radius: 4px;
            transform-origin: center;
        }
        
        .ray-1 { width: 120px; height: 8px; top: -4px; left: 50%; transform: translateX(-50%) rotate(0deg); animation: rayPulse 3s ease-in-out infinite; }
        .ray-2 { width: 100px; height: 6px; top: 20px; right: -10px; transform: rotate(30deg); animation: rayPulse 3s ease-in-out infinite 0.2s; }
        .ray-3 { width: 110px; height: 7px; bottom: 20px; right: -15px; transform: rotate(-30deg); animation: rayPulse 3s ease-in-out infinite 0.4s; }
        .ray-4 { width: 120px; height: 8px; bottom: -4px; left: 50%; transform: translateX(-50%) rotate(0deg); animation: rayPulse 3s ease-in-out infinite 0.6s; }
        .ray-5 { width: 100px; height: 6px; bottom: 20px; left: -10px; transform: rotate(30deg); animation: rayPulse 3s ease-in-out infinite 0.8s; }
        .ray-6 { width: 110px; height: 7px; top: 20px; left: -15px; transform: rotate(-30deg); animation: rayPulse 3s ease-in-out infinite 1s; }
        .ray-7 { width: 90px; height: 5px; top: 50%; right: -5px; transform: translateY(-50%) rotate(90deg); animation: rayPulse 3s ease-in-out infinite 1.2s; }
        .ray-8 { width: 90px; height: 5px; top: 50%; left: -5px; transform: translateY(-50%) rotate(90deg); animation: rayPulse 3s ease-in-out infinite 1.4s; }
        
        @keyframes rayPulse {
            0%, 100% { opacity: 0.3; transform: scale(1); }
            50% { opacity: 0.8; transform: scale(1.1); }
        }
        
        @keyframes rotate {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
        
        .floating-particles {
            position: absolute;
            width: 100%;
            height: 100%;
            pointer-events: none;
        }
        
        .particle {
            position: absolute;
            width: 4px;
            height: 4px;
            background: rgba(255, 255, 255, 0.6);
            border-radius: 50%;
            animation: float 6s infinite linear;
        }
        
        .particle:nth-child(1) { top: 20%; left: 10%; animation-delay: 0s; }
        .particle:nth-child(2) { top: 60%; left: 15%; animation-delay: 1s; }
        .particle:nth-child(3) { top: 80%; left: 30%; animation-delay: 2s; }
        .particle:nth-child(4) { top: 30%; left: 70%; animation-delay: 3s; }
        .particle:nth-child(5) { top: 70%; left: 80%; animation-delay: 4s; }
        .particle:nth-child(6) { top: 10%; left: 90%; animation-delay: 5s; }
        
        @keyframes float {
            0%, 100% { transform: translateY(0px) rotate(0deg); opacity: 0; }
            10% { opacity: 1; }
            90% { opacity: 1; }
            100% { transform: translateY(-20px) rotate(360deg); opacity: 0; }
        }
        
        .github-badge {
            position: absolute;
            top: 30px;
            right: 30px;
            background: rgba(0, 0, 0, 0.3);
            padding: 10px 20px;
            border-radius: 25px;
            color: white;
            font-weight: 600;
            border: 1px solid rgba(255, 255, 255, 0.2);
            backdrop-filter: blur(10px);
        }
        
        .connection-line {
            position: absolute;
            top: 50%;
            left: 50%;
            width: 200px;
            height: 2px;
            background: linear-gradient(90deg, rgba(255,255,255,0.3), rgba(255,255,255,0.8), rgba(255,255,255,0.3));
            transform: translateX(-50%) translateY(-50%);
            animation: connectionFlow 2s infinite;
        }
        
        @keyframes connectionFlow {
            0% { opacity: 0.3; transform: translateX(-50%) translateY(-50%) scaleX(0.5); }
            50% { opacity: 1; transform: translateX(-50%) translateY(-50%) scaleX(1); }
            100% { opacity: 0.3; transform: translateX(-50%) translateY(-50%) scaleX(0.5); }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="floating-particles">
            <div class="particle"></div>
            <div class="particle"></div>
            <div class="particle"></div>
            <div class="particle"></div>
            <div class="particle"></div>
            <div class="particle"></div>
        </div>
        
        <div class="github-badge">🚀 Open Source</div>
        
        <div class="left-section">
            <h1 class="title">UniFi<br>MCP Server</h1>
            <p class="subtitle">Intelligent Network Management Through AI</p>
            
            <div class="apis-container">
                <div class="api-item">
                    <div class="api-icon">🌐</div>
                    <div class="api-name">Network</div>
                </div>
                <div class="api-item">
                    <div class="api-icon">🛡️</div>
                    <div class="api-name">Protect</div>
                </div>
                <div class="api-item">
                    <div class="api-icon">🔑</div>
                    <div class="api-name">Access</div>
                </div>
            </div>
        </div>
        
        <div class="integration-arrow">→</div>
        <div class="connection-line"></div>
        
        <div class="right-section">
            <div class="claude-container">
                <div class="claude-core">
                    <div class="claude-ray ray-1"></div>
                    <div class="claude-ray ray-2"></div>
                    <div class="claude-ray ray-3"></div>
                    <div class="claude-ray ray-4"></div>
                    <div class="claude-ray ray-5"></div>
                    <div class="claude-ray ray-6"></div>
                    <div class="claude-ray ray-7"></div>
                    <div class="claude-ray ray-8"></div>
                    <div class="claude-inner">Claude</div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>

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




