from typing import Any, List, Dict, Optional
import os
from mcp.server.fastmcp import FastMCP
import requests

# Configuration
UNIFI_API_KEY = os.getenv("UNIFI_API_KEY", "CHANGEME")
UNIFI_GATEWAY_HOST = os.getenv("UNIFI_GATEWAY_HOST", "192.168.1.1")
UNIFI_GATEWAY_PORT = os.getenv("UNIFI_GATEWAY_PORT", "443")
UNIFI_GATEWAY_BASE_URL = f"https://{UNIFI_GATEWAY_HOST}:{UNIFI_GATEWAY_PORT}/proxy/network/integration"

# Initialize FastMCP server
mcp = FastMCP("unifi")

def unifi_request(path: str, method: str, params: Optional[Dict[str, Any]] = None, data: Optional[Dict[str, Any]] = None):
    """
    Make a request to the Unifi API

    Args:
        path (str): The path to the API endpoint
        method (str): The HTTP method to use
        data (Optional[Dict[str, Any]], optional): The data to send to the API. Defaults to None.

    Returns:
        dict: The response JSON from the API
    """
    url = f"{UNIFI_GATEWAY_BASE_URL}/{path}"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": UNIFI_API_KEY,
    }
    response = requests.request(method, url, headers=headers, params=params, data=data, verify=False)
    return response.json()

@mcp.resource("sites://")
async def list_sites() -> List[Dict[str, Any]]:
    """List all sites in the Unifi controller"""
    sites = []
    params = {"limit": 200, "offset": 0}

    while True:
        resp = unifi_request("/v1/sites", "GET", params=params)
        sites.extend(resp["data"])
        if resp["count"] != resp["limit"] or resp["totalCount"] <= len(sites):
            break
        params["offset"] += resp["limit"]

    return sites

@mcp.resource("sites://{site_id}/devices")
async def list_devices(site_id: str) -> List[Dict[str, Any]]:
    """
    List all devices in a specific Unifi site
    
    Args:
        site_id (str): The ID of the site to list devices for
        
    Returns:
        List[Dict[str, Any]]: List of devices in the site
    """
    devices = []
    params = {"limit": 200, "offset": 0, "site_id": site_id}
    
    while True:
        resp = unifi_request(f"/v1/sites/{site_id}/devices", "GET", params=params)
        devices.extend(resp["data"])
        if resp["count"] != resp["limit"] or resp["totalCount"] <= len(devices):
            break
        params["offset"] += resp["limit"]
    
    return devices

@mcp.resource("sites://{site_id}/devices/{device_id}")
async def get_device_details(site_id: str, device_id: str) -> Dict[str, Any]:
    """
    Get details for a specific device in a Unifi site
    
    Args:
        site_id (str): The ID of the site the device belongs to
        device_id (str): The ID of the device to get details for
        
    Returns:
        Dict[str, Any]: Device details
    """
    return unifi_request(f"/v1/sites/{site_id}/devices/{device_id}", "GET")

@mcp.resource("sites://{site_id}/devices/{device_id}/statistics")
async def get_device_statistics(site_id: str, device_id: str) -> Dict[str, Any]:
    """
    Get the latest statistics for a specific device in a Unifi site
    
    Args:
        site_id (str): The ID of the site the device belongs to
        device_id (str): The ID of the device to get statistics for
        
    Returns:
        Dict[str, Any]: Device statistics including CPU and memory usage
    """
    return unifi_request(f"/v1/sites/{site_id}/devices/{device_id}/statistics/latest", "GET")

@mcp.resource("sites://{site_id}/clients")
async def list_clients(site_id: str) -> List[Dict[str, Any]]:
    """
    List all connected clients in a specific Unifi site.
    Clients can be physical devices (computers, smartphones) or active VPN connections.
    
    Args:
        site_id (str): The ID of the site to list clients for
        
    Returns:
        List[Dict[str, Any]]: List of connected clients in the site
    """
    clients = []
    params = {"limit": 200, "offset": 0}
    
    while True:
        resp = unifi_request(f"/v1/sites/{site_id}/clients", "GET", params=params)
        clients.extend(resp["data"])
        if resp["count"] != resp["limit"] or resp["totalCount"] <= len(clients):
            break
        params["offset"] += resp["limit"]
    
    return clients

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
