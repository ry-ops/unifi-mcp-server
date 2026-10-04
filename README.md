<p align="center">
  <img src="docs/hero.svg" width="100%" alt="You ask who's hogging the bandwidth; the UniFi MCP server queries the local Integration API, the legacy controller API and the cloud Site Manager, the network map lights up, and the answer flags the living-room TV.">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/tools-26-1f7cff" alt="26 tools">
  <img src="https://img.shields.io/badge/resources-13-3ec7ff" alt="13 resources">
  <img src="https://img.shields.io/badge/playbooks-9-b58cff" alt="9 prompt playbooks">
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.12+-3ddc84" alt="Python 3.12+"></a>
  <a href="https://modelcontextprotocol.io/"><img src="https://img.shields.io/badge/MCP-FastMCP-ff8a5c" alt="MCP"></a>
  <a href="https://github.com/ry-ops/unifi-mcp-server/pkgs/container/unifi-mcp-server"><img src="https://img.shields.io/badge/docker-ghcr.io-ffb02e" alt="Docker image on ghcr.io"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-8b96ad" alt="MIT"></a>
</p>

<p align="center"><b>Ask your UniFi network anything.</b> An MCP server that lets Claude, or any MCP client, monitor and manage UniFi Network, Protect and Access, on your local console and through UniFi's cloud Site Manager, in plain English.</p>

<p align="center">
  <a href="#what">What it does</a> ·
  <a href="#toolbox">Toolbox</a> ·
  <a href="#setup">Setup</a> ·
  <a href="#safety">Safety</a> ·
  <a href="#a2a">A2A</a> ·
  <a href="#troubleshooting">Troubleshooting</a>
</p>

---

<a id="what"></a>

## ✨ What it does

- 📡 **Watches your network.** System health, device uptime, client activity and bandwidth, and a quick one-line status. Status reports are cached for 5 minutes, so repeat questions are fast.
- 🔎 **Finds anything.** Hosts on your local console and across every console in your UniFi account, devices by MAC, and site discovery when you don't know the site ID.
- 🛠️ **Acts when you ask.** Block, unblock or kick a client; flash a device's LED to find it; turn a WLAN on or off; unlock a door; reboot a Protect camera, toggle its LED or privacy mode.
- 🌐 **Talks to five UniFi APIs:** the Network Integration API (v1) and classic API on your console, the Protect and Access APIs, and the cloud **Site Manager** at `api.ui.com`.
- 📚 **Comes with playbooks.** 9 MCP prompts walk an AI through common jobs (search, confirm, act), plus an A2A agent card for agent-to-agent discovery.

**Ask things like:**

> *"How's my UniFi network doing?"*
> *"Who's using the most bandwidth right now?"*
> *"Find the device with MAC aa:bb:cc:dd:ee:ff and flash its LED."*
> *"Block the kids' tablet until I say otherwise."*
> *"Turn off the guest Wi-Fi."*
> *"List every UniFi console on my account."*

<a id="toolbox"></a>

## 🧰 The toolbox

<p align="center">
  <img src="docs/toolbox.svg" width="100%" alt="26 tools in four groups (monitor 6, find and discover 9, act 9, debug 2), 13 read-only resources, the five UniFi APIs, and the block-a-client playbook stepping through read, match, confirm, act, offer an undo.">
</p>

| Group | Tools |
|---|---|
| **Monitor** (6) | `unifi_health`, `get_system_status`, `get_device_health`, `get_client_activity`, `get_quick_status`, `list_active_clients` |
| **Find & discover** (9) | `discover_sites`, `list_hosts`, `list_hosts_cloud`, `list_all_hosts`, `find_host_everywhere`, `find_device_by_mac`, `list_hosts_api_format`, `list_hosts_fixed`, `working_list_hosts_example` |
| **Act** (9) | `block_client`, `unblock_client`, `kick_client`, `locate_device`, `wlan_set_enabled_legacy`, `access_unlock_door`, `protect_camera_reboot`, `protect_camera_led`, `protect_toggle_privacy` |
| **Debug** (2) | `debug_api_connectivity`, `debug_registry` |

**Resources** (read-only, by URI):
- **Health and status:** `unifi://health` (plus its `health://unifi` and `status://unifi` aliases), `unifi://capabilities`, and `status://system`, `status://devices`, `status://clients`.
- **Per site:** `sites://{site_id}/devices`, `/clients`, `/clients/active` and `/wlans`.
- **Search:** `sites://{site_id}/search/clients/{query}` and `/search/devices/{query}`.

**Prompt playbooks:**
- **Health and status:** `how_to_check_unifi_health`, `how_to_check_system_status`, `how_to_monitor_devices`, `how_to_check_network_activity`.
- **Finding things:** `how_to_find_device`, `how_to_list_hosts`.
- **Changing things:** `how_to_block_client`, `how_to_toggle_wlan`.
- **Debugging:** `how_to_debug_api_issues`.

<a id="setup"></a>

## 🚀 Setup

You need **Python 3.12+** with [`uv`](https://github.com/astral-sh/uv), a UniFi OS console running the Network application, and optionally a Site Manager API key for the cloud tools.

**1. Get your keys**
- **Local console:** in UniFi Network, go to **Settings → Control Plane → Integrations** and create an API key.
- **Cloud (optional):** at [unifi.ui.com](https://unifi.ui.com), go to **Settings → API** and create a Site Manager API key.

**2. Install**

```bash
git clone https://github.com/ry-ops/unifi-mcp-server && cd unifi-mcp-server
uv sync
```

**3. Configure.** The server reads `secrets.env` from the project directory. Environment variables work too.

```bash
# Local console
UNIFI_API_KEY=your_local_api_key
UNIFI_GATEWAY_HOST=192.168.1.1
UNIFI_GATEWAY_PORT=443
UNIFI_VERIFY_TLS=false

# Classic API, for WLAN toggling and advanced config (optional)
UNIFI_USERNAME=your_unifi_username
UNIFI_PASSWORD=your_unifi_password

# Cloud Site Manager (optional)
UNIFI_SITEMGR_BASE=https://api.ui.com
UNIFI_SITEMGR_TOKEN=your_site_manager_api_key

# Optional
UNIFI_TIMEOUT_S=15
```

> [!WARNING]
> `secrets.env` is tracked in this repository as a template of placeholders. Before you put real keys in it, run `git update-index --skip-worktree secrets.env`, or use environment variables instead, so your credentials can never be committed.

**4. Run it**

```bash
uv run mcp dev main.py   # MCP Inspector, to try the tools
uv run main.py           # stdio server
```

**5. Connect Claude Desktop.** Add this to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "unifi": {
      "command": "uv",
      "args": ["--directory", "/absolute/path/to/unifi-mcp-server", "run", "main.py"],
      "env": {
        "UNIFI_API_KEY": "your_local_api_key",
        "UNIFI_GATEWAY_HOST": "192.168.1.1",
        "UNIFI_SITEMGR_TOKEN": "your_site_manager_api_key"
      }
    }
  }
}
```

<details>
<summary><b>Docker</b></summary>

An image is built from `main` and published to GitHub Container Registry. MCP talks over stdio, so run it interactively:

```bash
docker run -i --rm --env-file secrets.env ghcr.io/ry-ops/unifi-mcp-server:latest
```
</details>

<a id="safety"></a>

## 🔒 Safety

- **Nine tools change things:** blocking and kicking clients, toggling WLANs, unlocking doors, and rebooting cameras or changing their LED and privacy mode. The **playbooks** tell the AI to search, confirm with you, and then act. The **tools themselves don't enforce confirmation**, so your MCP client's tool-approval setting is the real gate. Keep it on.
- **Give it the least access that works.** A local API key covers the Integration API. Only add the classic username and password, or the cloud token, if you need those features.
- **`UNIFI_VERIFY_TLS=false`** is the default because consoles ship self-signed certificates. Turn it on if your console has a valid one.
- **Never commit real credentials.** See the warning in [Setup](#setup).

<a id="a2a"></a>

## 🤝 Agent-to-agent (A2A)

[`agent-card.json`](agent-card.json) describes this server to other agents. It lists its skills (system health, device management, client monitoring, client blocking, WLAN management, Protect, Access, multi-site host discovery and API troubleshooting), how they map to the tools, resources and playbooks above, and its authentication and safety requirements.

<a id="troubleshooting"></a>

## 🩺 Troubleshooting

<details>
<summary><b>Start with the built-in diagnostics</b></summary>

Ask your assistant to run **`debug_api_connectivity`**. It tests every API endpoint and suggests fixes. `discover_sites` finds the right site ID, and `debug_registry` shows what the server has loaded.
</details>

<details>
<summary><b>401 or 403 from the console</b></summary>

- Check `UNIFI_API_KEY` and that it was created on this console.
- Classic API features (like WLAN toggling) also need `UNIFI_USERNAME` and `UNIFI_PASSWORD`.
</details>

<details>
<summary><b>Can't connect</b></summary>

- `UNIFI_GATEWAY_HOST` is the console's IP or hostname, with no scheme.
- Self-signed certificate? Keep `UNIFI_VERIFY_TLS=false`.
- Raise `UNIFI_TIMEOUT_S` on slow links.
</details>

<details>
<summary><b>Cloud tools return nothing</b></summary>

Set `UNIFI_SITEMGR_TOKEN` to a Site Manager key from unifi.ui.com. The local key doesn't work for the cloud.
</details>

There's more in [TROUBLESHOOTING.md](TROUBLESHOOTING.md), [NETWORK_PLAYBOOK.md](NETWORK_PLAYBOOK.md) and [commands.md](commands.md).

## 🗺️ Roadmap

What's done and what's next is in [roadmap.md](roadmap.md).

## 🙏 Credits

This project started as a fork of [**zcking/mcp-server-unifi**](https://github.com/zcking/mcp-server-unifi) by Zachary King, and has since grown Protect, Access, Site Manager, status monitoring, playbooks and A2A support. MIT licensed. See [LICENSE](LICENSE).

<!-- org-footer -->
---

<p align="center"><sub>Part of <a href="https://github.com/ry-ops">ry-ops</a> · building the pipes between infrastructure, automation, and observability · built by <a href="https://github.com/ry-ops">ry-ops</a></sub></p>
