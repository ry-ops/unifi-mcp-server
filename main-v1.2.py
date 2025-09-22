```python
# main.py
# UniFi MCP Server – Integration + Legacy + Access + Protect + Site Manager
# - Rich resources for reads, curated tools for safe actions, prompt playbooks
# - Dual-mode auth (API key first; fall back to legacy cookie where needed)
# - Site Manager (cloud) API: hosts, sites, devices, ISP metrics, SD-WAN configs

from typing import Any, Dict, List, Optional
import os, json, requests, urllib3
from mcp.server.fastmcp import FastMCP

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ========= Configuration =========
UNIFI_API_KEY   = os.getenv("UNIFI_API_KEY", "API_KEY_HERE")
UNIFI_HOST      = os.getenv("UNIFI_GATEWAY_HOST", "GATEWAY_HOST_HERE")
UNIFI_PORT      = os.getenv("UNIFI_GATEWAY_PORT", "443")
VERIFY_TLS      = os.getenv("UNIFI_VERIFY_TLS", "false").lower() in ("1", "true", "yes")

# Legacy credentials
LEGACY_USER     = os.getenv("UNIFI_USERNAME", "")
LEGACY_PASS     = os.getenv("UNIFI_PASSWORD", "")

# Site Manager (cloud)
SM_BASE         = os.getenv("UNIFI_SITEMGR_BASE", "").rstrip("/")
SM_TOKEN        = os.getenv("UNIFI_SITEMGR_TOKEN", "")
SM_PREFIX       = os.getenv("UNIFI_SITEMGR_PREFIX", "/api/v1").rstrip("/")

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

# Legacy session
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
    try:
        r = requests.get(f"{PROTECT_BASE}{path}", headers=_h_key(), params=params, verify=VERIFY_TLS, timeout=REQUEST_TIMEOUT_S)
        if r.status_code == 200:
            return _raise_for(r)
        if r.status_code not in (401, 403):
            return _raise_for(r)
    except Exception:
        pass
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

# ========= Site Manager helpers =========
def _sm_headers() -> Dict[str, str]:
    if not SM_BASE or not SM_TOKEN:
        raise UniFiHTTPError("Site Manager not configured.")
    token = SM_TOKEN if SM_TOKEN.lower().startswith("bearer ") else f"Bearer {SM_TOKEN}"
    return {"Authorization": token, "Content-Type": "application/json"}

def sm_get(path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    url = f"{SM_BASE}{SM_PREFIX}{path}"
    r = requests.get(url, headers=_sm_headers(), params=params, verify=VERIFY_TLS, timeout=REQUEST_TIMEOUT_S)
    return _raise_for(r)

def sm_post(path: str, body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    url = f"{SM_BASE}{SM_PREFIX}{path}"
    r = requests.post(url, headers=_sm_headers(), json=body or {}, verify=VERIFY_TLS, timeout=REQUEST_TIMEOUT_S)
    return _raise_for(r)

def sm_paginate(path: str, extra_params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    params = {"limit": 200, "offset": 0}
    if extra_params:
        params.update(extra_params)
    items: List[Dict[str, Any]] = []
    while True:
        resp = sm_get(path, params=params)
        data = resp.get("data", resp if isinstance(resp, list) else [])
        if isinstance(data, list):
            items.extend(data)
        else:
            items.extend(data.get("items", []))
        count  = resp.get("count", len(items))
        limit  = resp.get("limit", params["limit"])
        total  = resp.get("totalCount", None)
        if total is None or count != limit or (total is not None and len(items) >= total):
            break
        params["offset"] += limit
    return items

# ========= Site Manager resources =========
@mcp.resource("sitemanager://hosts")
async def sm_hosts() -> List[Dict[str, Any]]:
    return sm_paginate("/hosts")

@mcp.resource("sitemanager://hosts/{host_id}")
async def sm_host_by_id(host_id: str) -> Dict[str, Any]:
    return sm_get(f"/hosts/{host_id}")

@mcp.resource("sitemanager://sites")
async def sm_sites() -> List[Dict[str, Any]]:
    return sm_paginate("/sites")

@mcp.resource("sitemanager://sites/{site_id}/devices")
async def sm_site_devices(site_id: str) -> List[Dict[str, Any]]:
    return sm_paginate(f"/sites/{site_id}/devices")

@mcp.resource("sitemanager://isp/metrics")
async def sm_isp_metrics() -> Dict[str, Any]:
    return sm_get("/isp/metrics")

@mcp.resource("sitemanager://sdwan/configs")
async def sm_sdwan_configs() -> List[Dict[str, Any]]:
    return sm_paginate("/sdwan/configs")

@mcp.resource("sitemanager://sdwan/configs/{config_id}")
async def sm_sdwan_config_by_id(config_id: str) -> Dict[str, Any]:
    return sm_get(f"/sdwan/configs/{config_id}")

@mcp.resource("sitemanager://sdwan/configs/{config_id}/status")
async def sm_sdwan_config_status(config_id: str) -> Dict[str, Any]:
    return sm_get(f"/sdwan/configs/{config_id}/status")

# ========= Site Manager tool =========
@mcp.tool()
def sm_isp_metrics_query(metric: str, start: str, end: str, granularity: str = "5m", filters_json: str = "{}") -> Dict[str, Any]:
    try:
        filters = json.loads(filters_json) if filters_json else {}
    except Exception as e:
        raise UniFiHTTPError(f"filters_json must be valid JSON: {e}")
    body = {"metric": metric, "start": start, "end": end, "granularity": granularity, "filters": filters}
    return sm_post("/isp/metrics/query", body)

# ========= Site Manager prompts =========
@mcp.prompt("how_to_list_cloud_sites")
def how_to_list_cloud_sites():
    return {
        "description": "List UniFi sites via Site Manager (cloud).",
        "messages": [{"role": "system",
                      "content": "Call 'sitemanager://sites' and present site names/ids. Then let the user choose a site for deeper queries."}]
    }

@mcp.prompt("how_to_list_cloud_devices")
def how_to_list_cloud_devices():
    return {
        "description": "List devices for a given cloud site.",
        "messages": [{"role": "system",
                      "content": "After selecting a site, call 'sitemanager://sites/{site_id}/devices' and summarize by role/model/status."}]
    }

@mcp.prompt("how_to_query_isp_metrics")
def how_to_query_isp_metrics():
    return {
        "description": "Query ISP performance metrics (loss/latency/throughput) over a time range.",
        "messages": [{"role": "system",
                      "content": "Use 'sitemanager://isp/metrics' to discover available metrics, then call the 'sm_isp_metrics_query' tool with metric, start, end, granularity, and optional filters."}]
    }

@mcp.prompt("how_to_view_sdwan_status")
def how_to_view_sdwan_status():
    return {
        "description": "Inspect SD-WAN configs and status.",
        "messages": [{"role": "system",
                      "content": "List 'sitemanager://sdwan/configs', select a config, then call 'sitemanager://sdwan/configs/{config_id}' and '.../{config_id}/status' to summarize health and tunnels."}]
    }

# ========= Entrypoint =========
if __name__ == "__main__":
    print("🚀 UniFi MCP – Integration + Legacy + Access + Protect + Site Manager")
    print(f"→ Controller: https://{UNIFI_HOST}:{UNIFI_PORT}  TLS verify={VERIFY_TLS}")
    if not UNIFI_API_KEY:
        print("⚠️ UNIFI_API_KEY not set — Integration/Access/Protect key-based calls may fail.")
    if not SM_BASE or not SM_TOKEN:
        print("⚠️ Site Manager not configured — set UNIFI_SITEMGR_BASE and UNIFI_SITEMGR_TOKEN.")
    mcp.run(transport="stdio")
```
