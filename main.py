# main.py
# UniFi MCP Server — cloud-only (unifi.ui.com), full UniFi Network API + Site Manager
# - Every call goes to https://api.ui.com with one API key; Network calls use the cloud connector
# - One tool per API operation, generated from the bundled OpenAPI specs (unifi_tools.py)
# - A few hand-written helpers on top: health, site status, search, describe_operation
# - UNIFI_READ_ONLY=true registers only the tools that never change anything

from typing import Annotated, Any, Dict, List, Optional
from datetime import datetime, timezone
from pathlib import Path
import json

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

import unifi_client as uc
from unifi_tools import FUNCTIONS, OPERATIONS

ROOT = Path(__file__).resolve().parent

mcp = FastMCP("unifi")

# ========= Generated API tools =========
def register_api_tools() -> int:
    count = 0
    for op in OPERATIONS:
        if uc.READ_ONLY and not op["read_only"]:
            continue
        mcp.add_tool(
            FUNCTIONS[op["name"]],
            name=op["name"],
            annotations=ToolAnnotations(
                title=op["summary"],
                readOnlyHint=op["read_only"],
                destructiveHint=op["destructive"],
                idempotentHint=op["idempotent"],
                openWorldHint=True,
            ),
        )
        count += 1
    return count

# ========= Schema lookup =========
_SPECS: Dict[str, Dict[str, Any]] = {}

def _spec(spec_file: str) -> Dict[str, Any]:
    if spec_file not in _SPECS:
        _SPECS[spec_file] = json.loads((ROOT / spec_file).read_text())
    return _SPECS[spec_file]

def _inline(spec: Dict[str, Any], node: Any, seen: tuple = (), depth: int = 0) -> Any:
    """Inline $refs so the caller sees one self-contained schema. Cycles and deep nesting stop at a stub."""
    if isinstance(node, list):
        return [_inline(spec, n, seen, depth) for n in node]
    if not isinstance(node, dict):
        return node
    if "$ref" in node:
        name = node["$ref"].split("/")[-1]
        if name in seen or depth > 12:
            return {"$ref": node["$ref"], "note": "see above"}
        return _inline(spec, spec["components"]["schemas"][name], seen + (name,), depth + 1)
    return {k: _inline(spec, v, seen, depth) for k, v in node.items()}

def _op(tool_name: str) -> Dict[str, Any]:
    op = next((o for o in OPERATIONS if o["name"] == tool_name), None)
    if op is None:
        raise uc.UniFiHTTPError(f"Unknown tool {tool_name!r}. Call list_operations to see them all.")
    return op

# ========= Helper tools =========
@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True))
def unifi_health() -> Dict[str, Any]:
    """Check the API key, the console, the Network application and the default site."""
    out: Dict[str, Any] = {"cloud_base": uc.CLOUD_BASE, "read_only": uc.READ_ONLY}
    try:
        out["consoles"] = uc.list_consoles()
        out["console_id"] = uc.console_id()
        out["network_application"] = uc.network_call("GET", "/v1/info")
        out["default_site_id"] = uc.default_site_id()
        out["ok"] = True
    except Exception as e:
        out["ok"] = False
        out["error"] = str(e)
    return out

@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True))
def get_site_status(
    site_id: Annotated[Optional[str], Field(description="Site ID. Leave empty to use the default site.")] = None,
) -> Dict[str, Any]:
    """One-call overview of a site: device states, offline devices, pending firmware, clients by type."""
    devices = uc.paginate("/v1/sites/{siteId}/devices", site_id)
    clients = uc.paginate("/v1/sites/{siteId}/clients", site_id)
    by_state: Dict[str, int] = {}
    for d in devices:
        by_state[d.get("state", "UNKNOWN")] = by_state.get(d.get("state", "UNKNOWN"), 0) + 1
    by_type: Dict[str, int] = {}
    for c in clients:
        by_type[c.get("type", "UNKNOWN")] = by_type.get(c.get("type", "UNKNOWN"), 0) + 1
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "site_id": site_id or uc.default_site_id(),
        "devices": {
            "total": len(devices),
            "by_state": by_state,
            "not_online": [{"name": d.get("name"), "model": d.get("model"), "state": d.get("state")}
                           for d in devices if d.get("state") != "ONLINE"],
            "firmware_updatable": [{"name": d.get("name"), "firmwareVersion": d.get("firmwareVersion")}
                                   for d in devices if d.get("firmwareUpdatable")],
        },
        "clients": {"total": len(clients), "by_type": by_type},
    }

@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True))
def search_site(
    query: Annotated[str, Field(description="Part of a name, MAC address or IP address.")],
    site_id: Annotated[Optional[str], Field(description="Site ID. Leave empty to use the default site.")] = None,
) -> Dict[str, Any]:
    """Find connected clients and adopted devices whose name, MAC or IP contains the query."""
    q = query.lower()
    def hit(item: Dict[str, Any]) -> bool:
        return any(q in str(item.get(k) or "").lower() for k in ("name", "macAddress", "ipAddress"))
    return {
        "devices": [d for d in uc.paginate("/v1/sites/{siteId}/devices", site_id) if hit(d)],
        "clients": [c for c in uc.paginate("/v1/sites/{siteId}/clients", site_id) if hit(c)],
    }

@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=False))
def list_operations(
    tag: Annotated[Optional[str], Field(description="Only this API group, e.g. Firewall, Clients, WiFi Broadcasts.")] = None,
) -> List[Dict[str, Any]]:
    """Every API operation this server covers, with its tool name, method, path and whether it changes anything."""
    return [
        {k: op[k] for k in ("name", "api", "tag", "method", "path", "summary", "read_only", "destructive")}
        | {"registered": op["read_only"] or not uc.READ_ONLY}
        for op in OPERATIONS
        if tag is None or op["tag"].lower() == tag.lower()
    ]

@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=False))
def describe_operation(
    tool_name: Annotated[str, Field(description="Name of an API tool, e.g. create_firewall_policy.")],
) -> Dict[str, Any]:
    """Full request-body JSON schema of an API tool, with references inlined. Use before create/update calls."""
    op = _op(tool_name)
    spec = _spec(op["spec"])
    method = spec["paths"][op["path"]][op["method"].lower()]
    body = (method.get("requestBody") or {}).get("content", {}).get("application/json", {}).get("schema")
    return {
        **{k: op[k] for k in ("name", "method", "path", "summary", "operation_id", "read_only", "destructive")},
        "parameters": method.get("parameters", []),
        "request_body_schema": _inline(spec, body) if body else None,
    }

# ========= Resources =========
@mcp.resource("unifi://health")
def health_resource() -> Dict[str, Any]:
    return unifi_health()

@mcp.resource("unifi://sites/{site_id}/devices")
def devices_resource(site_id: str) -> List[Dict[str, Any]]:
    return uc.paginate("/v1/sites/{siteId}/devices", site_id)

@mcp.resource("unifi://sites/{site_id}/clients")
def clients_resource(site_id: str) -> List[Dict[str, Any]]:
    return uc.paginate("/v1/sites/{siteId}/clients", site_id)

# ========= Prompt playbooks =========
@mcp.prompt("check_unifi_health")
def check_unifi_health() -> str:
    return ("Call unifi_health to confirm the API key, console and Network application. "
            "Then call get_site_status and summarize offline devices, pending firmware and client counts.")

@mcp.prompt("restart_device")
def restart_device() -> str:
    return ("Use search_site to find the device, confirm the exact device with the user, then call "
            "execute_adopted_device_action with body {\"action\": \"RESTART\"}.")

@mcp.prompt("change_firewall_safely")
def change_firewall_safely() -> str:
    return ("Call list_firewall_zones and list_firewall_policies first. Before creating or updating a policy, call "
            "describe_operation for that tool to get the exact body schema. Show the user the planned JSON and get a "
            "yes before calling create_firewall_policy, update_firewall_policy or patch_firewall_policy. "
            "Use get_user_defined_firewall_policy_ordering to check where a new policy lands.")

@mcp.prompt("guest_access")
def guest_access() -> str:
    return ("Find the guest with list_connected_clients (filter by name or macAddress), then call "
            "execute_client_action with {\"action\": \"AUTHORIZE_GUEST_ACCESS\", \"timeLimitMinutes\": 60}. "
            "For many guests, generate_vouchers is usually the better fit.")

# ========= Entrypoint =========
api_tool_count = register_api_tools()

if __name__ == "__main__":
    uc.log(f"UniFi MCP (cloud) -> {uc.CLOUD_BASE}; {api_tool_count} API tools"
           + (" (read-only mode)" if uc.READ_ONLY else ""))
    if not uc.UNIFI_API_KEY:
        uc.log("UNIFI_API_KEY is not set; every call will fail until it is.")
    mcp.run(transport="stdio")
