# unifi_client.py
# Cloud-only HTTP client for the UniFi APIs.
# - Every request goes to https://api.ui.com with one X-API-KEY
# - Site Manager calls hit api.ui.com directly
# - Network calls go through the Site Manager cloud connector:
#   /v1/connector/consoles/{consoleId}/proxy/network/integration/v1/...
# - Console and default site are auto-discovered unless pinned in the environment

from typing import Any, Dict, List, Optional
from pathlib import Path
from urllib.parse import quote
import os, sys, re, requests

# ========= Load Environment Variables from secrets.env =========
def log(msg: str) -> None:
    # stdout is the MCP stdio channel, so all logging goes to stderr
    print(msg, file=sys.stderr)

def load_env_file(env_file: Path = Path(__file__).resolve().parent / "secrets.env") -> None:
    """Load KEY=VALUE lines from secrets.env next to this file. Real env vars win."""
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = (part.strip() for part in line.split("=", 1))
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        os.environ.setdefault(key, value)

load_env_file()

# ========= Configuration =========
CLOUD_BASE        = "https://api.ui.com"
UNIFI_API_KEY     = os.getenv("UNIFI_API_KEY", "")
UNIFI_CONSOLE_ID  = os.getenv("UNIFI_CONSOLE_ID", "").strip()
UNIFI_SITE_ID     = os.getenv("UNIFI_SITE_ID", "").strip()
READ_ONLY         = os.getenv("UNIFI_READ_ONLY", "false").lower() in ("1", "true", "yes")
REQUEST_TIMEOUT_S = int(os.getenv("UNIFI_TIMEOUT_S", "30"))

NETWORK_PREFIX = "/proxy/network/integration"

class UniFiHTTPError(RuntimeError):
    pass

# ========= HTTP =========
SESSION = requests.Session()

_PLACEHOLDER = re.compile(r"\{([^}]+)\}")

def _segment(name: str, value: Any) -> str:
    """Encode one path parameter. Rejects values that could walk the proxied path."""
    if value is None or str(value) == "":
        raise UniFiHTTPError(f"Missing path parameter: {name}")
    text = str(value)
    if text in (".", "..") or "/" in text or "\\" in text:
        raise UniFiHTTPError(f"Invalid value for path parameter {name}: {text!r}")
    return quote(text, safe=":")

def build_path(template: str, path_params: Dict[str, Any]) -> str:
    return _PLACEHOLDER.sub(lambda m: _segment(m.group(1), path_params.get(m.group(1))), template)

def _request(method: str, url: str, params: Optional[Dict[str, Any]] = None, body: Any = None) -> Any:
    if not UNIFI_API_KEY:
        raise UniFiHTTPError("UNIFI_API_KEY is not set. Create one at unifi.ui.com and put it in secrets.env.")
    if not url.startswith(CLOUD_BASE + "/"):
        raise UniFiHTTPError(f"Refusing request outside {CLOUD_BASE}: {url}")
    params = {k: v for k, v in (params or {}).items() if v is not None}
    r = SESSION.request(
        method,
        url,
        headers={"X-API-KEY": UNIFI_API_KEY, "Accept": "application/json"},
        params=params,
        json=body,
        timeout=REQUEST_TIMEOUT_S,
    )
    if r.status_code >= 400:
        raise UniFiHTTPError(f"{method} {r.url} -> {r.status_code} {r.reason}; body: {(r.text or '')[:800]}")
    if not r.text.strip():
        return {"ok": True, "status": r.status_code}
    try:
        return r.json()
    except ValueError:
        return {"ok": True, "status": r.status_code, "text": r.text[:2000]}

# ========= Site Manager (api.ui.com) =========
def cloud_call(method: str, path: str, path_params: Optional[Dict[str, Any]] = None,
               query: Optional[Dict[str, Any]] = None, body: Any = None, all_pages: bool = False) -> Any:
    url = CLOUD_BASE + build_path(path, path_params or {})
    resp = _request(method, url, query, body)
    if not all_pages or method != "GET":
        return resp
    # Site Manager pages with nextToken
    items: List[Any] = list(resp.get("data", []))
    params = dict(query or {})
    while resp.get("nextToken"):
        params["nextToken"] = resp["nextToken"]
        resp = _request(method, url, params)
        items.extend(resp.get("data", []))
    return {"data": items, "count": len(items)}

# ========= Console / site discovery =========
_console_id: Optional[str] = UNIFI_CONSOLE_ID or None
_site_id: Optional[str] = UNIFI_SITE_ID or None

def list_consoles() -> List[Dict[str, Any]]:
    hosts = cloud_call("GET", "/v1/hosts", all_pages=True).get("data", [])
    out = []
    for h in hosts:
        state = h.get("reportedState") or {}
        out.append({
            "id": h.get("id"),
            "name": state.get("name") or state.get("hostname"),
            "type": h.get("type"),
            "model": (state.get("hardware") or {}).get("shortname"),
            "state": state.get("state"),
        })
    return out

def console_id() -> str:
    """UNIFI_CONSOLE_ID, or the only console on the account."""
    global _console_id
    if _console_id:
        return _console_id
    consoles = [c for c in list_consoles() if c["type"] == "console"]
    if len(consoles) == 1:
        _console_id = consoles[0]["id"]
        return _console_id
    if not consoles:
        raise UniFiHTTPError("No consoles on this UniFi account. Check that the API key belongs to the "
                             "account that owns the console and that remote management is on.")
    raise UniFiHTTPError("Several consoles found; set UNIFI_CONSOLE_ID to one of: "
                         + ", ".join(f"{c['name']} = {c['id']}" for c in consoles))

def network_base() -> str:
    return f"{CLOUD_BASE}/v1/connector/consoles/{_segment('consoleId', console_id())}{NETWORK_PREFIX}"

def default_site_id() -> str:
    """UNIFI_SITE_ID, the only site, or the site whose internalReference is 'default'."""
    global _site_id
    if _site_id:
        return _site_id
    sites = _request("GET", f"{network_base()}/v1/sites", {"limit": 200}).get("data", [])
    if len(sites) == 1:
        _site_id = sites[0]["id"]
    else:
        match = [s for s in sites if s.get("internalReference") == "default"]
        if not match:
            raise UniFiHTTPError("Several sites found; pass site_id or set UNIFI_SITE_ID to one of: "
                                 + ", ".join(f"{s.get('name')} = {s.get('id')}" for s in sites))
        _site_id = match[0]["id"]
    return _site_id

# ========= Network API (through the cloud connector) =========
def network_call(method: str, path: str, path_params: Optional[Dict[str, Any]] = None,
                 query: Optional[Dict[str, Any]] = None, body: Any = None, all_pages: bool = False) -> Any:
    path_params = dict(path_params or {})
    if "{siteId}" in path and not path_params.get("siteId"):
        path_params["siteId"] = default_site_id()
    url = network_base() + build_path(path, path_params)
    resp = _request(method, url, query, body)
    if not all_pages or method != "GET" or not isinstance(resp, dict) or "totalCount" not in resp:
        return resp
    # Network API pages with offset/limit/totalCount
    items: List[Any] = list(resp.get("data", []))
    params = dict(query or {})
    while len(items) < resp.get("totalCount", 0) and resp.get("count", 0) > 0:
        params["offset"] = (params.get("offset") or 0) + resp["count"]
        resp = _request(method, url, params)
        items.extend(resp.get("data", []))
    return {"offset": (query or {}).get("offset", 0), "count": len(items), "totalCount": len(items), "data": items}

def paginate(path: str, site_id: Optional[str] = None, filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """All items of a Network list endpoint."""
    resp = network_call("GET", path, {"siteId": site_id}, {"offset": 0, "limit": 200, "filter": filter}, all_pages=True)
    return resp.get("data", [])
