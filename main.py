# main.py
# UniFi MCP Server – Integration + Legacy + Access + Protect (+ Site Manager stubs)
# - Rich resources for reads, curated tools for safe actions, prompt playbooks
# - Dual-mode auth (API key first; fall back to legacy cookie where needed)
# - Includes health alias (health://unifi) and debug_registry tool
# - Safer URL building to avoid line-wrap identifier breaks

from typing import Any, Dict, List, Optional
import os, json, requests, urllib3
from pathlib import Path
from mcp.server.fastmcp import FastMCP

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ========= Load Environment Variables from secrets.env =========
def load_env_file(env_file: str = "secrets.env"):
    """Load environment variables from a .env file"""
    env_path = Path(env_file)
    if env_path.exists():
        print(f"📁 Loading environment from: {env_path.absolute()}")
        with open(env_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Parse KEY=VALUE format
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Remove quotes if present
                    if (value.startswith('"') and value.endswith('"')) or \
                       (value.startswith("'") and value.endswith("'")):
                        value = value[1:-1]
                    
                    # Set environment variable if not already set
                    if key not in os.environ:
                        os.environ[key] = value
                        print(f"  ✓ Loaded: {key}")
                    else:
                        print(f"  ⚠️  Skipped {key} (already set in environment)")
                else:
                    print(f"  ⚠️  Invalid format on line {line_num}: {line}")
    else:
        print(f"⚠️  Environment file not found: {env_path.absolute()}")
        print("   Create secrets.env with your UniFi credentials")

# Load environment variables first
load_env_file()

# ========= Configuration =========
UNIFI_API_KEY   = os.getenv("UNIFI_API_KEY", "API")
UNIFI_HOST      = os.getenv("UNIFI_GATEWAY_HOST", "HOST")
UNIFI_PORT      = os.getenv("UNIFI_GATEWAY_PORT", "443")
VERIFY_TLS      = os.getenv("UNIFI_VERIFY_TLS", "false").lower() in ("1", "true", "yes")

# Legacy credentials (optional; enable for config endpoints not in Integration API)
LEGACY_USER     = os.getenv("UNIFI_USERNAME", "USERNAME")
LEGACY_PASS     = os.getenv("UNIFI_PASSWORD", "PASSWORD")

# Site Manager (cloud) – generic bearer pass-through (optional)
SM_BASE         = os.getenv("UNIFI_SITEMGR_BASE", "").rstrip("/")
SM_TOKEN        = os.getenv("UNIFI_SITEMGR_TOKEN", "")

# Base URLs
NET_INTEGRATION_BASE = f"https://{UNIFI_HOST}:{UNIFI_PORT}/proxy/network/integrations/v1"
LEGACY_BASE          = f"https://{UNIFI_HOST}:{UNIFI_PORT}/proxy/network/api"
ACCESS_BASE          = f"https://{UNIFI_HOST}:{UNIFI_PORT}/proxy/access/api/v1"
PROTECT_BASE         = f"https://{UNIFI_HOST}:{UNIFI_PORT}/proxy/protect/api"

REQUEST_TIMEOUT_S    = int(os.getenv("UNIFI_TIMEOUT_S", "15"))

mcp = FastMCP("unifi")

# ========= HTTP helpers =========
class UniFiHTTPError(RuntimeError):
    pass

def _raise_for(r: requests.Response) -> Dict[str, Any]:
    try:
        r.raise_for_status()
        return r.json() if r.text.strip() else {}
    except requests.exceptions.HTTPError as e:
        body = (r.text or "")[:800]
        raise UniFiHTTPError(f"{r.request.method} {r.url} -> {r.status_code} {r.reason}; body: {body}") from e

def _h_key() -> Dict[str, str]:
    return {"X-API-Key": UNIFI_API_KEY, "Content-Type": "application/json"}

def _get(url: str, headers: Dict[str, str], params=None, timeout=REQUEST_TIMEOUT_S) -> Dict[str, Any]:
    return _raise_for(requests.get(url, headers=headers, params=params, verify=VERIFY_TLS, timeout=timeout))

def _post(url: str, headers: Dict[str, str], body=None, timeout=REQUEST_TIMEOUT_S) -> Dict[str, Any]:
    return _raise_for(requests.post(url, headers=headers, json=body, verify=VERIFY_TLS, timeout=timeout))

# Legacy session (cookie auth)
LEGACY = requests.Session()

def legacy_login():
    if not (LEGACY_USER and LEGACY_PASS):
        raise UniFiHTTPError("Legacy login requires UNIFI_USERNAME and UNIFI_PASSWORD.")
    r = LEGACY.post(
        f"https://{UNIFI_HOST}:{UNIFI_PORT}/api/auth/login",
        json={"username": LEGACY_USER, "password": LEGACY_PASS},
        verify=VERIFY_TLS,
        timeout=REQUEST_TIMEOUT_S,
    )
    _raise_for(r)

def legacy_get(path: str, params=None) -> Dict[str, Any]:
    if not LEGACY.cookies:
        legacy_login()
    r = LEGACY.get(f"{LEGACY_BASE}{path}", params=params, verify=VERIFY_TLS, timeout=REQUEST_TIMEOUT_S)
    return _raise_for(r)

def legacy_post(path: str, body=None) -> Dict[str, Any]:
    if not LEGACY.cookies:
        legacy_login()
    r = LEGACY.post(f"{LEGACY_BASE}{path}", json=body, verify=VERIFY_TLS, timeout=REQUEST_TIMEOUT_S)
    return _raise_for(r)

# ========= UniFi Protect helpers =========
def protect_get(path: str, params=None) -> Dict[str, Any]:
    """
    Try API key first; if unauthorized, fall back to legacy cookie session.
    """
    try:
        r = requests.get(f"{PROTECT_BASE}{path}", headers=_h_key(), params=params, verify=VERIFY_TLS, timeout=REQUEST_TIMEOUT_S)
        if r.status_code == 200:
            return _raise_for(r)
        if r.status_code not in (401, 403):
            return _raise_for(r)
    except Exception:
        pass  # fall back
    if not LEGACY.cookies:
        legacy_login()
    r = LEGACY.get(f"{PROTECT_BASE}{path}", params=params, verify=VERIFY_TLS, timeout=REQUEST_TIMEOUT_S)
    return _raise_for(r)

def protect_post(path: str, body=None) -> Dict[str, Any]:
    try:
        r = requests.post(f"{PROTECT_BASE}{path}", headers=_h_key(), json=body, verify=VERIFY_TLS, timeout=REQUEST_TIMEOUT_S)
        if r.status_code in (200, 204):
            return _raise_for(r)
        if r.status_code not in (401, 403):
            return _raise_for(r)
    except Exception:
        pass
    if not LEGACY.cookies:
        legacy_login()
    r = LEGACY.post(f"{PROTECT_BASE}{path}", json=body, verify=VERIFY_TLS, timeout=REQUEST_TIMEOUT_S)
    return _raise_for(r)

# ========= UniFi Health (triple-registered) =========

def _health_check() -> Dict[str, Any]:
    """
    Minimal controller sanity check against Integration API.
    Returns ok: True with sites count, or ok: False with error.
    """
    try:
        resp = _get("/".join([NET_INTEGRATION_BASE, "sites"]), _h_key())
        return {
            "ok": True,
            "integration_sites_count": resp.get("count"),
            "base": NET_INTEGRATION_BASE,
            "verify_tls": VERIFY_TLS,
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "base": NET_INTEGRATION_BASE, "verify_tls": VERIFY_TLS}

# 1) Original scheme you tried
@mcp.resource("unifi://health")
async def unifi_health_resource() -> Dict[str, Any]:
    return _health_check()

# 2) Alternate scheme many inspectors display reliably
@mcp.resource("health://unifi")
async def health_alias_resource() -> Dict[str, Any]:
    return _health_check()

# 3) Extra alias (belt & suspenders)
@mcp.resource("status://unifi")
async def status_alias_resource() -> Dict[str, Any]:
    return _health_check()

# Tool fallback (always visible in Tools tab)
@mcp.tool()
def unifi_health() -> Dict[str, Any]:
    """Ping the UniFi Integration API and report basic health."""
    return _health_check()

# Prompt so agents know how to call it
@mcp.prompt("how_to_check_unifi_health")
def how_to_check_unifi_health():
    return {
        "description": "Check UniFi controller health via Integration API.",
        "messages": [{
            "role": "system",
            "content": (
                "To check UniFi health, call 'health://unifi' (or 'unifi://health' / 'status://unifi'). "
                "If resources are unavailable, call the 'unifi_health' tool instead."
            )
        }]
    }

# ========= Utilities =========
def paginate_integration(path: str, extra_params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    params = {"limit": 200, "offset": 0}
    if extra_params:
        params.update(extra_params)
    items: List[Dict[str, Any]] = []
    while True:
        resp = _get(f"{NET_INTEGRATION_BASE}{path}", _h_key(), params=params)
        data = resp.get("data", [])
        items.extend(data)
        count, limit, total = resp.get("count", 0), resp.get("limit", 0), resp.get("totalCount", 0)
        if count != limit or total <= len(items):
            break
        params["offset"] += limit
    return items

# ========= Capability probe =========
@mcp.resource("unifi://capabilities")
async def capabilities() -> Dict[str, Any]:
    out: Dict[str, Any] = {"integration": {}, "access": {}, "legacy": {}, "protect": {}, "sitemanager": {}}

    def try_get(label: str, url: str, headers: Optional[Dict[str, str]] = None):
        try:
            r = requests.get(url, headers=headers, verify=VERIFY_TLS, timeout=6)
            out[label] = {"url": url, "status": r.status_code}
        except Exception as e:
            out[label] = {"url": url, "error": str(e)}

    # Network Integration
    try_get("integration.sites", "/".join([NET_INTEGRATION_BASE, "sites"]), _h_key())
    try_get("integration.devices_default", "/".join([NET_INTEGRATION_BASE, "sites", "default", "devices"]), _h_key())
    try_get("integration.clients_default", "/".join([NET_INTEGRATION_BASE, "sites", "default", "clients"]), _h_key())
    try_get("integration.wlans_default", "/".join([NET_INTEGRATION_BASE, "sites", "default", "wlans"]), _h_key())

    # Access
    try_get("access.doors", "/".join([ACCESS_BASE, "doors"]), _h_key())
    try_get("access.readers", "/".join([ACCESS_BASE, "readers"]), _h_key())
    try_get("access.events", "/".join([ACCESS_BASE, "events"]), _h_key())

    # Legacy quick check
    try:
        legacy_login()
        r = LEGACY.get("/".join([LEGACY_BASE, "s", "default", "stat", "sta"]), verify=VERIFY_TLS, timeout=6)
        out["legacy.stat_sta"] = {"url": r.request.url, "status": r.status_code}
    except Exception as e:
        out["legacy.stat_sta"] = {"error": str(e)}

    # Protect
    def try_get_protect(label: str, path: str):
        try:
            r = requests.get(f"{PROTECT_BASE}{path}", headers=_h_key(), verify=VERIFY_TLS, timeout=6)
            if r.status_code in (401, 403) and LEGACY_USER and LEGACY_PASS:
                legacy_login()
                r = LEGACY.get(f"{PROTECT_BASE}{path}", verify=VERIFY_TLS, timeout=6)
            out[f"protect.{label}"] = {"url": f"{PROTECT_BASE}{path}", "status": r.status_code}
        except Exception as e:
            out[f"protect.{label}"] = {"url": f"{PROTECT_BASE}{path}", "error": str(e)}

    try_get_protect("bootstrap", "/bootstrap")
    try_get_protect("cameras", "/cameras")
    try_get_protect("events", "/events")

    # Site Manager
    if SM_BASE and SM_TOKEN:
        try_get("sitemanager.root", f"{SM_BASE}/", {"Authorization": SM_TOKEN})
    else:
        out["sitemanager.info"] = "Set UNIFI_SITEMGR_BASE & UNIFI_SITEMGR_TOKEN to probe."

    return out

# ========= Health (consolidated) =========
# Note: The individual health resources are defined above in the triple-registered section

# Debug tool to see what FastMCP registered
@mcp.tool()
def debug_registry() -> Dict[str, Any]:
    """
    Lists resources, tools, and prompts currently registered.
    Helpful when a resource isn't visible in your inspector UI.
    """
    def grab(obj, names):
        for n in names:
            if hasattr(obj, n):
                return getattr(obj, n)
        return []

    resources = grab(mcp, ("resources", "_resources"))
    tools     = grab(mcp, ("tools", "_tools"))
    prompts   = grab(mcp, ("prompts", "_prompts"))

    def res_name(r):
        return getattr(r, "uri_template", getattr(r, "name", str(r)))
    def tool_name(t):
        return getattr(t, "name", str(t))
    def prompt_name(p):
        return getattr(p, "name", str(p))

    return {
        "resources": sorted([res_name(r) for r in resources]),
        "tools":     sorted([tool_name(t) for t in tools]),
        "prompts":   sorted([prompt_name(p) for p in prompts]),
    }

# ========= Network Integration: resources =========
@mcp.resource("sites://")
async def sites() -> List[Dict[str, Any]]:
    return paginate_integration("/sites")

@mcp.resource("sites://{site_id}/devices")
async def devices(site_id: str) -> List[Dict[str, Any]]:
    return paginate_integration(f"/sites/{site_id}/devices")

@mcp.resource("sites://{site_id}/clients")
async def clients(site_id: str) -> List[Dict[str, Any]]:
    return paginate_integration(f"/sites/{site_id}/clients")

@mcp.resource("sites://{site_id}/clients/active")
async def clients_active(site_id: str) -> List[Dict[str, Any]]:
    return paginate_integration(f"/sites/{site_id}/clients/active")

# WLANs with graceful fallback (Integration -> Legacy) and safe URL joins
@mcp.resource("sites://{site_id}/wlans")
async def wlans(site_id: str):
    # 1) Integration attempt (often 404/not exposed)
    try:
        url = "/".join([NET_INTEGRATION_BASE, "sites", site_id, "wlans"])
        res = _get(url, _h_key())
        return res.get("data", [])
    except UniFiHTTPError as e:
        if "404" not in str(e):
            raise
    # 2) Legacy fallback
    if LEGACY_USER and LEGACY_PASS:
        lr = legacy_get(f"/s/{site_id}/rest/wlanconf")
        return lr.get("data", lr)
    # 3) Explain
    return {
        "ok": False,
        "reason": "WLANs not exposed by Integration API and no legacy credentials provided.",
        "tried": [
            "/".join([NET_INTEGRATION_BASE, "sites", site_id, "wlans"]),
            f"{LEGACY_BASE}/s/{site_id}/rest/wlanconf (legacy)"
        ],
        "how_to_enable_legacy": "Set UNIFI_USERNAME and UNIFI_PASSWORD."
    }

# Search helpers
@mcp.resource("sites://{site_id}/search/clients/{query}")
async def search_clients(site_id: str, query: str):
    cs = await clients(site_id)
    q = query.lower()
    def hit(c): return any(q in str(c.get(k, "")).lower() for k in ("hostname", "name", "mac", "ip", "user"))
    return [c for c in cs if hit(c)]

@mcp.resource("sites://{site_id}/search/devices/{query}")
async def search_devices(site_id: str, query: str):
    ds = await devices(site_id)
    q = query.lower()
    def hit(d): return any(q in str(d.get(k, "")).lower() for k in ("name", "model", "mac", "ip", "ip_address"))
    return [d for d in ds if hit(d)]

# ========= UniFi Access: resources =========
@mcp.resource("access://doors")
async def access_doors() -> List[Dict[str, Any]]:
    res = _get("/".join([ACCESS_BASE, "doors"]), _h_key())
    return res.get("data", res)

@mcp.resource("access://readers")
async def access_readers() -> List[Dict[str, Any]]:
    res = _get("/".join([ACCESS_BASE, "readers"]), _h_key())
    return res.get("data", res)

@mcp.resource("access://users")
async def access_users() -> List[Dict[str, Any]]:
    res = _get("/".join([ACCESS_BASE, "users"]), _h_key())
    return res.get("data", res)

@mcp.resource("access://events")
async def access_events() -> List[Dict[str, Any]]:
    res = _get("/".join([ACCESS_BASE, "events"]), _h_key())
    return res.get("data", res)

# ========= UniFi Protect: resources =========
@mcp.resource("protect://nvr")
async def protect_nvr() -> Dict[str, Any]:
    return protect_get("/bootstrap")

@mcp.resource("protect://cameras")
async def protect_cameras() -> List[Dict[str, Any]]:
    res = protect_get("/cameras")
    if isinstance(res, dict) and "cameras" in res:
        return res["cameras"]
    return res

@mcp.resource("protect://camera/{camera_id}")
async def protect_camera(camera_id: str) -> Dict[str, Any]:
    return protect_get(f"/cameras/{camera_id}")

@mcp.resource("protect://events")
async def protect_events() -> List[Dict[str, Any]]:
    res = protect_get("/events")
    if isinstance(res, dict) and "events" in res:
        return res["events"]
    return res

@mcp.resource("protect://events/range/{start_ts}/{end_ts}")
async def protect_events_range(start_ts: str, end_ts: str) -> List[Dict[str, Any]]:
    res = protect_get("/events", params={"start": start_ts, "end": end_ts})
    if isinstance(res, dict) and "events" in res:
        return res["events"]
    return res

@mcp.resource("protect://streams/{camera_id}")
async def protect_streams(camera_id: str) -> Dict[str, Any]:
    cam = protect_get(f"/cameras/{camera_id}")
    return {
        "id": cam.get("id"),
        "name": cam.get("name"),
        "channels": cam.get("channels"),
        "isRtspEnabled": cam.get("isRtspEnabled")
    }

# ========= Action tools =========
# Integration API – safe set
@mcp.tool()
def block_client(site_id: str, mac: str) -> Dict[str, Any]:
    return _post("/".join([NET_INTEGRATION_BASE, "sites", site_id, "clients", "block"]), _h_key(), {"mac": mac})

@mcp.tool()
def unblock_client(site_id: str, mac: str) -> Dict[str, Any]:
    return _post("/".join([NET_INTEGRATION_BASE, "sites", site_id, "clients", "unblock"]), _h_key(), {"mac": mac})

@mcp.tool()
def kick_client(site_id: str, mac: str) -> Dict[str, Any]:
    return _post("/".join([NET_INTEGRATION_BASE, "sites", site_id, "clients", "kick"]), _h_key(), {"mac": mac})

@mcp.tool()
def locate_device(site_id: str, device_id: str, seconds: int = 30) -> Dict[str, Any]:
    return _post("/".join([NET_INTEGRATION_BASE, "sites", site_id, "devices", device_id, "locate"]), _h_key(), {"duration": seconds})

# Legacy-only example for WLAN toggle
@mcp.tool()
def wlan_set_enabled_legacy(site_id: str, wlan_id: str, enabled: bool) -> Dict[str, Any]:
    """Toggle WLAN (legacy API) when Integration API doesn't expose WLANs."""
    body = {"_id": wlan_id, "enabled": bool(enabled)}
    return legacy_post(f"/s/{site_id}/rest/wlanconf/{wlan_id}", body)

# Access – sample action (varies by build)
@mcp.tool()
def access_unlock_door(door_id: str, seconds: int = 5) -> Dict[str, Any]:
    return _post("/".join([ACCESS_BASE, "doors", door_id, "unlock"]), _h_key(), {"duration": seconds})

# Protect – safe starters
@mcp.tool()
def protect_camera_reboot(camera_id: str) -> Dict[str, Any]:
    return protect_post(f"/cameras/{camera_id}/reboot")

@mcp.tool()
def protect_camera_led(camera_id: str, enabled: bool) -> Dict[str, Any]:
    body = {"ledSettings": {"isEnabled": bool(enabled)}}
    return protect_post(f"/cameras/{camera_id}", body)

@mcp.tool()
def protect_toggle_privacy(camera_id: str, enabled: bool) -> Dict[str, Any]:
    body = {"privacyMode": bool(enabled)}
    return protect_post(f"/cameras/{camera_id}", body)

# ========= Prompt playbooks =========
@mcp.prompt("how_to_find_device")
def how_to_find_device():
    return {
        "description": "Find a network device and flash its LEDs.",
        "messages": [{"role": "system",
                      "content": "Search device via 'sites://{site_id}/search/devices/{query}', confirm, then call 'locate_device' for ~30s."}]
    }

@mcp.prompt("how_to_block_client")
def how_to_block_client():
    return {
        "description": "Find & block a client safely.",
        "messages": [{"role": "system",
                      "content": "List 'sites://{site_id}/clients/active', match MAC/host, confirm with user, then call 'block_client'. Offer 'unblock_client' as a reversal."}]
    }

@mcp.prompt("how_to_toggle_wlan")
def how_to_toggle_wlan():
    return {
        "description": "Toggle a WLAN using Integration if available, else Legacy.",
        "messages": [{"role": "system",
                      "content": "Fetch 'sites://{site_id}/wlans'. If returns an error object with ok:false, request legacy creds, then call 'wlan_set_enabled_legacy'."}]
    }

@mcp.prompt("how_to_manage_access")
def how_to_manage_access():
    return {
        "description": "Check doors/readers and perform a momentary unlock.",
        "messages": [{"role": "system",
                      "content": "List 'access://doors' to choose a door, confirm with the user, then call 'access_unlock_door' with a short duration."}]
    }

@mcp.prompt("how_to_find_camera")
def how_to_find_camera():
    return {
        "description": "Find a Protect camera and show its streams.",
        "messages": [{"role": "system",
                      "content": "Call 'protect://cameras', match by name/model, then 'protect://streams/{camera_id}' to present channels/RTSP."}]
    }

@mcp.prompt("how_to_review_motion")
def how_to_review_motion():
    return {
        "description": "Review recent motion/smart events in Protect.",
        "messages": [{"role": "system",
                      "content": "Fetch 'protect://events' or 'protect://events/range/{start_ts}/{end_ts}', then summarize by camera and type."}]
    }

@mcp.prompt("how_to_reboot_camera")
def how_to_reboot_camera():
    return {
        "description": "Safely reboot a Protect camera after confirmation.",
        "messages": [{"role": "system",
                      "content": "List 'protect://cameras', confirm the camera with the user, then call 'protect_camera_reboot' and warn about brief downtime."}]
    }

# ========= Entrypoint =========
if __name__ == "__main__":
    print("🚀 UniFi MCP – Integration + Legacy + Access + Protect (+ Site Manager stubs)")
    print(f"→ Controller: https://{UNIFI_HOST}:{UNIFI_PORT}  TLS verify={VERIFY_TLS}")
    if not UNIFI_API_KEY:
        print("⚠️ UNIFI_API_KEY not set — Integration/Access/Protect key-based calls may fail.")
    mcp.run(transport="stdio")
