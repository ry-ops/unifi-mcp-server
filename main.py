# main.py
# UniFi MCP Server – Integration + Legacy + Access + Protect (+ Site Manager stubs)
# - Rich resources for reads, curated tools for safe actions, prompt playbooks
# - Dual-mode auth (API key first; fall back to legacy cookie where needed)
# - Includes health alias (health://unifi) and debug_registry tool
# - Safer URL building to avoid line-wrap identifier breaks
# - Enhanced status management and list hosts functionality

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
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

# ========= UniFi Health Functions =========
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

# ========= Enhanced List Hosts Functions =========
def list_hosts_api_ui_com_format():
    """
    Exact implementation matching your provided examples:
    - import http.client approach  
    - import requests approach
    Both for https://api.ui.com/v1/hosts
    """
    results = {
        "timestamp": datetime.now().isoformat(),
        "http_client_method": {},
        "requests_method": {},
        "unified_response": {}
    }
    
    # Method 1: Using http.client (your first example)
    try:
        import http.client
        conn = http.client.HTTPSConnection("api.ui.com")
        payload = ''
        headers = {
            'Accept': 'application/json',
            'X-API-Key': SM_TOKEN  # Use your SM_TOKEN as the X-API-Key
        }
        conn.request("GET", "/v1/hosts", payload, headers)
        res = conn.getresponse()
        data = res.read()
        
        results["http_client_method"] = {
            "success": res.status == 200,
            "status_code": res.status,
            "raw_data": data.decode("utf-8"),
            "parsed_data": json.loads(data.decode("utf-8")) if res.status == 200 else None
        }
        conn.close()
        
    except Exception as e:
        results["http_client_method"] = {"error": str(e)}
    
    # Method 2: Using requests (your second example)
    try:
        url = "https://api.ui.com/v1/hosts"
        payload = {}
        headers = {
            'Accept': 'application/json',
            'X-API-Key': SM_TOKEN  # Use your SM_TOKEN as the X-API-Key
        }
        response = requests.request("GET", url, headers=headers, data=payload, 
                                  verify=VERIFY_TLS, timeout=REQUEST_TIMEOUT_S)
        
        results["requests_method"] = {
            "success": response.status_code == 200,
            "status_code": response.status_code,
            "response_text": response.text,
            "parsed_data": response.json() if response.status_code == 200 else None
        }
        
    except Exception as e:
        results["requests_method"] = {"error": str(e)}
    
    # Create unified response
    if results["requests_method"].get("success"):
        results["unified_response"] = results["requests_method"]["parsed_data"]
    elif results["http_client_method"].get("success"):
        results["unified_response"] = results["http_client_method"]["parsed_data"]
    
    return results

def get_correct_site_ids():
    """
    Get the correct site IDs from your controller
    Since 'default' is failing, we need to discover the actual site IDs
    """
    try:
        # Try to get sites from Integration API
        resp = _get(f"{NET_INTEGRATION_BASE}/sites", _h_key())
        sites = resp.get("data", [])
        return [site.get("id") for site in sites if site.get("id")]
    except Exception as e:
        print(f"Failed to get sites from Integration API: {e}")
        
        # Try legacy API to get sites
        try:
            legacy_login()
            resp = legacy_get("/self/sites")
            sites = resp.get("data", [])
            return [site.get("name") for site in sites if site.get("name")]
        except Exception as e2:
            print(f"Failed to get sites from Legacy API: {e2}")
            
    return []

def list_hosts_with_correct_sites():
    """
    List hosts using the correct site IDs discovered from your controller
    """
    result = {
        "success": False,
        "discovered_sites": [],
        "hosts_by_site": {},
        "total_hosts": 0,
        "errors": []
    }
    
    # Discover correct site IDs
    site_ids = get_correct_site_ids()
    result["discovered_sites"] = site_ids
    
    if not site_ids:
        result["errors"].append("No valid site IDs discovered")
        return result
    
    # Try each site
    for site_id in site_ids:
        try:
            # Get clients for this site
            clients = paginate_integration(f"/sites/{site_id}/clients")
            devices = paginate_integration(f"/sites/{site_id}/devices")
            
            site_hosts = {
                "site_id": site_id,
                "clients": clients,
                "devices": devices,
                "client_count": len(clients),
                "device_count": len(devices),
                "total": len(clients) + len(devices)
            }
            
            result["hosts_by_site"][site_id] = site_hosts
            result["total_hosts"] += site_hosts["total"]
            result["success"] = True
            
        except Exception as e:
            result["errors"].append(f"Site {site_id}: {str(e)}")
    
    return result

# ========= Status Manager Classes =========
@dataclass
class UniFiStatus:
    """Structured status information for UniFi components"""
    component: str
    status: str
    last_check: datetime
    details: Dict[str, Any]
    issues: List[str]

class UniFiStatusManager:
    """Centralized status management for all UniFi services"""
    
    def __init__(self):
        self.last_status_check = None
        self.cached_status = {}
        self.status_cache_duration = 300  # 5 minutes
    
    def get_comprehensive_status(self, site_id: str = None) -> Dict[str, Any]:
        """Get complete status of all UniFi services"""
        now = datetime.now()
        
        # Use discovered site ID if none provided
        if site_id is None:
            sites = get_correct_site_ids()
            site_id = sites[0] if sites else "default"
        
        # Check if we need to refresh cache
        if (self.last_status_check is None or 
            (now - self.last_status_check).seconds > self.status_cache_duration):
            self.cached_status = self._collect_all_status(site_id)
            self.last_status_check = now
        
        return self.cached_status
    
    def _collect_all_status(self, site_id: str) -> Dict[str, Any]:
        """Collect status from all UniFi services"""
        status = {
            "timestamp": datetime.now().isoformat(),
            "site_id": site_id,
            "overall_health": "unknown",
            "services": {},
            "summary": {
                "total_devices": 0,
                "online_devices": 0,
                "total_clients": 0,
                "active_clients": 0,
                "issues_count": 0
            }
        }
        
        # Check Integration API health
        try:
            health = _health_check()
            status["services"]["integration"] = {
                "status": "healthy" if health.get("ok") else "error",
                "details": health,
                "last_check": datetime.now().isoformat()
            }
        except Exception as e:
            status["services"]["integration"] = {
                "status": "error",
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }
        
        # Check devices status
        try:
            devices = paginate_integration(f"/sites/{site_id}/devices")
            online_devices = [d for d in devices if d.get("state") == 1]
            status["services"]["devices"] = {
                "status": "healthy",
                "total": len(devices),
                "online": len(online_devices),
                "offline": len(devices) - len(online_devices),
                "last_check": datetime.now().isoformat()
            }
            status["summary"]["total_devices"] = len(devices)
            status["summary"]["online_devices"] = len(online_devices)
        except Exception as e:
            status["services"]["devices"] = {
                "status": "error",
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }
        
        # Check clients status
        try:
            all_clients = paginate_integration(f"/sites/{site_id}/clients")
            active_clients = paginate_integration(f"/sites/{site_id}/clients/active")
            status["services"]["clients"] = {
                "status": "healthy",
                "total": len(all_clients),
                "active": len(active_clients),
                "last_check": datetime.now().isoformat()
            }
            status["summary"]["total_clients"] = len(all_clients)
            status["summary"]["active_clients"] = len(active_clients)
        except Exception as e:
            status["services"]["clients"] = {
                "status": "error",
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }
        
        # Check Access status (if available)
        try:
            doors_resp = _get(f"{ACCESS_BASE}/doors", _h_key())
            status["services"]["access"] = {
                "status": "healthy",
                "doors_count": len(doors_resp.get("data", [])),
                "last_check": datetime.now().isoformat()
            }
        except Exception as e:
            status["services"]["access"] = {
                "status": "unavailable",
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }
        
        # Check Protect status (if available)
        try:
            cameras = protect_get("/cameras")
            online_cameras = [c for c in cameras.get("data", []) if c.get("state") == "CONNECTED"]
            status["services"]["protect"] = {
                "status": "healthy",
                "cameras_total": len(cameras.get("data", [])),
                "cameras_online": len(online_cameras),
                "last_check": datetime.now().isoformat()
            }
        except Exception as e:
            status["services"]["protect"] = {
                "status": "unavailable",
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }
        
        # Calculate overall health
        status["overall_health"] = self._calculate_overall_health(status["services"])
        
        # Count issues
        status["summary"]["issues_count"] = sum(
            1 for service in status["services"].values() 
            if service["status"] in ["error", "degraded"]
        )
        
        return status
    
    def _calculate_overall_health(self, services: Dict[str, Any]) -> str:
        """Calculate overall system health based on service statuses"""
        statuses = [s["status"] for s in services.values()]
        
        if any(s == "error" for s in statuses):
            return "degraded"
        elif all(s in ["healthy", "unavailable"] for s in statuses):
            # Consider unavailable services (like Access/Protect) as OK if not configured
            return "healthy"
        else:
            return "unknown"
    
    def get_device_health_summary(self, site_id: str = None) -> Dict[str, Any]:
        """Get detailed device health information"""
        if site_id is None:
            sites = get_correct_site_ids()
            site_id = sites[0] if sites else "default"
            
        try:
            devices = paginate_integration(f"/sites/{site_id}/devices")
            
            summary = {
                "total_devices": len(devices),
                "by_state": {},
                "by_type": {},
                "issues": [],
                "uptime_stats": {"min": None, "max": None, "avg": None}
            }
            
            uptimes = []
            for device in devices:
                # Count by state
                state = device.get("state", "unknown")
                state_name = {1: "online", 0: "offline", -1: "error"}.get(state, "unknown")
                summary["by_state"][state_name] = summary["by_state"].get(state_name, 0) + 1
                
                # Count by type
                dev_type = device.get("type", "unknown")
                summary["by_type"][dev_type] = summary["by_type"].get(dev_type, 0) + 1
                
                # Check for issues
                if state == 0:  # offline
                    summary["issues"].append(f"{device.get('name', 'Unknown')} is offline")
                
                # Collect uptime
                uptime = device.get("uptime")
                if uptime:
                    uptimes.append(uptime)
            
            # Calculate uptime stats
            if uptimes:
                summary["uptime_stats"] = {
                    "min": min(uptimes),
                    "max": max(uptimes),
                    "avg": sum(uptimes) / len(uptimes)
                }
            
            return summary
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_client_activity_summary(self, site_id: str = None) -> Dict[str, Any]:
        """Get client activity and usage patterns"""
        if site_id is None:
            sites = get_correct_site_ids()
            site_id = sites[0] if sites else "default"
            
        try:
            active_clients = paginate_integration(f"/sites/{site_id}/clients/active")
            
            summary = {
                "active_count": len(active_clients),
                "by_connection": {},
                "bandwidth_usage": {"total_rx": 0, "total_tx": 0},
                "top_users": [],
                "last_updated": datetime.now().isoformat()
            }
            
            # Analyze active clients
            clients_with_usage = []
            for client in active_clients:
                # Count by connection type
                conn_type = "wired" if client.get("is_wired") else "wireless"
                summary["by_connection"][conn_type] = summary["by_connection"].get(conn_type, 0) + 1
                
                # Sum bandwidth
                rx_bytes = client.get("rx_bytes", 0)
                tx_bytes = client.get("tx_bytes", 0)
                summary["bandwidth_usage"]["total_rx"] += rx_bytes
                summary["bandwidth_usage"]["total_tx"] += tx_bytes
                
                # Collect for top users
                total_usage = rx_bytes + tx_bytes
                clients_with_usage.append({
                    "name": client.get("hostname") or client.get("name") or client.get("mac"),
                    "usage": total_usage,
                    "rx": rx_bytes,
                    "tx": tx_bytes
                })
            
            # Get top 5 users by bandwidth
            summary["top_users"] = sorted(
                clients_with_usage, 
                key=lambda x: x["usage"], 
                reverse=True
            )[:5]
            
            return summary
            
        except Exception as e:
            return {"error": str(e)}

# Initialize the status manager
status_manager = UniFiStatusManager()

# ========= UniFi Health (triple-registered) =========

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
    
    # Get correct site for testing
    sites = get_correct_site_ids()
    test_site = sites[0] if sites else "default"
    
    try_get("integration.devices", "/".join([NET_INTEGRATION_BASE, "sites", test_site, "devices"]), _h_key())
    try_get("integration.clients", "/".join([NET_INTEGRATION_BASE, "sites", test_site, "clients"]), _h_key())
    try_get("integration.wlans", "/".join([NET_INTEGRATION_BASE, "sites", test_site, "wlans"]), _h_key())

    # Access
    try_get("access.doors", "/".join([ACCESS_BASE, "doors"]), _h_key())
    try_get("access.readers", "/".join([ACCESS_BASE, "readers"]), _h_key())
    try_get("access.events", "/".join([ACCESS_BASE, "events"]), _h_key())

    # Legacy quick check
    try:
        legacy_login()
        r = LEGACY.get("/".join([LEGACY_BASE, "s", test_site, "stat", "sta"]), verify=VERIFY_TLS, timeout=6)
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

# ========= Network Integration: resources =========
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

# ========= Enhanced Status Resources =========
@mcp.resource("status://system")
async def system_status_resource() -> Dict[str, Any]:
    """Real-time system status resource"""
    return status_manager.get_comprehensive_status()

@mcp.resource("status://devices")
async def devices_status_resource() -> Dict[str, Any]:
    """Device health status resource"""
    return status_manager.get_device_health_summary()

@mcp.resource("status://clients")
async def clients_status_resource() -> Dict[str, Any]:
    """Client activity status resource"""
    return status_manager.get_client_activity_summary()

# ========= Tools =========

# Tool fallback (always visible in Tools tab)
@mcp.tool()
def unifi_health() -> Dict[str, Any]:
    """Ping the UniFi Integration API and report basic health."""
    return _health_check()

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

# ========= Enhanced Status Management Tools =========
@mcp.tool()
def get_system_status(site_id: str = None) -> Dict[str, Any]:
    """Get comprehensive UniFi system status including all services and components."""
    return status_manager.get_comprehensive_status(site_id)

@mcp.tool()
def get_device_health(site_id: str = None) -> Dict[str, Any]:
    """Get detailed device health summary with uptime and issue tracking."""
    return status_manager.get_device_health_summary(site_id)

@mcp.tool()
def get_client_activity(site_id: str = None) -> Dict[str, Any]:
    """Get client activity summary with bandwidth usage and connection types."""
    return status_manager.get_client_activity_summary(site_id)

@mcp.tool()
def get_quick_status() -> Dict[str, Any]:
    """Get a quick status overview of critical UniFi components."""
    health = _health_check()
    if not health.get("ok"):
        return {"status": "error", "message": "UniFi controller unreachable", "details": health}
    
    try:
        # Get correct site ID
        sites = get_correct_site_ids()
        site_id = sites[0] if sites else "default"
        
        # Quick counts
        devices = paginate_integration(f"/sites/{site_id}/devices")
        active_clients = paginate_integration(f"/sites/{site_id}/clients/active")
        
        online_devices = len([d for d in devices if d.get("state") == 1])
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "site_id": site_id,
            "summary": {
                "devices_online": f"{online_devices}/{len(devices)}",
                "active_clients": len(active_clients),
                "controller_responsive": True
            }
        }
    except Exception as e:
        return {
            "status": "degraded", 
            "message": f"Controller responsive but data collection failed: {str(e)}"
        }

# ========= Enhanced List Hosts Tools =========
@mcp.tool()
def list_hosts_api_format():
    """
    List hosts using the exact API format from your examples
    Matches: GET https://api.ui.com/v1/hosts with X-API-Key header
    """
    return list_hosts_api_ui_com_format()

@mcp.tool()
def discover_sites():
    """
    Discover the correct site IDs for your UniFi controller
    """
    return {
        "discovered_sites": get_correct_site_ids(),
        "note": "Use these site IDs instead of 'default' for local API calls"
    }

@mcp.tool()
def list_hosts_fixed():
    """
    List hosts using discovered site IDs instead of 'default'
    """
    return list_hosts_with_correct_sites()

@mcp.tool()
def working_list_hosts_example():
    """
    Complete working example that combines your API format with proper error handling
    """
    example_result = {
        "method_used": None,
        "data": None,
        "success": False,
        "error": None,
        "fallback_attempted": False
    }
    
    # Method 1: Try cloud API (your working method)
    try:
        url = "https://api.ui.com/v1/hosts"
        headers = {
            'Accept': 'application/json',
            'X-API-Key': SM_TOKEN
        }
        response = requests.get(url, headers=headers, verify=VERIFY_TLS, timeout=REQUEST_TIMEOUT_S)
        
        if response.status_code == 200:
            example_result["method_used"] = "cloud_api"
            example_result["data"] = response.json()
            example_result["success"] = True
            return example_result
        else:
            example_result["error"] = f"Cloud API failed: {response.status_code}"
    except Exception as e:
        example_result["error"] = f"Cloud API error: {str(e)}"
    
    # Method 2: Fallback to local API with proper site discovery
    example_result["fallback_attempted"] = True
    try:
        sites = get_correct_site_ids()
        if sites:
            site_id = sites[0]  # Use first available site
            clients = paginate_integration(f"/sites/{site_id}/clients")
            devices = paginate_integration(f"/sites/{site_id}/devices")
            
            # Format similar to cloud API response
            local_data = {
                "data": [],
                "source": "local_integration_api",
                "site_id": site_id
            }
            
            # Add clients as hosts
            for client in clients:
                host_entry = {
                    "id": client.get("mac"),
                    "type": "client",
                    "hostname": client.get("hostname"),
                    "ipAddress": client.get("ip"),
                    "mac": client.get("mac"),
                    "isActive": client.get("is_active", False)
                }
                local_data["data"].append(host_entry)
            
            # Add devices as hosts
            for device in devices:
                host_entry = {
                    "id": device.get("mac"),
                    "type": "device", 
                    "hostname": device.get("name"),
                    "ipAddress": device.get("ip"),
                    "mac": device.get("mac"),
                    "isActive": device.get("state") == 1
                }
                local_data["data"].append(host_entry)
            
            example_result["method_used"] = "local_integration_api"
            example_result["data"] = local_data
            example_result["success"] = True
            
        else:
            example_result["error"] = "No valid sites found for local API"
            
    except Exception as e:
        example_result["error"] = f"Local API fallback failed: {str(e)}"
    
    return example_result

@mcp.tool()
def debug_api_connectivity():
    """
    Debug API connectivity issues and provide troubleshooting information
    """
    debug_info = {
        "timestamp": datetime.now().isoformat(),
        "tests": {},
        "environment": {},
        "recommendations": []
    }
    
    # Test 1: Cloud API connectivity
    try:
        response = requests.get("https://api.ui.com/v1/hosts", 
                              headers={"Accept": "application/json", "X-API-Key": SM_TOKEN},
                              timeout=10, verify=VERIFY_TLS)
        debug_info["tests"]["cloud_api"] = {
            "status": "success" if response.status_code == 200 else "failed",
            "status_code": response.status_code,
            "response_length": len(response.text),
            "error": response.text[:200] if response.status_code != 200 else None
        }
    except Exception as e:
        debug_info["tests"]["cloud_api"] = {"status": "error", "error": str(e)}
    
    # Test 2: Local controller connectivity
    try:
        response = requests.get(f"{NET_INTEGRATION_BASE}/sites",
                              headers=_h_key(), timeout=10, verify=VERIFY_TLS)
        debug_info["tests"]["local_controller"] = {
            "status": "success" if response.status_code == 200 else "failed",
            "status_code": response.status_code,
            "response_length": len(response.text),
            "error": response.text[:200] if response.status_code != 200 else None
        }
    except Exception as e:
        debug_info["tests"]["local_controller"] = {"status": "error", "error": str(e)}
    
    # Test 3: Check if controller is reachable
    try:
        response = requests.get(f"https://{UNIFI_HOST}:{UNIFI_PORT}/",
                              timeout=5, verify=VERIFY_TLS)
        debug_info["tests"]["controller_reachable"] = {
            "status": "reachable",
            "status_code": response.status_code
        }
    except Exception as e:
        debug_info["tests"]["controller_reachable"] = {"status": "unreachable", "error": str(e)}
    
    # Environment check
    debug_info["environment"] = {
        "unifi_host": UNIFI_HOST,
        "unifi_port": UNIFI_PORT,
        "api_key_configured": bool(UNIFI_API_KEY and UNIFI_API_KEY != "API"),
        "cloud_base_configured": bool(SM_BASE),
        "cloud_token_configured": bool(SM_TOKEN),
        "verify_tls": VERIFY_TLS,
        "timeout": REQUEST_TIMEOUT_S,
        "discovered_sites": get_correct_site_ids()
    }
    
    # Generate recommendations
    if debug_info["tests"]["cloud_api"]["status"] != "success":
        debug_info["recommendations"].append("Cloud API failed - check UNIFI_SITEMGR_TOKEN")
    
    if debug_info["tests"]["local_controller"]["status"] != "success":
        debug_info["recommendations"].append("Local controller failed - check UNIFI_API_KEY and network connectivity")
    
    if debug_info["tests"]["controller_reachable"]["status"] != "reachable":
        debug_info["recommendations"].append("Controller unreachable - check UNIFI_GATEWAY_HOST and UNIFI_GATEWAY_PORT")
    
    return debug_info

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

# ========= Updated Original Tools with Fixed Site IDs =========
@mcp.tool()
def list_hosts(site_id: str = None) -> Dict[str, Any]:
    """List all network hosts/clients on the specified site"""
    if site_id is None:
        sites = get_correct_site_ids()
        site_id = sites[0] if sites else "default"
    
    try:
        clients = paginate_integration(f"/sites/{site_id}/clients")
        devices = paginate_integration(f"/sites/{site_id}/devices")
        
        return {
            "success": True,
            "site_id": site_id,
            "clients": clients,
            "devices": devices,
            "client_count": len(clients),
            "device_count": len(devices),
            "total_hosts": len(clients) + len(devices),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "site_id": site_id,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@mcp.tool()
def list_active_clients(site_id: str = None) -> Dict[str, Any]:
    """List only currently connected/active clients"""
    if site_id is None:
        sites = get_correct_site_ids()
        site_id = sites[0] if sites else "default"
        
    try:
        clients = paginate_integration(f"/sites/{site_id}/clients/active")
        return {
            "success": True,
            "site_id": site_id,
            "active_clients": clients,
            "count": len(clients),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "site_id": site_id,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@mcp.tool()
def find_device_by_mac(mac: str, site_id: str = None) -> Dict[str, Any]:
    """Find a specific device by MAC address"""
    if site_id is None:
        sites = get_correct_site_ids()
        site_id = sites[0] if sites else "default"
        
    try:
        # Search in clients
        clients = paginate_integration(f"/sites/{site_id}/clients")
        client_match = next((c for c in clients if c.get("mac", "").lower() == mac.lower()), None)
        
        # Search in devices
        devices = paginate_integration(f"/sites/{site_id}/devices")
        device_match = next((d for d in devices if d.get("mac", "").lower() == mac.lower()), None)
        
        result = {
            "success": True,
            "mac": mac,
            "site_id": site_id,
            "found": False,
            "client": client_match,
            "device": device_match,
            "timestamp": datetime.now().isoformat()
        }
        
        if client_match or device_match:
            result["found"] = True
            result["type"] = "client" if client_match else "device"
            result["data"] = client_match or device_match
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "mac": mac,
            "site_id": site_id,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@mcp.tool()
def list_hosts_cloud(page_size: int = 100) -> Dict[str, Any]:
    """List hosts using UniFi Site Manager (cloud) API"""
    result = {
        "success": False,
        "method": "cloud_api",
        "data": [],
        "error": None,
        "api_used": "sitemanager_cloud"
    }
    
    if not (SM_BASE and SM_TOKEN):
        result["error"] = "Cloud API requires UNIFI_SITEMGR_BASE and UNIFI_SITEMGR_TOKEN"
        return result
    
    try:
        headers = {
            "Accept": "application/json",
            "Authorization": SM_TOKEN,
            "Content-Type": "application/json"
        }
        
        params = {"limit": page_size}
        
        url = f"{SM_BASE}/v1/hosts"
        resp = requests.get(url, headers=headers, params=params, verify=VERIFY_TLS, timeout=REQUEST_TIMEOUT_S)
        
        if resp.status_code == 200:
            data = resp.json()
            result["success"] = True
            result["data"] = data.get("data", data)
            result["count"] = len(result["data"])
            result["raw_response"] = data
        else:
            result["error"] = f"HTTP {resp.status_code}: {resp.text[:500]}"
            
    except Exception as e:
        result["error"] = str(e)
    
    return result

@mcp.tool()
def list_all_hosts(site_id: str = None, include_cloud: bool = False) -> Dict[str, Any]:
    """Comprehensive host listing from local controller and optionally cloud"""
    if site_id is None:
        sites = get_correct_site_ids()
        site_id = sites[0] if sites else "default"
    
    result = {
        "success": False,
        "timestamp": datetime.now().isoformat(),
        "methods_tried": [],
        "local": {},
        "cloud": {},
        "combined_data": [],
        "summary": {}
    }
    
    # Try local Integration API first
    local_result = list_hosts(site_id)
    result["local"] = local_result
    result["methods_tried"].append("integration_api")
    
    # Try cloud API if requested and available
    if include_cloud:
        cloud_result = list_hosts_cloud()
        result["cloud"] = cloud_result
        result["methods_tried"].append("cloud_api")
    
    # Combine data
    combined_hosts = []
    
    if local_result.get("success"):
        # Add local clients and devices
        local_clients = local_result.get("clients", [])
        local_devices = local_result.get("devices", [])
        
        for client in local_clients:
            client["source"] = "local"
            combined_hosts.append(client)
        
        for device in local_devices:
            device["source"] = "local"
            combined_hosts.append(device)
    
    if include_cloud and result["cloud"].get("success"):
        # Add cloud hosts with a marker
        cloud_hosts = result["cloud"].get("data", [])
        for host in cloud_hosts:
            host["source"] = "cloud"
        combined_hosts.extend(cloud_hosts)
    
    result["combined_data"] = combined_hosts
    result["success"] = len(combined_hosts) > 0
    
    # Generate summary
    result["summary"] = {
        "total_hosts": len(combined_hosts),
        "local_success": local_result.get("success", False),
        "cloud_success": result["cloud"].get("success", False) if include_cloud else "not_requested",
        "local_count": len(local_result.get("clients", [])) + len(local_result.get("devices", [])) if local_result.get("success") else 0,
        "cloud_count": len(result["cloud"].get("data", [])) if include_cloud and result["cloud"].get("success") else 0
    }
    
    return result

@mcp.tool() 
def find_host_everywhere(identifier: str, site_id: str = None) -> Dict[str, Any]:
    """Search for a host by MAC, hostname, or name across local and cloud"""
    if site_id is None:
        sites = get_correct_site_ids()
        site_id = sites[0] if sites else "default"
        
    result = {
        "success": False,
        "identifier": identifier,
        "site_id": site_id,
        "matches": [],
        "search_locations": []
    }
    
    try:
        # Get comprehensive host list
        all_hosts = list_all_hosts(site_id, include_cloud=True)
        
        if not all_hosts.get("success"):
            result["error"] = "Failed to retrieve host data"
            return result
        
        # Search through all hosts
        identifier_lower = identifier.lower()
        matches = []
        
        for host in all_hosts.get("combined_data", []):
            # Check MAC address
            if host.get("mac", "").lower() == identifier_lower:
                matches.append({"match_type": "mac", "host": host})
                continue
            
            # Check hostname
            hostname = host.get("hostname") or ""
            if identifier_lower in hostname.lower():
                matches.append({"match_type": "hostname", "host": host})
                continue
                
            # Check name field
            name = host.get("name") or ""
            if identifier_lower in name.lower():
                matches.append({"match_type": "name", "host": host})
                continue
        
        result["success"] = True
        result["matches"] = matches
        result["match_count"] = len(matches)
        result["search_locations"] = all_hosts.get("methods_tried", [])
        
        return result
        
    except Exception as e:
        result["error"] = str(e)
        return result

# ========= Prompt playbooks =========
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

@mcp.prompt("how_to_check_system_status")
def how_to_check_system_status():
    return {
        "description": "Check overall UniFi system health and status.",
        "messages": [{
            "role": "system",
            "content": (
                "To check system status, use 'get_system_status' tool or 'status://system' resource. "
                "This provides comprehensive health info for all UniFi services including devices, "
                "clients, Access, and Protect components."
            )
        }]
    }

@mcp.prompt("how_to_monitor_devices")
def how_to_monitor_devices():
    return {
        "description": "Monitor device health and identify issues.",
        "messages": [{
            "role": "system", 
            "content": (
                "Use 'get_device_health' tool or 'status://devices' resource to get device health summary. "
                "This shows online/offline counts, device types, uptime stats, and highlights any offline devices."
            )
        }]
    }

@mcp.prompt("how_to_check_network_activity")
def how_to_check_network_activity():
    return {
        "description": "Check current network activity and client usage.",
        "messages": [{
            "role": "system",
            "content": (
                "Use 'get_client_activity' tool or 'status://clients' resource to see active clients, "
                "bandwidth usage, connection types (wired/wireless), and top bandwidth users."
            )
        }]
    }

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

@mcp.prompt("how_to_list_hosts")
def how_to_list_hosts():
    return {
        "description": "List all hosts using local and cloud APIs.",
        "messages": [{
            "role": "system",
            "content": (
                "Use 'working_list_hosts_example' for a complete working implementation, "
                "'list_hosts_api_format' for cloud API format, or 'list_hosts_fixed' for local API with proper site discovery. "
                "Run 'discover_sites' first if you need to find valid site IDs."
            )
        }]
    }

@mcp.prompt("how_to_debug_api_issues")
def how_to_debug_api_issues():
    return {
        "description": "Debug UniFi API connectivity and configuration issues.",
        "messages": [{
            "role": "system",
            "content": (
                "Use 'debug_api_connectivity' to test all API endpoints and get troubleshooting recommendations. "
                "Use 'discover_sites' to find correct site IDs. Check environment configuration with the debug results."
            )
        }]
    }

# ========= Entrypoint =========
if __name__ == "__main__":
    print("🚀 UniFi MCP – Integration + Legacy + Access + Protect (+ Site Manager stubs)")
    print(f"→ Controller: https://{UNIFI_HOST}:{UNIFI_PORT}  TLS verify={VERIFY_TLS}")
    if not UNIFI_API_KEY:
        print("⚠️ UNIFI_API_KEY not set — Integration/Access/Protect key-based calls may fail.")
    
    # Show discovered sites on startup
    sites = get_correct_site_ids()
    if sites:
        print(f"📍 Discovered sites: {', '.join(sites)}")
    else:
        print("⚠️ No sites discovered - check API credentials")
    
    mcp.run(transport="stdio")
