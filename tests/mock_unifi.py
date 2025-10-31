"""
Mock UniFi Controller for Integration Testing

Provides a mock HTTP server that simulates UniFi controller responses
for testing authentication, error handling, and API interactions.
"""

from typing import Dict, Any, Optional, Callable
import json
import time


class MockUniFiController:
    """
    Mock UniFi controller that tracks state and simulates API responses.
    """

    def __init__(self):
        self.sites = [
            {"id": "default", "name": "Default", "desc": "Default Site"}
        ]
        self.devices = [
            {"id": "device1", "mac": "aa:bb:cc:dd:ee:ff", "name": "Test AP", "model": "U6-Pro", "state": 1},
            {"id": "device2", "mac": "11:22:33:44:55:66", "name": "Test Switch", "model": "USW-24", "state": 1}
        ]
        self.clients = [
            {"mac": "aa:bb:cc:dd:ee:01", "hostname": "laptop", "ip": "192.168.1.100", "is_wired": False},
            {"mac": "aa:bb:cc:dd:ee:02", "hostname": "desktop", "ip": "192.168.1.101", "is_wired": True}
        ]
        self.wlans = [
            {"_id": "wlan1", "name": "Main WiFi", "enabled": True, "security": "wpapsk"},
            {"_id": "wlan2", "name": "Guest WiFi", "enabled": True, "security": "wpapsk"}
        ]

        # Auth state
        self.valid_api_keys = {"test_api_key_12345"}
        self.valid_credentials = {"admin": "password"}
        self.sessions = {}  # session_id -> {"username": str, "created_at": float}
        self.failed_login_attempts = 0

        # Request tracking for rate limiting tests
        self.request_count = 0
        self.requests_by_endpoint = {}

    def validate_api_key(self, api_key: str) -> bool:
        """Check if API key is valid."""
        return api_key in self.valid_api_keys

    def create_session(self, username: str) -> str:
        """Create a new session and return session ID."""
        session_id = f"session_{int(time.time())}_{username}"
        self.sessions[session_id] = {
            "username": username,
            "created_at": time.time()
        }
        return session_id

    def validate_session(self, session_id: str) -> bool:
        """Check if session is valid and not expired."""
        if session_id not in self.sessions:
            return False

        session = self.sessions[session_id]
        age = time.time() - session["created_at"]

        # Sessions expire after 1 hour in mock
        return age < 3600

    def authenticate(self, username: str, password: str) -> Optional[str]:
        """
        Authenticate user and return session ID if successful.
        """
        if username in self.valid_credentials and self.valid_credentials[username] == password:
            self.failed_login_attempts = 0
            return self.create_session(username)
        else:
            self.failed_login_attempts += 1
            return None

    def track_request(self, endpoint: str):
        """Track request for rate limiting tests."""
        self.request_count += 1
        if endpoint not in self.requests_by_endpoint:
            self.requests_by_endpoint[endpoint] = 0
        self.requests_by_endpoint[endpoint] += 1

    # API Response Builders

    def get_sites(self) -> Dict[str, Any]:
        """Return sites list."""
        return {
            "data": self.sites,
            "count": len(self.sites),
            "limit": 200,
            "offset": 0,
            "totalCount": len(self.sites)
        }

    def get_devices(self, site_id: str) -> Dict[str, Any]:
        """Return devices for a site."""
        return {
            "data": self.devices,
            "count": len(self.devices),
            "limit": 200,
            "offset": 0,
            "totalCount": len(self.devices)
        }

    def get_clients(self, site_id: str, active_only: bool = False) -> Dict[str, Any]:
        """Return clients for a site."""
        clients = self.clients
        if active_only:
            # Mock: first client is inactive
            clients = clients[1:]

        return {
            "data": clients,
            "count": len(clients),
            "limit": 200,
            "offset": 0,
            "totalCount": len(clients)
        }

    def get_wlans(self, site_id: str) -> Dict[str, Any]:
        """Return WLANs for a site."""
        return {
            "data": self.wlans
        }

    def block_client(self, mac: str) -> Dict[str, Any]:
        """Block a client."""
        # Find client
        client = next((c for c in self.clients if c["mac"] == mac), None)
        if not client:
            return {"error": "Client not found", "status_code": 404}

        client["blocked"] = True
        return {"success": True, "mac": mac}

    def unblock_client(self, mac: str) -> Dict[str, Any]:
        """Unblock a client."""
        client = next((c for c in self.clients if c["mac"] == mac), None)
        if not client:
            return {"error": "Client not found", "status_code": 404}

        client["blocked"] = False
        return {"success": True, "mac": mac}

    def kick_client(self, mac: str) -> Dict[str, Any]:
        """Kick (disconnect) a client."""
        client = next((c for c in self.clients if c["mac"] == mac), None)
        if not client:
            return {"error": "Client not found", "status_code": 404}

        return {"success": True, "mac": mac}

    def locate_device(self, device_id: str, duration: int) -> Dict[str, Any]:
        """Locate (blink LEDs on) a device."""
        device = next((d for d in self.devices if d["id"] == device_id), None)
        if not device:
            return {"error": "Device not found", "status_code": 404}

        return {"success": True, "device_id": device_id, "duration": duration}

    def set_wlan_enabled(self, wlan_id: str, enabled: bool) -> Dict[str, Any]:
        """Enable/disable a WLAN."""
        wlan = next((w for w in self.wlans if w["_id"] == wlan_id), None)
        if not wlan:
            return {"error": "WLAN not found", "status_code": 404}

        wlan["enabled"] = enabled
        return {"success": True, "wlan_id": wlan_id, "enabled": enabled}

    def get_stats(self) -> Dict[str, Any]:
        """Get mock controller stats."""
        return {
            "total_requests": self.request_count,
            "requests_by_endpoint": self.requests_by_endpoint,
            "active_sessions": len(self.sessions),
            "failed_login_attempts": self.failed_login_attempts
        }


def create_mock_responses(mock_controller: MockUniFiController) -> Dict[str, Callable]:
    """
    Create a dict of URL patterns -> response functions for use with responses library.

    Returns dict of {pattern: handler_function}
    """
    import re

    def sites_handler(request):
        """Handle GET /proxy/network/integrations/v1/sites"""
        # Check API key auth
        api_key = request.headers.get("X-API-Key")
        if not mock_controller.validate_api_key(api_key):
            return (401, {}, json.dumps({"error": "Unauthorized"}))

        mock_controller.track_request("/sites")
        return (200, {}, json.dumps(mock_controller.get_sites()))

    def devices_handler(request):
        """Handle GET /proxy/network/integrations/v1/sites/{site}/devices"""
        api_key = request.headers.get("X-API-Key")
        if not mock_controller.validate_api_key(api_key):
            return (401, {}, json.dumps({"error": "Unauthorized"}))

        # Extract site_id from URL
        match = re.search(r'/sites/([^/]+)/devices', request.url)
        site_id = match.group(1) if match else "default"

        mock_controller.track_request("/devices")
        return (200, {}, json.dumps(mock_controller.get_devices(site_id)))

    def clients_handler(request):
        """Handle GET /proxy/network/integrations/v1/sites/{site}/clients"""
        api_key = request.headers.get("X-API-Key")
        if not mock_controller.validate_api_key(api_key):
            return (401, {}, json.dumps({"error": "Unauthorized"}))

        active_only = "/active" in request.url
        mock_controller.track_request("/clients")
        return (200, {}, json.dumps(mock_controller.get_clients("default", active_only)))

    def login_handler(request):
        """Handle POST /api/auth/login"""
        try:
            data = json.loads(request.body)
            username = data.get("username")
            password = data.get("password")

            session_id = mock_controller.authenticate(username, password)
            if session_id:
                mock_controller.track_request("/login")
                # Return session cookie
                return (200, {"Set-Cookie": f"session={session_id}"}, json.dumps({"success": True}))
            else:
                return (401, {}, json.dumps({"error": "Invalid credentials"}))
        except Exception as e:
            return (400, {}, json.dumps({"error": str(e)}))

    def block_client_handler(request):
        """Handle POST /proxy/network/integrations/v1/sites/{site}/clients/block"""
        api_key = request.headers.get("X-API-Key")
        if not mock_controller.validate_api_key(api_key):
            return (401, {}, json.dumps({"error": "Unauthorized"}))

        try:
            data = json.loads(request.body)
            mac = data.get("mac")
            result = mock_controller.block_client(mac)

            if "error" in result:
                return (result.get("status_code", 400), {}, json.dumps(result))

            mock_controller.track_request("/block_client")
            return (200, {}, json.dumps(result))
        except Exception as e:
            return (400, {}, json.dumps({"error": str(e)}))

    return {
        "sites": sites_handler,
        "devices": devices_handler,
        "clients": clients_handler,
        "login": login_handler,
        "block_client": block_client_handler
    }
