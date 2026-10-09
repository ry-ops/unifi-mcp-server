# 📚 UniFi MCP Server: network playbook

Things to ask, and the tools the AI uses to answer. Every tool is listed in [commands.md](commands.md). `site_id` is optional everywhere; leave it out to use the default site.

## 🟢 Health and status

| Ask | Tools |
|---|---|
| "Is my UniFi setup working?" | `unifi_health` |
| "Is anything offline?" / "Any firmware updates waiting?" | `get_site_status` |
| "How's the gateway doing: CPU, memory, uptime?" | `list_adopted_devices` → `get_latest_adopted_device_statistics` |
| "What version of Network is the console running?" | `get_application_info` |
| "List every console on my account." | `cloud_list_hosts` |
| "How was my ISP's latency and packet loss today?" | `cloud_get_isp_metrics` (type `5m` or `1h`) |

## 🔎 Finding things

| Ask | Tools |
|---|---|
| "Find the device called pve01." / "Who has 10.0.0.42?" | `search_site` |
| "Which clients are wired?" | `list_connected_clients` with `filter` `type.eq('WIRED')` |
| "Which devices are U6 access points?" | `list_adopted_devices` with `filter` `name.like('U6*')` |
| "Any devices waiting to be adopted?" | `list_devices_pending_adoption` |
| "What's on VLAN 30, and what uses that network?" | `list_networks` → `get_network_references` |

List tools return 25 items by default. Ask for "all of them" and the AI passes `all_pages=true`.

## 🟡 Changing things (the AI should confirm first)

| Ask | Tools |
|---|---|
| "Restart the laundry AP." | `search_site` → `execute_adopted_device_action` `{"action": "RESTART"}` |
| "Power-cycle the camera on switch port 7." | `get_adopted_device_details` → `execute_port_action` with `port_idx` 7, `{"action": "POWER_CYCLE"}` |
| "Give the guest laptop an hour online." | `list_connected_clients` → `execute_client_action` `{"action": "AUTHORIZE_GUEST_ACCESS", "timeLimitMinutes": 60}` |
| "Make 10 one-day vouchers." | `generate_vouchers` (check the fields with `describe_operation`) |
| "Turn off the guest Wi-Fi." | `list_wifi_broadcasts` → `get_wifi_broadcast_details` → `update_wifi_broadcast` with `enabled: false` |
| "Adopt the new switch." | `list_devices_pending_adoption` → `adopt_devices` |

`update_*` tools replace the whole object (PUT), so the AI should fetch the current object, change only what you asked, and send it all back. `patch_firewall_policy` is the one partial update.

## 🔴 Firewall and policy (use the `change_firewall_safely` playbook)

1. **Read:** `list_firewall_zones`, `list_firewall_policies` (82 policies is normal; most are built-in).
2. **Schema:** `describe_operation("create_firewall_policy")`.
3. **Confirm:** the AI shows you the JSON it plans to send.
4. **Act:** `create_firewall_policy`, `update_firewall_policy` or `patch_firewall_policy`.
5. **Check:** `get_user_defined_firewall_policy_ordering` with the source and destination zone IDs; `reorder_user_defined_firewall_policies` to move it.

The same pattern works for ACL rules (`*_acl_rule*`), DNS policies (`*_dns_policy`) and traffic matching lists (`*_traffic_matching_list`), which firewall policies can reference.

## Filter cheat sheet

| Want | Filter |
|---|---|
| Exact match | `state.eq('ONLINE')` |
| Wildcard | `name.like('U7*')` |
| One of several | `model.in('U6+','U7 Pro')` |
| Combine | `and(type.eq('WIRELESS'),name.like('*iPhone*'))` |
| Either | `or(name.like('pve*'),name.like('k3s*'))` |

The fields each list tool can filter on are in its description.

## Prompt playbooks built into the server

| Playbook | What it walks the AI through |
|---|---|
| `check_unifi_health` | `unifi_health`, then `get_site_status`, then a short summary |
| `restart_device` | find, confirm, `execute_adopted_device_action` |
| `change_firewall_safely` | the five firewall steps above |
| `guest_access` | find the guest, authorize, or use vouchers for many guests |
