# 🗺️ UniFi MCP Server Roadmap

This document outlines planned enhancements for the UniFi MCP Server.
The roadmap is divided into phases for incremental implementation and safe rollout.

**Last Updated**: October 28, 2025

---

## ✅ Phase 1: Core Health & Monitoring (COMPLETED)
- [x] `unifi://health` resource
- [x] `health://unifi` and `status://unifi` aliases
- [x] `unifi_health` tool (fallback)
- [x] `status://system` resource (comprehensive system health)
- [x] `status://devices` resource (device health monitoring)
- [x] `status://clients` resource (client activity tracking)
- [x] `get_system_status()` tool (complete health overview)
- [x] `get_device_health()` tool (device uptime and status)
- [x] `get_client_activity()` tool (bandwidth and connection stats)
- [x] `get_quick_status()` tool (fast health check)
- [x] `unifi://capabilities` resource (system capabilities)
- [ ] `unifi://alerts` resource (controller alerts/warnings)
- [ ] `ping_device(site_id, device_id)` tool  

---

## ✅ Phase 2: Client & Device Management (COMPLETED)
- [x] `sites://{site_id}/devices` resource (all network devices)
- [x] `sites://{site_id}/clients` resource (all network clients)
- [x] `sites://{site_id}/clients/active` resource (connected clients)
- [x] `sites://{site_id}/search/clients/{query}` resource (client search)
- [x] `sites://{site_id}/search/devices/{query}` resource (device search)
- [x] `block_client(site_id, mac)` tool (block network access)
- [x] `unblock_client(site_id, mac)` tool (restore network access)
- [x] `kick_client(site_id, mac)` tool (disconnect client)
- [x] `locate_device(site_id, device_id)` tool (flash LED)
- [x] `find_device_by_mac(mac)` tool (find device by MAC)
- [x] `find_host_everywhere(identifier)` tool (search all sources)
- [x] `list_hosts()` tool (list all network hosts)
- [x] `list_active_clients()` tool (connected clients only)

---

## ✅ Phase 3: WLAN Management (COMPLETED)
- [x] `sites://{site_id}/wlans` resource (list wireless networks)
- [x] `wlan_set_enabled_legacy(site_id, wlan_id, enabled)` tool (toggle WLAN)
- [x] Integration + Legacy API fallback for WLAN operations
- [ ] `sites://{site_id}/wlan-stats` resource
- [ ] `set_wlan_password(site_id, wlan_id, password)` tool

---

## ✅ Phase 4: UniFi Protect Integration (COMPLETED)
- [x] `protect_camera_reboot(camera_id)` tool (reboot camera)
- [x] `protect_camera_led(camera_id, enabled)` tool (control LED)
- [x] `protect_toggle_privacy(camera_id, enabled)` tool (privacy mode)
- [ ] `protect://events/live` resource (motion/person/car events)
- [ ] `protect_snapshot(camera_id)` tool
- [ ] `protect_download_clip(camera_id, start, end)` tool

---

## ✅ Phase 5: UniFi Access Integration (COMPLETED)
- [x] `access_unlock_door(door_id, seconds)` tool (unlock door)
- [ ] `access://users/active` resource
- [ ] `access_grant_temp(user_id, door_id, duration)` tool
- [ ] `access_revoke(user_id)` tool

---

## ✅ Phase 6: Multi-API & Cloud Support (COMPLETED)
- [x] Dual API support (Integration + Legacy)
- [x] Cloud Site Manager API integration
- [x] Smart fallback logic (cloud → local)
- [x] Auto site ID discovery
- [x] `list_hosts_api_format()` tool (cloud API format)
- [x] `list_hosts_fixed()` tool (auto site discovery)
- [x] `list_hosts_cloud()` tool (cloud-only listing)
- [x] `list_all_hosts()` tool (comprehensive local + cloud)
- [x] `working_list_hosts_example()` tool (best practice example)
- [ ] `sitemanager://sites` resource (list cloud sites)
- [ ] `sitemanager://sites/{site_id}/status` resource
- [ ] `sitemanager_switch_site(site_id)` tool

---

## ✅ Phase 7: A2A Protocol & Automation (COMPLETED)
- [x] A2A (Agent-to-Agent) protocol implementation
- [x] `how_to_check_unifi_health` prompt playbook
- [x] `how_to_check_system_status` prompt playbook
- [x] `how_to_monitor_devices` prompt playbook
- [x] `how_to_check_network_activity` prompt playbook
- [x] `how_to_find_device` prompt playbook
- [x] `how_to_block_client` prompt playbook (with safety checks)
- [x] `how_to_toggle_wlan` prompt playbook
- [x] `how_to_list_hosts` prompt playbook
- [x] `how_to_debug_api_issues` prompt playbook
- [ ] `auto_block_suspicious_clients(site_id)` tool
- [ ] `rotate_guest_wlan_password(site_id, schedule)` tool

---

## ✅ Phase 8: Debugging & Diagnostics (COMPLETED)
- [x] `debug_api_connectivity()` tool (comprehensive API testing)
- [x] `discover_sites()` tool (find valid site IDs)
- [x] `debug_registry()` tool (show all resources/tools)
- [x] SSRF protection with URL validation
- [x] Comprehensive error handling
- [x] Detailed troubleshooting recommendations

---

## ✅ Phase 9: Documentation & Integration (COMPLETED - Oct 2025)
- [x] Comprehensive README with A2A documentation
- [x] Network Playbook (NETWORK_PLAYBOOK.md)
- [x] GitHub Actions workflow (Claude Code integration)
- [x] A2A badge and feature highlighting
- [x] Example usage and troubleshooting guides
- [x] Security best practices documentation
- [x] Commands reference (commands.md)

---

## 🔄 Phase 10: Network Deep-Dive (IN PROGRESS)
- [ ] `sites://{site_id}/vlans` resource (with legacy fallback)
- [ ] `sites://{site_id}/firewall-rules` resource
- [ ] `toggle_port_poe(site_id, port_id, enabled)` tool
- [ ] `restart_device(site_id, device_id)` tool
- [ ] Port statistics and monitoring  

---

## 🌟 Future Enhancements (Stretch Goals)

### Advanced Protect Features
- [ ] `protect://events/live` resource (real-time motion/person/car events)
- [ ] `protect_snapshot(camera_id)` tool (capture camera snapshot)
- [ ] `protect_download_clip(camera_id, start, end)` tool (download video clips)
- [ ] Prompt: "How to review last night's motion events"

### Advanced Access Features
- [ ] `access://users/active` resource (active users list)
- [ ] `access_grant_temp(user_id, door_id, duration)` tool (temporary access)
- [ ] `access_revoke(user_id)` tool (revoke access)

### Enhanced WLAN Capabilities
- [ ] `sites://{site_id}/wlan-stats` resource (WLAN statistics)
- [ ] `set_wlan_password(site_id, wlan_id, password)` tool (password rotation)
- [ ] Prompt: "How to rotate guest Wi-Fi password"

### Advanced Network Operations
- [ ] `sites://{site_id}/vlans` resource (VLAN management)
- [ ] `sites://{site_id}/firewall-rules` resource (firewall rules)
- [ ] `toggle_port_poe(site_id, port_id, enabled)` tool (PoE control)
- [ ] `restart_device(site_id, device_id)` tool (device restart)
- [ ] Port statistics and monitoring

### Intelligent Automation
- [ ] `auto_block_suspicious_clients(site_id)` tool (anomaly detection + blocking)
- [ ] `rotate_guest_wlan_password(site_id, schedule)` tool (scheduled rotation)
- [ ] Prompt: "How to prepare a daily UniFi report"
- [ ] AI-assisted decision-making with safety guardrails
- [ ] Event forwarding to AI agents (real-time context)

### Multi-Controller & Enterprise
- [ ] Multi-controller support (manage multiple sites)
- [ ] `sitemanager://sites` resource (list all cloud sites)
- [ ] `sitemanager://sites/{site_id}/status` resource (site uptime/alerts)
- [ ] `sitemanager_switch_site(site_id)` tool (switch between controllers)
- [ ] Centralized dashboard across multiple controllers

### Performance & Scalability
- [ ] WebSocket support for real-time updates
- [ ] Enhanced caching strategies
- [ ] Batch operations for large-scale changes
- [ ] Performance analytics and optimization suggestions  

---

## Summary Statistics

**Phases Completed**: 9 of 10 (90%)
**Total Features Implemented**: 70+
**A2A Prompts**: 9 playbooks
**Resources**: 13 URIs
**Tools**: 26 functions

### Progress by Category
- ✅ **Core Infrastructure**: 100% complete
- ✅ **Health & Monitoring**: 100% complete
- ✅ **Client Management**: 100% complete
- ✅ **Device Management**: 100% complete
- ✅ **Multi-API Support**: 100% complete
- ✅ **A2A Protocol**: 100% complete
- ✅ **Documentation**: 100% complete
- 🔄 **Advanced Features**: 40% complete
- 🌟 **Future Enhancements**: 0% (planned)

---

## Legend
- ✅ Completed
- 🔄 In progress / planned
- 🌟 Future / stretch goal

---

## Recent Achievements (October 2025)
- 🎉 Fixed client tracking API issue (removed invalid /clients/active endpoint)
- 🎉 Added comprehensive A2A protocol documentation
- 🎉 Created Network Playbook with 40+ commands
- 🎉 Implemented GitHub Actions workflow for Claude Code integration
- 🎉 Enhanced README with A2A capabilities highlighting
- 🎉 Added SSRF protection and security improvements
- 🎉 Comprehensive multi-API fallback logic
