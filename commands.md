📖 UniFi MCP Server – Command Reference
This document lists all available resources, tools, and prompts provided by the UniFi MCP Server.

🌐 UniFi Network (Integration + Legacy)
Type
Command
Description
Resource
sites://
List all UniFi sites
Resource
sites://{site_id}/devices
List devices in a site
Resource
sites://{site_id}/clients
List all clients in a site
Resource
sites://{site_id}/clients/active
List active clients
Resource
sites://{site_id}/wlans
List WLANs (Integration, Legacy fallback)
Resource
sites://{site_id}/search/clients/{query}
Search clients by hostname/MAC/IP/user
Resource
sites://{site_id}/search/devices/{query}
Search devices by name/model/MAC/IP
Tool
block_client(site_id, mac)
Block a client
Tool
unblock_client(site_id, mac)
Unblock a client
Tool
kick_client(site_id, mac)
Kick a client
Tool
locate_device(site_id, device_id, seconds=30)
Locate a device (flash LEDs)
Tool
wlan_set_enabled_legacy(site_id, wlan_id, enabled)
Toggle WLAN (Legacy API)
Prompt
how_to_find_device
Find a device and flash its LEDs
Prompt
how_to_block_client
Find & block a client
Prompt
how_to_toggle_wlan
Toggle a WLAN (Integration/Legacy)

🔐 UniFi Access
Type
Command
Description
Resource
access://doors
List doors
Resource
access://readers
List readers
Resource
access://users
List access users
Resource
access://events
List access events
Tool
access_unlock_door(door_id, seconds=5)
Unlock door temporarily
Prompt
how_to_manage_access
Manage doors/readers, unlock doors

📹 UniFi Protect
Type
Command
Description
Resource
protect://nvr
Get NVR bootstrap info
Resource
protect://cameras
List cameras
Resource
protect://camera/{camera_id}
Get camera details
Resource
protect://events
List events
Resource
protect://events/range/{start_ts}/{end_ts}
Events in a time range
Resource
protect://streams/{camera_id}
Camera stream info (channels, RTSP)
Tool
protect_camera_reboot(camera_id)
Reboot a camera
Tool
protect_camera_led(camera_id, enabled)
Toggle camera LED
Tool
protect_toggle_privacy(camera_id, enabled)
Toggle camera privacy mode
Prompt
how_to_find_camera
Find a camera and show streams
Prompt
how_to_review_motion
Review Protect motion/smart events
Prompt
how_to_reboot_camera
Reboot a camera

☁️ UniFi Site Manager (Cloud)
Type
Command
Description
Resource
sitemanager://hosts
List hosts
Resource
sitemanager://hosts/{host_id}
Get host by ID
Resource
sitemanager://sites
List cloud sites
Resource
sitemanager://sites/{site_id}/devices
List devices in a cloud site
Resource
sitemanager://isp/metrics
List/describe ISP metrics
Resource
sitemanager://sdwan/configs
List SD-WAN configs
Resource
sitemanager://sdwan/configs/{config_id}
Get SD-WAN config by ID
Resource
sitemanager://sdwan/configs/{config_id}/status
Get SD-WAN config status
Tool
sm_isp_metrics_query(metric, start, end, granularity="5m", filters_json="{}")
Query ISP metrics
Prompt
how_to_list_cloud_sites
List cloud sites
Prompt
how_to_list_cloud_devices
List devices in a cloud site
Prompt
how_to_query_isp_metrics
Query ISP performance metrics
Prompt
how_to_view_sdwan_status
Inspect SD-WAN configs and status

📊 Summary
	•	Resources: 25
	•	Tools: 10
	•	Prompts: 11
	•	Total MCP Commands: 46
