# main.py
# UniFi MCP Server – Integration + Legacy + Access + Protect (+ Site Manager stubs)
# - Rich resources for reads, curated tools for safe actions, prompt playbooks
# - Dual-mode auth (API key first; fall back to legacy cookie where needed)
# - Adds health alias (health://unifi) and debug_registry tool

from typing import Any, Dict, List, Optional
import os, json, requests, urllib3
from mcp.server.fastmcp import FastMCP

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ========= Configuration =========
UNIFI_API_KEY   = os.getenv("UNIFI_API_KEY", "API_KEY_HERE")
UNIFI_HOST      = os.getenv("UNIFI_GATEWAY_HOST", "GATEWAY_HOST_HERE")
UNIFI_PORT      = os.getenv("UNIFI_GATEWAY_PORT", "443")
VERIFY_TLS      = os.getenv("UNIFI_VERIFY_TLS", "false").lower() in ("1", "true", "yes")

# Legacy credentials (optional; enable for config endpoints not in Integration API)
LEGACY_USER     = os.getenv("UNIFI_USERNAME", "UNIFI_USERNAME_HERE")
LEGACY_PASS     = os.getenv("UNIFI_PASSWORD", "UNIFI_PASSWORD_HERE")

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
    try_get("integration.sites", f"{NET_INTEGRATION_BASE}/sites", _h_key())
    try_get("integration.devices_default", f"{NET_INTEGRATION_BASE}/sites/default/devices", _h_key())
    try_get("integration.clients_default", f"{NET_INTEGRATION_BASE}/sites/default/clients", _h_key())
    try_get("integration.wlans_default", f"{NET_INTEGRATION_BASE}/sites/default/wlans", _h_key())

    # Access
    try_get("access.doors", f"{ACCESS_BASE}/doors", _h_key())
    try_get("access.readers", f"{ACCESS_BASE}/readers", _h_key())
    try_get("access.events", f"{ACCESS_BASE}/events", _h_key())

    # Legacy quick check
    try:
        legacy_login()
        r = LEGACY.get(f"{LEGACY_BASE}/s/default/stat/sta", verify=VERIFY_TLS, timeout=6)
        out["legacy.stat_sta"] = {"url": r.request.url, "status": r.status_code}
    except Exception as e:
        out["legacy.stat_sta"] = {"error": str(e)}

    # Protect
    def try_get_protect(label: str, path: str):
        try:
            # API key
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

# ========= Health =========
@mcp.resource("unifi://health")
async def health() -> Dict[str, Any]:
    try:
        me = _get(f"{NET_INTEGRATION_BASE}/sites", _h_key())  # simple check
        return {"ok": True, "integration_sites_count": me.get("count")}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# Alias resource for UIs that list this scheme more reliably
@mcp.resource("health://unifi")
async def health_alias() -> Dict[str, Any]:
    return await health()

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

# WLANs with graceful fallback (Integration -> Legacy)
@mcp.resource("sites://{site_id}/wlans")
async def wlans(site_id: str):
    # 1) Integration attempt (often 404/not exposed)
    try:
        res = _get(f"{NET_INTEGRATION_BASE}/sites/{site_id}/wlans", _h_key())
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
            f"{NET_INTEGRATION_
