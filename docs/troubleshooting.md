# 🔧 UniFi MCP Server: troubleshooting

Since version 2.0 the server is **cloud-only**: every request goes to `https://api.ui.com` with one API key, and Network API calls reach your console through UniFi's cloud connector. There's no console IP, port, TLS setting or username/password any more.

## Start here

Ask your assistant to run **`unifi_health`**. It reports:

- the consoles your key can see,
- the console and default site the server picked,
- the Network application version on the console,
- or the exact error, if any step fails.

From a terminal, the same checks with `curl`:

```bash
# 1. Does the key work, and which consoles can it see?
curl -s -H "X-API-KEY: $UNIFI_API_KEY" https://api.ui.com/v1/hosts

# 2. Can the cloud connector reach the console's Network app?
curl -s -H "X-API-KEY: $UNIFI_API_KEY" \
  "https://api.ui.com/v1/connector/consoles/$CONSOLE_ID/proxy/network/integration/v1/sites"
```

## Common problems

### 401 Unauthorized
The key is wrong, revoked, or has a stray space or quote. Create a new one at [unifi.ui.com](https://unifi.ui.com) under **Settings → API Keys** and put it in `secrets.env` as `UNIFI_API_KEY=...`.

### "No consoles on this UniFi account"
The key is valid (no 401) but `/v1/hosts` comes back empty. Usually:

1. **The key belongs to a different account or organization** than the console. Create it while signed in as the console's owner.
2. **The console isn't linked to the cloud.** In the console's settings, turn on remote management and sign in with that account.
3. **The console was just set up or re-adopted.** It can take a few minutes to appear.

### "Several consoles found" / "Several sites found"
The server only guesses when there's exactly one console, and exactly one site or a site whose internal name is `default`. Set `UNIFI_CONSOLE_ID` or `UNIFI_SITE_ID` to one of the IDs in the error, or pass `site_id` to a tool.

### 404 with `api.resource-not-found`
The endpoint exists but the ID doesn't. List the collection first (for example `list_adopted_devices`) and use an `id` from it. Network API IDs are UUIDs, not MAC addresses.

### 400 on a create or update
The body doesn't match the schema. Call **`describe_operation`** with the tool name (for example `create_firewall_policy`) to get the full schema with required fields and allowed values. Many bodies use a field such as `type`, `management` or `action` to pick a variant; the fields each variant adds are listed under `variants`.

The console also checks rules the spec doesn't spell out. These came up in live testing on Network 11.0.81:

| Error code or message | Fix |
|---|---|
| `api.network.validation.missing-zone-id` | `create_network` needs `zoneId` (for example the Internal zone's ID from `list_firewall_zones`), although the spec marks it optional. |
| "WPA security combined with standard WiFi requires fast roaming setting" | Set `securityConfiguration.fastRoamingEnabled` on a `STANDARD` Wi-Fi with WPA security. |
| "band steering setting requires broadcasting on multiple bands" | Leave out `bandSteeringEnabled`, or list more than one band in `broadcastingFrequenciesGHz`. |
| `api.wifi-broadcast.validation.too-many-wifi-broadcasts` | An access point already broadcasts as many Wi-Fi networks as it can. Use `broadcastingDeviceFilter` to put the new one on access points that have room, or remove one. |

### 400 on a list with `filter`
Check the syntax: `name.like('U*')`, `state.eq('ONLINE')`, `and(type.eq('WIRED'),name.like('pve*'))`. Each list tool's description lists the fields it can filter on and the functions each field allows.

### Timeouts
The cloud connector adds a round trip. Raise `UNIFI_TIMEOUT_S` (default 30).

## MCP client problems

### "Server disconnected" right after start
Run the server by hand and read stderr:

```bash
uv run --directory /path/to/unifi-mcp-server python main.py
```

The server writes its logs to **stderr** and nothing to stdout, because stdout carries the MCP protocol. Before 2.0, startup messages with emoji went to stdout; that broke the protocol and crashed on Windows consoles using code page cp1252 ([#39](https://github.com/ry-ops/unifi-mcp-server/issues/39)).

### The server can't find `secrets.env`
It reads `secrets.env` from the folder `main.py` is in, wherever the client starts it. Environment variables set by the client win over the file.

### A tool you expected is missing
- `UNIFI_READ_ONLY=true` hides the 32 tools that can change things.
- Tools from before 2.0 (`block_client`, `kick_client`, `locate_device`, `list_hosts`, `wlan_set_enabled_legacy`, Protect and Access tools) were removed. They called the local console or endpoints that aren't in the Network API. See the table below for replacements.

| Old tool | Use instead |
|---|---|
| `get_system_status`, `get_quick_status`, `get_device_health`, `get_client_activity` | `get_site_status` |
| `list_hosts`, `list_active_clients` | `list_connected_clients`, `list_adopted_devices` |
| `find_device_by_mac`, `find_host_everywhere` | `search_site` |
| `list_hosts_cloud`, `discover_sites` | `cloud_list_hosts`, `list_local_sites` |
| `wlan_set_enabled_legacy` | `get_wifi_broadcast_details` then `update_wifi_broadcast` with `enabled` changed |
| `locate_device` | not in the Network API; `execute_adopted_device_action` supports `RESTART` |
| `block_client`, `kick_client` | not in the Network API; use firewall or ACL rules, or `UNAUTHORIZE_GUEST_ACCESS` for guests |
| `debug_api_connectivity`, `debug_registry` | `unifi_health`, `list_operations` |

## Still stuck?
Open an [issue](https://github.com/ry-ops/unifi-mcp-server/issues) with the `unifi_health` output, with your key and console ID removed.
