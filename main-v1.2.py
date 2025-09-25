# main.py
# UniFi MCP Server – Integration + Legacy + Access + Protect + Site Manager
# - Rich resources for reads, curated tools for safe actions, prompt playbooks
# - Dual-mode auth (API key first; fall back to legacy cookie where needed)
# - Site Manager (cloud) API: hosts, sites, devices, ISP metrics, SD-WAN configs

from typing import Any, Dict, List, Optional, Literal
import os
import json
import requests
import urllib3
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Load environment variables from secrets.env
load_dotenv('secrets.env')

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ========= Configuration =========
UNIFI_API_KEY   = os.getenv("UNIFI_API_KEY", "")
UNIFI_HOST      = os.getenv("UNIFI_GATEWAY_HOST", "")
UNIFI_PORT      = os.getenv("UNIFI_GATEWAY_PORT", "443")
VERIFY_TLS      = os.getenv("UNIFI_VERIFY_TLS", "false").lower() in ("1", "true", "yes")

# Legacy credentials (for cookie-based fallback where needed)
LEGACY_USER     = os.getenv("UNIFI_USERNAME", "")
LEGACY_PASS     = os.getenv("UNIFI_PASSWORD", "")

# Site Manager (cloud)
# Stable v1: https://api.ui.com/v1/...
# Early Access: https://api.ui.com/ea/...
SM_BASE   = os.getenv("UNIFI_SITEMGR_BASE", "").rstrip("/")
SM_TOKEN  = os.getenv("UNIFI_SITEMGR_TOKEN", "")
SM_PREFIX = os.getenv("UNIFI_SITEMGR_PREFIX", "/v1").rstrip("/")  # default to stable /v1

# Base URLs for local controller
NET_INTEGRATION_BASE = f"https://{UNIFI_HOST}:{UNIFI_PORT}/proxy/network/integrations/v1" if UNIFI_HOST else ""
LEGACY_BASE          = f"https://{UNIFI_HOST}:{UNIFI_PORT}/proxy/network/api" if UNIFI_HOST else ""
ACCESS_BASE          = f"https://{UNIFI_HOST}:{UNIFI_PORT}/proxy/access/api/v1" if UNIFI_HOST else ""
PROTECT_BASE         = f"https://{UNIFI_HOST}:{UNIFI_PORT}/proxy/protect/api" if UNIFI_HOST else ""

REQUEST_TIMEOUT_S    = int(os.getenv("UNIFI_TIMEOUT_S", "15"))

mcp = FastMCP("unifi")

# ========= HTTP helpers =========
class UniFiHTTPError(RuntimeError):
    """Raised on HTTP errors to unify error handling."""
    pass

def _raise_for(r: requests.Response) -> Dict[str, Any]:
    """Raise for HTTP status and return JSON if any."""
    try:
        r.raise_for_status()
        return r.json() if r.text.strip() else {}
    except requests.exceptions.HTTPError as e:
        body = (r.text or "")[:800]
        raise UniFiHTTPError(f"{r.request.method} {r.url} -> {r.status_code} {r.reason}; body: {body}") from e

def _h_key() -> Dict[str, str]:
    if not UNIFI_API_KEY:
        raise UniFiHTTPError("UNIFI_API_KEY not configured.")
    return {"X-API-Key": UNIFI_API_KEY, "Content-Type": "application/json"}

def _get(url: str, headers: Dict[str, str], params=None, timeout=REQUEST_TIMEOUT_S) -> Dict[str, Any]:
    return _raise_for(requests.get(url, headers=headers, params=params, verify=VERIFY_TLS, timeout=timeout))

def _post(url: str, headers: Dict[str, str], body=None, timeout=REQUEST_TIMEOUT_S) -> Dict[str, Any]:
    return _raise_for(requests.post(url, headers=headers, json=body, verify=VERIFY_TLS, timeout=timeout))

# ========= Legacy session (cookie auth) =========
LEGACY = requests.Session()

def legacy_login():
    if not (LEGACY_USER and LEGACY_PASS):
        raise UniFiHTTPError("Legacy login requires UNIFI_USERNAME and UNIFI_PASSWORD.")
    if not UNIFI_HOST:
        raise UniFiHTTPError("Legacy login requires UNIFI_GATEWAY_HOST.")
    r = LEGACY.post(
        f"https://{UNIFI_HOST}:{UNIFI_PORT}/api/auth/login",
        json={"username": LEGACY_USER, "password": LEGACY_PASS},
        verify=VERIFY_TLS,
        timeout=REQUEST_TIMEOUT_S,
    )
    _raise_for(r)

def legacy_get(path: str, params=None) -> Dict[str, Any]:
    if not LEGACY_BASE:
        raise UniFiHTTPError("Legacy API requires UNIFI_GATEWAY_HOST.")
    if not LEGACY.cookies:
        legacy_login()
    r = LEGACY.get(f"{LEGACY_BASE}{path}", params=params, verify=VERIFY_TLS, timeout=REQUEST_TIMEOUT_S)
    return _raise_for(r)

def legacy_post(path: str, body=None) -> Dict[str, Any]:
    if not LEGACY_BASE:
        raise UniFiHTTPError("Legacy API requires UNIFI_GATEWAY_HOST.")
    if not LEGACY.cookies:
        legacy_login()
    r = LEGACY.post(f"{LEGACY_BASE}{path}", json=body, verify=VERIFY_TLS, timeout=REQUEST_TIMEOUT_S)
    return _raise_for(r)

# ========= UniFi Protect helpers =========
def protect_get(path: str, params=None) -> Dict[str, Any]:
    """Use API key first; gracefully fall back to legacy cookie if 401/403."""
    if not PROTECT_BASE:
        raise UniFiHTTPError("Protect API requires UNIFI_GATEWAY_HOST.")
    
    # Try API key first
    if UNIFI_API_KEY:
        try:
            r = requests.get(f"{PROTECT_BASE}{path}", headers=_h_key(), params=params, verify=VERIFY_TLS, timeout=REQUEST_TIMEOUT_S)
            if r.status_code == 200:
                return _raise_for(r)
            if r.status_code not in (401, 403):
                return _raise_for(r)
        except requests.exceptions.RequestException:
            pass  # Fall back to legacy auth
    
    # Fall back to legacy cookie auth
    if not LEGACY.cookies:
        legacy_login()
    r = LEGACY.get(f"{PROTECT_BASE}{path}", params=params, verify=VERIFY_TLS, timeout=REQUEST_TIMEOUT_S)
    return _raise_for(r)

def protect_post(path: str, body=None) -> Dict[str, Any]:
    """Use API key first; gracefully fall back to legacy cookie if 401/403."""
    if not PROTECT_BASE:
        raise UniFiHTTPError("Protect API requires UNIFI_GATEWAY_HOST.")
    
    # Try API key first
    if UNIFI_API_KEY:
        try:
            r = requests.post(f"{PROTECT_BASE}{path}", headers=_h_key(), json=body, verify=VERIFY_TLS, timeout=REQUEST_TIMEOUT_S)
            if r.status_code in (200, 204):
                return _raise_for(r)
            if r.status_code not in (401, 403):
                return _raise_for(r)
        except requests.exceptions.RequestException:
            pass  # Fall back to legacy auth
    
    # Fall back to legacy cookie auth
    if not LEGACY.cookies:
        legacy_login()
    r = LEGACY.post(f"{PROTECT_BASE}{path}", json=body, verify=VERIFY_TLS, timeout=REQUEST_TIMEOUT_S)
    return _raise_for(r)

# ========= Site Manager helpers =========
def _sm_headers() -> Dict[str, str]:
    if not SM_BASE or not SM_TOKEN:
        raise UniFiHTTPError("Site Manager not configured. Set UNIFI_SITEMGR_BASE and UNIFI_SITEMGR_TOKEN.")
    token = SM_TOKEN if SM_TOKEN.lower().startswith("bearer ") else f"Bearer {SM_TOKEN}"
    return {"Authorization": token, "Content-Type": "application/json"}

def _sm_url(path: str) -> str:
    """Join SM_BASE + SM_PREFIX + path, all assumed to start with '/' except SM_BASE."""
    return f"{SM_BASE}{SM_PREFIX}{path}"

def sm_get(path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    url = _sm_url(path)
    r = requests.get(url, headers=_sm_headers(), params=params, verify=VERIFY_TLS, timeout=REQUEST_TIMEOUT_S)
    return _raise_for(r)

def sm_post(path: str, body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    url = _sm_url(path)
    r = requests.post(url, headers=_sm_headers(), json=body or {}, verify=VERIFY_TLS, timeout=REQUEST_TIMEOUT_S)
    return _raise_for(r)

def sm_paginate(path: str, extra_params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Handles both array responses and {data/items,count,limit,totalCount} wrappers.
    """
    params = {"limit": 200, "offset": 0}
    if extra_params:
        params.update(extra_params)
    items: List[Dict[str, Any]] = []
    while True:
        resp = sm_get(path, params=params)
        # Flexible extraction
        data = resp.get("data", resp if isinstance(resp, list) else resp.get("items", []))
        if isinstance(data, list):
            items.extend(data)
        # Paging heuristic
        limit  = resp.get("limit", params["limit"])
        total  = resp.get("totalCount", None)
        count  = resp.get("count", len(data) if isinstance(data, list) else 0)
        if total is not None and len(items) >= int(total):
            break
        if count != limit:
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

# --- ISP Metrics (currently EA under /ea/isp-metrics/:type) ---
# Guard valid metric types to give helpful errors.
ISPMetricType = Literal["availability", "latency", "loss", "throughput"]
_VALID_ISP_METRICS = {"availability", "latency", "loss", "throughput"}

def _ea_prefix_for_isp() -> str:
    """
    ISP metrics are currently under EA. Even if SM_PREFIX is /v1, we target /ea for these endpoints.
    If/when they graduate to /v1, update this function.
    """
    return "/ea"

@mcp.resource("sitemanager://isp/metrics/{metric_type}")
async def sm_isp_metrics(metric_type: str) -> Dict[str, Any]:
    mt = metric_type.lower().strip()
    if mt not in _VALID_ISP_METRICS:
        raise UniFiHTTPError(f"Invalid ISP metric_type '{metric_type}'. Choose one of: {sorted(_VALID_ISP_METRICS)}")
    ea = _ea_prefix_for_isp()
    # GET /ea/isp-metrics/:type
    url = f"{SM_BASE}{ea}/isp-metrics/{mt}"
    r = requests.get(url, headers=_sm_headers(), verify=VERIFY_TLS, timeout=REQUEST_TIMEOUT_S)
    return _raise_for(r)

@mcp.tool()
def sm_isp_metrics_query(
    metric_type: ISPMetricType,
    start: str,
    end: str,
    granularity: str = "5m",
    filters_json: str = "{}"
) -> Dict[str, Any]:
    """
    Query a specific ISP metric type over a time range.
    - metric_type: availability | latency | loss | throughput
    - start/end: ISO8601 timestamps (e.g., 2025-09-21T00:00:00Z)
    - granularity: e.g., "5m", "1h"
    - filters_json: JSON for label filters (e.g., {"siteId":"...", "hostId":"..."})
    """
    mt = (metric_type or "").lower().strip()
    if mt not in _VALID_ISP_METRICS:
        raise UniFiHTTPError(f"Invalid ISP metric_type '{metric_type}'. Choose one of: {sorted(_VALID_ISP_METRICS)}")
    try:
        filters = json.loads(filters_json) if filters_json else {}
        if not isinstance(filters, dict):
            raise ValueError("filters_json must decode to an object")
    except Exception as e:
        raise UniFiHTTPError(f"filters_json must be valid JSON: {e}")

    body = {
        "start": start,
        "end": end,
        "granularity": granularity,
        "filters": filters
    }
    ea = _ea_prefix_for_isp()
    # POST /ea/isp-metrics/:type/query
    url = f"{SM_BASE}{ea}/isp-metrics/{mt}/query"
    r = requests.post(url, headers=_sm_headers(), json=body, verify=VERIFY_TLS, timeout=REQUEST_TIMEOUT_S)
    return _raise_for(r)

# --- SD-WAN ---
@mcp.resource("sitemanager://sdwan/configs")
async def sm_sdwan_configs() -> List[Dict[str, Any]]:
    return sm_paginate("/sdwan/configs")

@mcp.resource("sitemanager://sdwan/configs/{config_id}")
async def sm_sdwan_config_by_id(config_id: str) -> Dict[str, Any]:
    return sm_get(f"/sdwan/configs/{config_id}")

@mcp.resource("sitemanager://sdwan/configs/{config_id}/status")
async def sm_sdwan_config_status(config_id: str) -> Dict[str, Any]:
    return sm_get(f"/sdwan/configs/{config_id}/status")

# ========= Site Manager prompts =========
@mcp.prompt("how_to_list_cloud_sites")
def how_to_list_cloud_sites():
    return {
        "description": "List UniFi sites via Site Manager (cloud).",
        "messages": [{
            "role": "system",
            "content": "Call 'sitemanager://sites' and present site names/ids. Then let the user choose a site for deeper queries."
        }]
    }

@mcp.prompt("how_to_list_cloud_devices")
def how_to_list_cloud_devices():
    return {
        "description": "List devices for a given cloud site.",
        "messages": [{
            "role": "system",
            "content": "After selecting a site, call 'sitemanager://sites/{site_id}/devices' and summarize by role/model/status."
        }]
    }

@mcp.prompt("how_to_query_isp_metrics")
def how_to_query_isp_metrics():
    return {
        "description": "Query ISP performance metrics (loss/latency/throughput/availability) over a time range.",
        "messages": [{
            "role": "system",
            "content": "Use 'sitemanager://isp/metrics/{metric_type}' to discover labels/availability, then call the 'sm_isp_metrics_query' tool with metric_type, start, end, granularity, and optional filters."
        }]
    }

@mcp.prompt("how_to_view_sdwan_status")
def how_to_view_sdwan_status():
    return {
        "description": "Inspect SD-WAN configs and status.",
        "messages": [{
            "role": "system",
            "content": "List 'sitemanager://sdwan/configs', select a config, then call 'sitemanager://sdwan/configs/{config_id}' and '.../{config_id}/status' to summarize health and tunnels."
        }]
    }

# ========= Configuration validation =========
def validate_config():
    """Validate configuration and provide helpful warnings."""
    issues = []
    
    if not SM_BASE or not SM_TOKEN:
        issues.append("⚠️ Site Manager not configured (ISP metrics, cloud sites/devices unavailable)")
    
    if not UNIFI_HOST:
        issues.append("⚠️ Local controller not configured (Protect, Access, Legacy features unavailable)")
    elif not UNIFI_API_KEY and not (LEGACY_USER and LEGACY_PASS):
        issues.append("⚠️ No authentication configured for local controller")
    
    return issues

# ========= Entrypoint =========
if __name__ == "__main__":
    print("🚀 UniFi MCP – Integration + Legacy + Access + Protect + Site Manager")
    
    # Validate configuration
    config_issues = validate_config()
    
    if UNIFI_HOST:
        print(f"→ Controller: https://{UNIFI_HOST}:{UNIFI_PORT}  TLS verify={VERIFY_TLS}")
        if UNIFI_API_KEY:
            print("✅ API key configured for local controller")
        if LEGACY_USER and LEGACY_PASS:
            print("✅ Legacy credentials configured")
    
    if SM_BASE and SM_TOKEN:
        print(f"→ Site Manager: {SM_BASE}{SM_PREFIX}  (ISP metrics served via /ea)")
        print("✅ Site Manager configured")
    
    # Print any configuration issues
    for issue in config_issues:
        print(issue)
    
    if not config_issues:
        print("✅ All systems configured and ready!")
    
    mcp.run(transport="stdio")
