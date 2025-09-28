## working config

# main.py
# UniFi MCP Server - Clean Cloud-Focused Implementation
# Streamlined for working cloud APIs only

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import os, json, requests, urllib3
from pathlib import Path
from mcp.server.fastmcp import FastMCP

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ========= Load Environment Variables =========
def load_env_file(env_file: str = "secrets.env"):
    """Load environment variables from a .env file"""
    env_path = Path(env_file)
    if env_path.exists():
        print(f"Loading environment from: {env_path.absolute()}")
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"\'')
                    if key not in os.environ:
                        os.environ[key] = value

load_env_file()

# ========= Configuration =========
UNIFI_API_KEY   = os.getenv("UNIFI_API_KEY", "API")
UNIFI_HOST      = os.getenv("UNIFI_GATEWAY_HOST", "HOST")
UNIFI_PORT      = os.getenv("UNIFI_GATEWAY_PORT", "443")
VERIFY_TLS      = os.getenv("UNIFI_VERIFY_TLS", "false").lower() in ("1", "true", "yes")
SM_TOKEN        = os.getenv("UNIFI_SITEMGR_TOKEN", "")

REQUEST_TIMEOUT_S = 10

# Base URLs
NET_INTEGRATION_BASE = f"https://{UNIFI_HOST}:{UNIFI_PORT}/proxy/network/integrations/v1"

# Initialize MCP server
mcp = FastMCP("unifi-cloud")

# ========= HTTP helpers =========
def _h_key() -> Dict[str, str]:
    return {"X-API-Key": UNIFI_API_KEY, "Content-Type": "application/json"}

# ========= Cloud API Functions =========
def list_hosts_cloud():
    """List hosts using UniFi Site Manager (cloud) API"""
    if not SM_TOKEN:
        return {"error": "UNIFI_SITEMGR_TOKEN not configured"}
    
    try:
        url = "https://api.ui.com/v1/hosts"
        headers = {'Accept': 'application/json', 'X-API-Key': SM_TOKEN}
        response = requests.get(url, headers=headers, verify=False, timeout=REQUEST_TIMEOUT_S)
        
        if response.status_code == 200:
            return {"success": True, "data": response.json().get("data", [])}
        else:
            return {"error": f"HTTP {response.status_code}: {response.text[:500]}"}
    except Exception as e:
        return {"error": str(e)}

def get_devices_cloud():
    """Get devices using Site Manager API"""
    if not SM_TOKEN:
        return {"error": "UNIFI_SITEMGR_TOKEN not configured"}
    
    try:
        url = "https://api.ui.com/v1/devices"
        headers = {'Accept': 'application/json', 'X-API-Key': SM_TOKEN}
        response = requests.get(url, headers=headers, verify=False, timeout=REQUEST_TIMEOUT_S)
        
        if response.status_code == 200:
            return {"success": True, "data": response.json().get("data", [])}
        else:
            return {"error": f"HTTP {response.status_code}: {response.text[:500]}"}
    except Exception as e:
        return {"error": str(e)}

def get_sites_cloud():
    """Get sites using Site Manager API"""
    if not SM_TOKEN:
        return {"error": "UNIFI_SITEMGR_TOKEN not configured"}
    
    try:
        url = "https://api.ui.com/v1/sites"
        headers = {'Accept': 'application/json', 'X-API-Key': SM_TOKEN}
        response = requests.get(url, headers=headers, verify=False, timeout=REQUEST_TIMEOUT_S)
        
        if response.status_code == 200:
            return {"success": True, "data": response.json().get("data", [])}
        else:
            return {"error": f"HTTP {response.status_code}: {response.text[:500]}"}
    except Exception as e:
        return {"error": str(e)}

def get_isp_metrics_cloud(metric_type: str = "5m", time_range: str = "24h"):
    """Get ISP metrics using Site Manager API"""
    if not SM_TOKEN:
        return {"error": "UNIFI_SITEMGR_TOKEN not configured"}
    
    try:
        url = f"https://api.ui.com/ea/isp-metrics/{metric_type}"
        headers = {'Accept': 'application/json', 'X-API-Key': SM_TOKEN}
        params = {"timeRange": time_range} if time_range else {}
        
        response = requests.get(url, headers=headers, params=params, verify=False, timeout=REQUEST_TIMEOUT_S)
        
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {"error": f"HTTP {response.status_code}: {response.text[:500]}"}
    except Exception as e:
        return {"error": str(e)}

def query_isp_metrics_cloud(metric_type: str = "5m", sites_data: list = None, time_range: str = "24h"):
    """Query ISP metrics using POST method with specific sites/hosts"""
    if not SM_TOKEN:
        return {"error": "UNIFI_SITEMGR_TOKEN not configured"}
    
    if not sites_data:
        # Auto-build from current host and sites
        try:
            # Get both host and site information
            hosts = list_hosts_cloud()
            sites = get_sites_cloud()
            
            if not hosts.get("success") or not hosts.get("data"):
                return {"error": "Could not get host data for query"}
            
            host_id = hosts["data"][0]["id"]
            end_time = datetime.now()
            
            if time_range == "24h":
                begin_time = end_time - timedelta(hours=24)
            elif time_range == "7d":
                begin_time = end_time - timedelta(days=7)
            elif time_range == "30d":
                begin_time = end_time - timedelta(days=30)
            else:
                begin_time = end_time - timedelta(hours=24)
            
            # Format timestamps in different ways
            iso_begin = begin_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
            iso_end = end_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
            
            # Try with actual site IDs if available
            site_attempts = []
            if sites.get("success") and sites.get("data"):
                for site in sites["data"]:
                    site_id = site.get("id")
                    if site_id:
                        site_attempts.append({
                            "beginTimestamp": iso_begin,
                            "siteId": site_id,
                            "endTimestamp": iso_end
                        })
            
            # Also try with host ID in different formats
            site_attempts.extend([
                # Host ID format
                {
                    "beginTimestamp": iso_begin,
                    "hostId": host_id,
                    "endTimestamp": iso_end
                },
                # Minimal format with just timestamps
                {
                    "beginTimestamp": iso_begin,
                    "endTimestamp": iso_end
                },
                # Different timestamp format (RFC3339)
                {
                    "beginTimestamp": begin_time.isoformat() + "Z",
                    "hostId": host_id,
                    "endTimestamp": end_time.isoformat() + "Z"
                },
                # Unix timestamp format
                {
                    "beginTimestamp": int(begin_time.timestamp()),
                    "hostId": host_id,
                    "endTimestamp": int(end_time.timestamp())
                }
            ])
            
            sites_data = site_attempts
            
        except Exception as e:
            return {"error": f"Failed to build query: {str(e)}"}
    
    try:
        url = f"https://api.ui.com/ea/isp-metrics/{metric_type}/query"
        headers = {
            'Accept': 'application/json', 
            'X-API-Key': SM_TOKEN, 
            'Content-Type': 'application/json'
        }
        
        # Try each site/format combination
        for i, site_data in enumerate(sites_data):
            payload = {"sites": [site_data]}
            
            debug_info = {
                "url": url,
                "attempt": i + 1,
                "total_attempts": len(sites_data),
                "payload": payload,
                "metric_type": metric_type,
                "time_range": time_range
            }
            
            response = requests.post(url, headers=headers, json=payload, verify=False, timeout=REQUEST_TIMEOUT_S)
            
            if response.status_code == 200:
                return {
                    "success": True, 
                    "data": response.json(), 
                    "debug": debug_info,
                    "working_format": site_data
                }
            elif response.status_code == 401:
                return {
                    "error": "Authentication failed - check API key permissions",
                    "debug": debug_info
                }
            elif response.status_code != 400:
                # Non-parameter error might be more informative
                return {
                    "error": f"HTTP {response.status_code}: {response.text[:500]}",
                    "debug": debug_info,
                    "note": f"Failed on attempt {i+1}, different error than parameter_invalid"
                }
        
        # If all attempts failed with 400 errors
        return {
            "error": f"All {len(sites_data)} format attempts failed with parameter_invalid",
            "debug": {
                "total_attempts": len(sites_data),
                "sample_payloads": sites_data[:3],  # Show first 3 attempts
                "last_response": response.text[:200] if 'response' in locals() else None
            },
            "suggestion": "POST query endpoint may require specific permissions or different API specification"
        }
        
    except Exception as e:
        return {"error": str(e), "debug": debug_info if 'debug_info' in locals() else None}

# ========= Basic Health Check =========
def _health_check() -> Dict[str, Any]:
    """Basic controller health check"""
    try:
        response = requests.get(f"{NET_INTEGRATION_BASE}/sites", headers=_h_key(), verify=False, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {"ok": True, "sites_count": data.get("count", 0)}
        else:
            return {"ok": False, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ========= Tools =========
@mcp.tool()
def get_console_info():
    """Get your UniFi console information"""
    return list_hosts_cloud()

@mcp.tool()
def get_all_devices():
    """Get all your UniFi devices"""
    return get_devices_cloud()

@mcp.tool()
def get_all_sites():
    """Get all your UniFi sites"""
    return get_sites_cloud()

@mcp.tool()
def get_isp_performance():
    """Get recent ISP performance metrics"""
    return get_isp_metrics_cloud("5m", "24h")

@mcp.tool()
def get_isp_metrics_hourly():
    """Get hourly ISP metrics for the last 7 days"""
    return get_isp_metrics_cloud("1h", "7d")

@mcp.tool()
def get_isp_metrics_custom(metric_type: str = "5m", time_range: str = "24h"):
    """Get ISP metrics with custom parameters
    metric_type: '5m' or '1h'
    time_range: '24h', '7d', or '30d'
    """
    return get_isp_metrics_cloud(metric_type, time_range)

@mcp.tool()
def query_isp_metrics(metric_type: str = "5m", time_range: str = "24h"):
    """Query ISP metrics using POST method for your specific network
    metric_type: '5m' or '1h'
    time_range: '24h', '7d', or '30d'
    """
    return query_isp_metrics_cloud(metric_type, None, time_range)

@mcp.tool()
def test_isp_query_minimal():
    """Test ISP query with minimal payload to identify required fields"""
    if not SM_TOKEN:
        return {"error": "UNIFI_SITEMGR_TOKEN not configured"}
    
    try:
        url = "https://api.ui.com/ea/isp-metrics/5m/query"
        headers = {
            'Accept': 'application/json', 
            'X-API-Key': SM_TOKEN, 
            'Content-Type': 'application/json'
        }
        
        # Try the absolute minimum payload
        minimal_payloads = [
            # Empty sites array
            {"sites": []},
            # Just empty object
            {},
            # Single field tests to see what's accepted
            {"timeRange": "24h"},
            {"metricType": "5m"},
            # Different timestamp formats
            {
                "sites": [{
                    "beginTimestamp": "2025-09-26T00:00:00Z",
                    "endTimestamp": "2025-09-27T00:00:00Z"
                }]
            }
        ]
        
        results = []
        for i, payload in enumerate(minimal_payloads):
            response = requests.post(url, headers=headers, json=payload, verify=False, timeout=10)
            
            result = {
                "attempt": i + 1,
                "payload": payload,
                "status_code": response.status_code,
                "response": response.text[:300]
            }
            
            # If we get a different error, that might be progress
            if response.status_code != 400:
                result["note"] = "Different status code - might indicate progress"
            elif "parameter_invalid" not in response.text:
                result["note"] = "Different error message - might indicate progress"
            
            results.append(result)
        
        return {
            "test_results": results,
            "summary": f"Tested {len(minimal_payloads)} minimal payloads",
            "note": "Looking for different error responses that might indicate correct format"
        }
        
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def check_local_controller():
    """Check local controller status"""
    return _health_check()

@mcp.tool()
def get_network_overview():
    """Get complete network overview"""
    result = {
        "timestamp": datetime.now().isoformat(),
        "console": list_hosts_cloud(),
        "devices": get_devices_cloud(),
        "sites": get_sites_cloud(),
        "local_controller": _health_check()
    }
    return result

# ========= Resources =========
@mcp.resource("cloud://hosts")
async def cloud_hosts_resource():
    """Your UniFi console details from cloud API"""
    return list_hosts_cloud()

@mcp.resource("cloud://devices")
async def cloud_devices_resource():
    """All your UniFi devices from cloud API"""
    return get_devices_cloud()

@mcp.resource("cloud://sites")
async def cloud_sites_resource():
    """All your sites from cloud API"""
    return get_sites_cloud()

@mcp.resource("unifi://console")
async def console_resource():
    """Your UniFi console details"""
    return list_hosts_cloud()

@mcp.resource("unifi://devices")
async def devices_resource():
    """All your UniFi devices"""
    return get_devices_cloud()

@mcp.resource("unifi://sites")
async def sites_resource():
    """All your UniFi sites"""
    return get_sites_cloud()

@mcp.resource("unifi://isp-metrics")
async def isp_metrics_resource():
    """Recent ISP performance metrics"""
    return get_isp_metrics_cloud("5m", "24h")

@mcp.resource("unifi://isp-metrics-hourly")
async def isp_metrics_hourly_resource():
    """Hourly ISP metrics for last 7 days"""
    return get_isp_metrics_cloud("1h", "7d")

@mcp.resource("unifi://isp-query")
async def isp_query_resource():
    """ISP metrics using POST query method"""
    return query_isp_metrics_cloud("5m", None, "24h")

@mcp.resource("unifi://isp-query-weekly")
async def isp_query_weekly_resource():
    """ISP metrics for last 7 days using POST query"""
    return query_isp_metrics_cloud("1h", None, "7d")

@mcp.resource("unifi://network-status")
async def network_status_resource():
    """Complete network status"""
    return get_network_overview()

# ========= Main Entry Point =========
if __name__ == "__main__":
    print("UniFi MCP Server - Cloud Edition")
    print(f"Controller: https://{UNIFI_HOST}:{UNIFI_PORT}")
    print(f"Cloud API: {'Configured' if SM_TOKEN else 'Not configured'}")
    
    if SM_TOKEN:
        test = list_hosts_cloud()
        if test.get("success"):
            print(f"Cloud API working: {len(test.get('data', []))} hosts found")
        else:
            print(f"Cloud API error: {test.get('error')}")
    
    mcp.run()
