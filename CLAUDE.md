# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **MCP (Model Context Protocol) Server** that integrates UniFi network equipment with AI assistants. It exposes UniFi Network, Access, and Protect APIs as MCP resources (read-only), tools (safe write operations), and prompts (usage guidance).

**Tech Stack:**
- Python 3.12
- FastMCP framework (mcp[cli] v1.14.1)
- httpx and requests for HTTP
- uv package manager
- Single-file implementation (main.py)

## Development Commands

**Setup:**
```bash
uv venv                    # Create virtual environment
uv pip install -e .        # Install dependencies in editable mode
```

**Run Server:**
```bash
python main.py             # Runs MCP server on stdio
```

**Configuration:**
Create `secrets.env` file (not tracked in git) with:
```bash
UNIFI_API_KEY=your_api_key
UNIFI_GATEWAY_HOST=192.168.1.1
UNIFI_GATEWAY_PORT=443
UNIFI_VERIFY_TLS=false
UNIFI_USERNAME=admin       # Legacy fallback only
UNIFI_PASSWORD=password    # Legacy fallback only
UNIFI_TIMEOUT_S=15
```

**Note:** `secreds.ev` is a template file (has a typo in filename). Actual secrets go in `secrets.env`.

## Architecture

### Three-Tier MCP Structure

1. **Resources** (read-only data access):
   - URI format: `sites://{site_id}/{resource_type}`
   - Examples: `sites://`, `sites://default/devices`, `access://doors`, `protect://cameras`
   - Registered in `@mcp.resource()` decorators

2. **Tools** (safe write operations):
   - Function format: `@mcp.tool()` decorated functions
   - Examples: `block_client()`, `locate_device()`, `access_unlock_door()`
   - All return structured JSON responses

3. **Prompts** (AI guidance):
   - URI format: descriptive names like `how_to_find_device`
   - Provide step-by-step workflows for common tasks
   - Registered in `@mcp.prompt()` decorators

### Authentication Strategy

**Dual-mode authentication:**
- **Primary:** API key via `X-API-Key` header (Integration API)
- **Fallback:** Cookie-based auth with username/password (Legacy API)

**Why dual-mode?**
- Some endpoints (WLANs, firewall rules) not yet in Integration API
- Protect API may need cookie auth depending on version
- Server tries API key first, falls back to cookies automatically

### API Coverage

**UniFi Network Integration API:**
- Sites, devices, clients, networks, port profiles, port forwards
- Primary interface, uses API key authentication

**UniFi Network Legacy API:**
- WLANs, firewall rules (not yet in Integration API)
- Uses cookie authentication, URL format: `/proxy/network/api/s/{site}/...`

**UniFi Access API:**
- Doors, readers, users, access control
- Uses API key authentication

**UniFi Protect API:**
- Cameras, NVR status, events
- May use cookie auth (version-dependent)

**UniFi Site Manager:**
- Stub implementation for cloud API (not fully functional)

### Key Implementation Patterns

**URL Building:**
Always use `"/".join([base, path, components])` to avoid line-wrap issues with long URLs.

**Pagination:**
```python
await paginate_integration(session, url, params)
```
Automatically fetches all pages (200 items per page) until complete.

**Health Checks:**
Registered three ways for compatibility:
- `unifi://health`
- `health://unifi`
- `status://unifi`

**Debug Tool:**
```python
debug_registry()  # Lists all registered resources, tools, prompts
```

**Safe Dual-Auth Requests:**
```python
# Try API key first
headers = {"X-API-Key": api_key}
response = await session.get(url, headers=headers)

if response.status_code == 401:
    # Fallback to cookie auth
    await legacy_login(session)
    response = await session.get(url)
```

## Code Structure (main.py)

**Sections in order:**
1. Imports and environment variable loading
2. `UniFiMCPServer` class initialization
3. Resource definitions (`@mcp.resource()`)
   - Sites
   - Network resources (devices, clients, networks, etc.)
   - Access resources (doors, readers)
   - Protect resources (cameras, NVR)
4. Tool definitions (`@mcp.tool()`)
   - Client management (block, kick, reconnect)
   - Device management (locate)
   - Access control (unlock doors)
   - Protect management (reboot cameras)
5. Prompt definitions (`@mcp.prompt()`)
6. Helper functions (pagination, auth, URL building)
7. Server initialization and run

## Important Notes

**Resource URI Design:**
- Must be unique and descriptive
- Use consistent naming: `sites://{site_id}/{type}`
- Special resources use custom prefixes: `access://`, `protect://`

**Tool Return Format:**
All tools return:
```python
{
    "success": bool,
    "message": str,
    "data": dict | None  # Optional payload
}
```

**Error Handling:**
- HTTP errors are caught and returned as `{"success": false, "message": error}`
- TLS verification disabled by default for self-signed certs (configurable)

**Site IDs:**
- Most resources require `site_id` parameter
- Default site is usually `"default"`
- Get available sites from `sites://` resource first

**Session Management:**
- Uses httpx.AsyncClient with `verify=False` for self-signed certs
- Timeout configured via `UNIFI_TIMEOUT_S` (default 15s)
- Legacy cookie auth persists across requests in session

## Known Limitations

1. **No Tests:** No pytest setup or test coverage currently
2. **Empty README:** README.md exists but has no content
3. **Filename Typo:** `secreds.ev` should be `secrets.env.example`
4. **Limited Protect Support:** Only basic camera/NVR operations implemented
5. **Site Manager Stub:** Cloud API endpoints not fully functional
6. **No CI/CD:** No automated testing or deployment pipeline

## When Adding New Features

**Adding a New Resource:**
1. Define `@mcp.resource()` function
2. Use unique URI pattern
3. Return list of TextContent or ImageContent objects
4. Include comprehensive JSON data in content

**Adding a New Tool:**
1. Define `@mcp.tool()` function with type hints
2. Use descriptive parameter names and docstrings
3. Return standardized `{"success": bool, "message": str}` format
4. Handle errors gracefully

**Adding a New Prompt:**
1. Define `@mcp.prompt()` function
2. Provide clear step-by-step workflow
3. Reference actual tools and resources by name
4. Include example commands

**API Coverage:**
Check UniFi documentation:
- Integration API: `https://{host}/proxy/network/v2/api/...`
- Legacy API: `https://{host}/proxy/network/api/s/{site}/...`
- Access API: `https://{host}/proxy/access/api/v2/...`
- Protect API: `https://{host}/proxy/protect/api/...`
