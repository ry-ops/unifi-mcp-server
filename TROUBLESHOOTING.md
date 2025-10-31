# 🔧 UniFi MCP Server - Troubleshooting Guide

Comprehensive troubleshooting guide for resolving common issues with the UniFi MCP Server.

---

## Table of Contents
- [Quick Diagnostics](#quick-diagnostics)
- [Common Issues](#common-issues)
- [Claude Desktop Integration Issues](#-claude-desktop-integration-issues)
- [Beginner Troubleshooting](#-beginner-troubleshooting)
- [Intermediate Troubleshooting](#-intermediate-troubleshooting)
- [Advanced Troubleshooting](#-advanced-troubleshooting)
- [Error Reference](#error-reference)
- [Getting Help](#getting-help)

---

## Quick Diagnostics

Run these commands first to identify the problem:

```bash
# Test all API connections
uv run python -c "from main import debug_api_connectivity; print(debug_api_connectivity())"

# Discover valid site IDs
uv run python -c "from main import discover_sites; print(discover_sites())"

# Check system health
uv run python -c "from main import get_system_status; print(get_system_status())"
```

---

## Common Issues

### Issue: MCP Server Won't Start

**Symptoms**: Server fails to start, import errors, module not found

**Quick Fix**:
```bash
# Ensure you're in the project directory
cd /path/to/unifi-mcp-server

# Reinstall dependencies
uv sync

# Try running the server
uv run mcp dev main.py
```

**Common Causes**:
- Missing dependencies
- Wrong Python version (need 3.12+)
- `uv` not installed

---

### Issue: "401 Unauthorized" Error

**Symptoms**: Cannot connect to controller, authentication fails

**Quick Fix**:
1. Check API key in `secrets.env`
2. Regenerate API key from UniFi controller
3. Verify controller IP address is correct

```bash
# Test connectivity
uv run python -c "from main import debug_api_connectivity; print(debug_api_connectivity())"
```

**See**: [Authentication Issues](#authentication-issues) below

---

### Issue: "Site ID 'default' not valid"

**Symptoms**: Commands fail with site ID errors

**Quick Fix**:
```bash
# Discover correct site IDs
uv run python -c "from main import discover_sites; print(discover_sites())"

# Use auto-discovery tools
uv run python -c "from main import working_list_hosts_example; print(working_list_hosts_example())"
```

**Solution**: Use tools with built-in site discovery instead of hardcoding "default"

---

### Issue: "2FA Required" for Legacy API

**Symptoms**: Login fails, asks for two-factor authentication

**Quick Fix Options**:
1. **Use Integration API instead** (recommended - doesn't need 2FA)
2. Create a local admin account without 2FA
3. Use app-specific passwords (if supported)

**Note**: Integration API (API key) is preferred over Legacy API (username/password)

---

### Issue: Can't See Any Devices or Clients

**Symptoms**: Empty lists, no data returned

**Diagnostic Steps**:
```bash
# 1. Test API connectivity
uv run python -c "from main import debug_api_connectivity; print(debug_api_connectivity())"

# 2. Check if controller is reachable
ping YOUR_CONTROLLER_IP

# 3. Verify API key has proper permissions
# Go to UniFi controller web UI → Settings → Admins
```

**Common Causes**:
- Wrong site ID
- API key lacks permissions
- Network connectivity issues
- Controller not responding

---

## 🔌 Claude Desktop Integration Issues

### Verifying MCP Server Connection

**Check if Claude Desktop sees your MCP server**:

1. **Open Claude Desktop**
2. **Look for the 🔌 icon** in the bottom right of the input box
3. **Click the icon** to see connected MCP servers
4. **You should see "unifi"** listed

**If you don't see the icon or the server**:
- Claude Desktop may not have loaded the config
- Configuration file may have errors
- Server may have failed to start

---

### Issue: MCP Server Not Appearing in Claude Desktop

**Symptoms**: No MCP icon, or "unifi" server not listed

**Quick Fix Checklist**:

1. ✅ **Check config file location**:
```bash
# macOS
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Windows
type %APPDATA%\Claude\claude_desktop_config.json

# Linux
cat ~/.config/Claude/claude_desktop_config.json
```

2. ✅ **Verify JSON is valid**:
```bash
# Use a JSON validator
python3 -m json.tool ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Should print formatted JSON with no errors
```

3. ✅ **Restart Claude Desktop completely**:
   - Quit Claude Desktop (Cmd+Q on macOS, not just close window)
   - Wait 5 seconds
   - Reopen Claude Desktop

4. ✅ **Check for config syntax errors**:
```json
{
  "mcpServers": {
    "unifi": {
      "command": "uv",
      "args": [
        "--directory",
        "/FULL/PATH/TO/unifi-mcp-server",
        "run",
        "main.py"
      ]
    }
  }
}
```

**Common Mistakes**:
- ❌ Missing comma after `"command": "uv"`
- ❌ Extra comma after last array item
- ❌ Relative path instead of absolute path
- ❌ Wrong quotes (use `"` not `'` or smart quotes)
- ❌ Config file in wrong location

---

### Issue: Server Starts But No Tools/Resources Available

**Symptoms**: Server shows as connected, but can't see any UniFi tools or resources

**Diagnostic**:
1. Ask Claude: *"What MCP tools and resources do you have available?"*
2. Claude should list UniFi-related tools like:
   - `get_system_status`
   - `list_hosts`
   - `block_client`
   - Resources like `status://system`

**If tools are missing**:

1. **Check server logs** (see below for how to view logs)
2. **Verify server started successfully**
3. **Check for initialization errors**

**Quick Fix**:
```bash
# Test server can start
cd /path/to/unifi-mcp-server
uv run main.py

# Should output MCP protocol messages
# Press Ctrl+C to stop
```

---

### Issue: "Command 'uv' not found" Error

**Symptoms**: Claude Desktop can't find `uv` command

**Cause**: `uv` not in PATH for GUI applications

**Solution 1 - Full Path to uv** (Recommended):
```json
{
  "mcpServers": {
    "unifi": {
      "command": "/full/path/to/uv",
      "args": [
        "--directory",
        "/Users/yourusername/projects/unifi-mcp-server",
        "run",
        "main.py"
      ]
    }
  }
}
```

**Find uv path**:
```bash
which uv
# Output: /Users/yourusername/.local/bin/uv
# Use this path in config
```

**Solution 2 - Use Python directly**:
```json
{
  "mcpServers": {
    "unifi": {
      "command": "/usr/bin/python3",
      "args": [
        "-m",
        "main"
      ],
      "cwd": "/Users/yourusername/projects/unifi-mcp-server"
    }
  }
}
```

---

### Issue: Environment Variables Not Loading

**Symptoms**: Server starts but gets authentication errors, even though `secrets.env` is configured

**Cause**: Claude Desktop doesn't automatically load `.env` files

**Solution 1 - Add env to config** (Recommended):
```json
{
  "mcpServers": {
    "unifi": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/yourusername/projects/unifi-mcp-server",
        "run",
        "main.py"
      ],
      "env": {
        "UNIFI_API_KEY": "your_actual_api_key_here",
        "UNIFI_GATEWAY_HOST": "10.88.140.144",
        "UNIFI_GATEWAY_PORT": "443",
        "UNIFI_VERIFY_TLS": "false"
      }
    }
  }
}
```

**Solution 2 - Modify main.py to load .env**:
```python
# Add to top of main.py
from dotenv import load_dotenv
load_dotenv("secrets.env")
```

**Security Note**: Be careful with credentials in `claude_desktop_config.json` - it's often synced/backed up

---

### Issue: Path Issues on Windows

**Symptoms**: "File not found" errors on Windows

**Windows-Specific Fixes**:

1. **Use forward slashes or escaped backslashes**:
```json
// Option 1: Forward slashes (works on Windows!)
{
  "command": "C:/Users/YourName/.local/bin/uv",
  "args": [
    "--directory",
    "C:/Users/YourName/projects/unifi-mcp-server",
    "run",
    "main.py"
  ]
}

// Option 2: Escaped backslashes
{
  "command": "C:\\Users\\YourName\\.local\\bin\\uv",
  "args": [
    "--directory",
    "C:\\Users\\YourName\\projects\\unifi-mcp-server",
    "run",
    "main.py"
  ]
}
```

2. **Use uv.exe explicitly**:
```json
{
  "command": "C:/Users/YourName/.cargo/bin/uv.exe"
}
```

3. **Check Windows path limits** (260 character limit):
   - Use shorter directory names if needed
   - Or enable long path support in Windows

---

### Viewing Claude Desktop Logs

**Finding MCP server logs**:

#### **macOS**:
```bash
# View logs in real-time
tail -f ~/Library/Logs/Claude/mcp*.log

# Or check system console
log show --predicate 'process == "Claude"' --last 5m
```

#### **Windows**:
```powershell
# Logs typically in:
Get-Content "$env:APPDATA\Claude\logs\mcp*.log" -Tail 50 -Wait
```

#### **Linux**:
```bash
# Check logs
tail -f ~/.config/Claude/logs/mcp*.log
```

**What to look for**:
- `Error starting MCP server`
- `Command not found: uv`
- `Authentication failed`
- `Connection refused`
- Python tracebacks

---

### Testing MCP Server Outside Claude Desktop

**Before troubleshooting Claude Desktop integration, test the server independently**:

#### **Test 1: Direct Python Execution**
```bash
cd /path/to/unifi-mcp-server
uv run python -c "from main import get_system_status; print(get_system_status())"

# Should print system status without errors
```

#### **Test 2: MCP Dev Mode**
```bash
uv run mcp dev main.py

# Opens MCP Inspector at http://localhost:5173
# Test tools and resources in the web UI
```

#### **Test 3: Check MCP Protocol**
```bash
# Run server and check it speaks MCP protocol
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | uv run main.py

# Should get JSON response with MCP version info
```

**If these tests fail**, fix the server issues first before debugging Claude Desktop integration.

---

### Common Configuration Examples

#### **Minimal Config (macOS)**:
```json
{
  "mcpServers": {
    "unifi": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/ryandahlberg/projects/unifi-mcp-server",
        "run",
        "main.py"
      ]
    }
  }
}
```

#### **Config with Environment Variables**:
```json
{
  "mcpServers": {
    "unifi": {
      "command": "/usr/local/bin/uv",
      "args": [
        "--directory",
        "/Users/ryandahlberg/projects/unifi-mcp-server",
        "run",
        "main.py"
      ],
      "env": {
        "UNIFI_API_KEY": "${UNIFI_API_KEY}",
        "UNIFI_GATEWAY_HOST": "10.88.140.144",
        "UNIFI_GATEWAY_PORT": "443",
        "UNIFI_VERIFY_TLS": "false"
      }
    }
  }
}
```

#### **Config with Debugging Enabled**:
```json
{
  "mcpServers": {
    "unifi": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/ryandahlberg/projects/unifi-mcp-server",
        "run",
        "main.py"
      ],
      "env": {
        "PYTHONVERBOSE": "1",
        "MCP_DEBUG": "true"
      }
    }
  }
}
```

---

### Troubleshooting Workflow for Claude Desktop

**Step-by-step debugging process**:

1. ✅ **Verify config file is valid JSON**
   ```bash
   python3 -m json.tool ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

2. ✅ **Test server runs independently**
   ```bash
   cd /path/to/unifi-mcp-server
   uv run main.py
   ```

3. ✅ **Check uv is accessible**
   ```bash
   which uv
   /path/to/uv --version
   ```

4. ✅ **Verify absolute paths in config**
   - No `~` or relative paths
   - Use `pwd` to get full path

5. ✅ **Restart Claude Desktop completely**
   - Quit fully (Cmd+Q)
   - Wait 5 seconds
   - Reopen

6. ✅ **Check for MCP icon**
   - Should appear in input box
   - Click to see servers

7. ✅ **Test in Claude**
   - Ask: "What UniFi tools do you have?"
   - Should list tools like `get_system_status`

8. ✅ **Test actual functionality**
   - Ask: "Check my UniFi network health"
   - Should use MCP tools to fetch data

---

### Advanced: Running Multiple MCP Servers

**If you have multiple MCP servers**:

```json
{
  "mcpServers": {
    "unifi": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/ryandahlberg/projects/unifi-mcp-server",
        "run",
        "main.py"
      ]
    },
    "another-server": {
      "command": "node",
      "args": [
        "/path/to/another-server/index.js"
      ]
    }
  }
}
```

**Troubleshooting tips**:
- Test each server individually
- Check for port conflicts
- Verify each server's logs separately

---

### Known Issues and Limitations

#### **Issue**: Slow first request
**Cause**: Server initialization and authentication takes time
**Workaround**: First request may take 5-10 seconds - this is normal

#### **Issue**: Server disconnects after idle
**Cause**: Claude Desktop may stop idle MCP servers
**Workaround**: Server will restart on next request automatically

#### **Issue**: Changes to secrets.env not reflected
**Cause**: Claude Desktop doesn't auto-reload config
**Workaround**: Restart Claude Desktop after changing config/env

---

### Still Can't Connect?

**Last resort debugging**:

1. **Create a minimal test server**:
```python
# test_mcp.py
import sys
import json

def main():
    # Read one line from stdin
    line = sys.stdin.readline()
    request = json.loads(line)

    # Send a simple response
    response = {
        "jsonrpc": "2.0",
        "id": request.get("id"),
        "result": {"status": "ok"}
    }
    print(json.dumps(response))
    sys.stdout.flush()

if __name__ == "__main__":
    main()
```

2. **Test minimal server in Claude Desktop**:
```json
{
  "mcpServers": {
    "test": {
      "command": "python3",
      "args": ["/path/to/test_mcp.py"]
    }
  }
}
```

3. **If minimal server works**, issue is in UniFi MCP server code
4. **If minimal server fails**, issue is with Claude Desktop configuration

---

## 🟢 Beginner Troubleshooting

### Step 1: Verify Installation

**Check Python version** (need 3.12+):
```bash
python3 --version
```

**Check uv installation**:
```bash
uv --version
```

**Install uv if missing**:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

### Step 2: Set Up Environment

**Create virtual environment**:
```bash
cd unifi-mcp-server
uv venv
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate     # On Windows
```

**Install dependencies**:
```bash
uv sync
```

---

### Step 3: Configure Credentials

**Check secrets.env file exists**:
```bash
ls -la secrets.env
```

**Verify secrets.env format**:
```env
# Should look like this:
UNIFI_API_KEY=your_actual_api_key_here
UNIFI_GATEWAY_HOST=10.88.140.144
UNIFI_GATEWAY_PORT=443
UNIFI_VERIFY_TLS=false

# Optional:
UNIFI_USERNAME=your_username
UNIFI_PASSWORD=your_password
UNIFI_SITEMGR_BASE=https://api.ui.com
UNIFI_SITEMGR_TOKEN=your_cloud_token
```

**Common mistakes**:
- ❌ Leaving placeholder values like `your_actual_api_key_here`
- ❌ Missing quotes around values with special characters
- ❌ Wrong IP address or port
- ❌ Spaces around `=` sign

---

### Step 4: Test Basic Connectivity

**Test if controller is reachable**:
```bash
ping YOUR_CONTROLLER_IP
```

**Test HTTPS access**:
```bash
curl -k https://YOUR_CONTROLLER_IP:443
```

**Run full diagnostics**:
```bash
uv run python -c "from main import debug_api_connectivity; print(debug_api_connectivity())"
```

---

### Step 5: Common Beginner Mistakes

#### Mistake 1: Not in Project Directory
```bash
# Wrong - running from home directory
cd ~
uv run main.py  # ❌ Won't work!

# Correct - run from project directory
cd /path/to/unifi-mcp-server
uv run main.py  # ✅ Works!
```

#### Mistake 2: Using Wrong API Key
```bash
# API key should be from UniFi controller, NOT:
# - UniFi account password
# - Router admin password
# - WiFi password

# Get correct API key:
# 1. Log into UniFi controller web UI
# 2. Settings → System → Advanced → API
# 3. Create API Key
```

#### Mistake 3: Firewall Blocking Access
```bash
# Check if firewall allows port 443:
telnet YOUR_CONTROLLER_IP 443

# If connection refused, check:
# - Controller firewall settings
# - Network firewall rules
# - VPN/proxy settings
```

---

## 🟡 Intermediate Troubleshooting

### Authentication Issues

#### API Key Not Working

**Symptoms**: 401 Unauthorized with Integration API

**Diagnostic**:
```bash
# Check what the API is returning
uv run python -c "
from main import debug_api_connectivity
import json
result = debug_api_connectivity()
print(json.dumps(result, indent=2))
"
```

**Solutions**:

1. **Regenerate API Key**:
   - Go to UniFi controller → Settings → System → Advanced → API
   - Delete old API key
   - Create new API key
   - Update `secrets.env` with new key

2. **Verify API Key Format**:
   - Should be long alphanumeric string (e.g., `ABC123def456...`)
   - No spaces, no quotes in secrets.env
   - No line breaks in the key

3. **Check API Key Permissions**:
   - Ensure the API key has "Full Management" permissions
   - Some features require admin-level access

---

#### 2FA Blocking Legacy API

**Symptoms**: "2fa required" error when using Legacy API

**Workaround 1 - Use Integration API** (Recommended):
```python
# Instead of legacy_get(), use Integration API
from main import paginate_integration
devices = paginate_integration("/sites/{site_id}/devices")
```

**Workaround 2 - Create Local Admin Without 2FA**:
1. UniFi controller → Settings → Admins
2. Add new local administrator
3. Do NOT enable 2FA for this account
4. Use these credentials in `secrets.env`

**Workaround 3 - Use App-Specific Password**:
- Some UniFi controllers support app-specific passwords
- Check Settings → Admins → Your Account
- Generate app-specific password
- Use this instead of main password

---

### Site ID Issues

#### Finding Correct Site IDs

**Problem**: Commands fail with "invalid site ID"

**Solution 1 - Auto Discovery**:
```python
from main import working_list_hosts_example
# This automatically discovers and uses correct site IDs
result = working_list_hosts_example()
```

**Solution 2 - Manual Discovery**:
```python
from main import discover_sites
sites = discover_sites()
print(f"Valid site IDs: {sites}")
```

**Solution 3 - Check Controller Web UI**:
1. Log into UniFi controller
2. Look at the URL when viewing a site
3. URL contains site ID: `/network/default/devices`
   - Site ID here would be "default"
4. Or check Settings → System → Sites

---

### Network Connectivity Issues

#### Controller Not Reachable

**Symptoms**: Connection timeout, cannot reach controller

**Diagnostic Steps**:

1. **Check basic connectivity**:
```bash
ping YOUR_CONTROLLER_IP
```

2. **Check port accessibility**:
```bash
nc -zv YOUR_CONTROLLER_IP 443
# or
telnet YOUR_CONTROLLER_IP 443
```

3. **Check TLS/SSL**:
```bash
openssl s_client -connect YOUR_CONTROLLER_IP:443
```

4. **Verify from same network**:
   - MCP server must be on same network as controller
   - Or have route to controller network
   - VPN may be required for remote access

**Common Solutions**:
- Ensure controller is powered on and responding
- Check network firewall rules
- Verify controller IP hasn't changed (DHCP)
- Disable VPN if causing routing issues
- Check for network segmentation/VLANs blocking access

---

### Performance Issues

#### Slow Response Times

**Symptoms**: Commands take long time to complete

**Diagnostic**:
```python
import time
from main import get_system_status

start = time.time()
status = get_system_status()
elapsed = time.time() - start
print(f"Took {elapsed:.2f} seconds")
```

**Solutions**:

1. **Enable Caching** (already enabled for 5 minutes):
   - Status calls are cached automatically
   - Subsequent calls within 5 minutes use cache

2. **Use Quick Status**:
```python
# Instead of full system status:
from main import get_quick_status
status = get_quick_status()  # Much faster!
```

3. **Network Optimization**:
   - Use wired connection instead of WiFi
   - Reduce network latency
   - Check for packet loss: `ping -c 100 YOUR_CONTROLLER_IP`

4. **Controller Resources**:
   - Ensure controller isn't overloaded
   - Check controller CPU/memory usage
   - Restart controller if needed

---

## 🔴 Advanced Troubleshooting

### Deep Diagnostics

#### Enable Debug Logging

**Add debug output to main.py**:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Or run with verbose output**:
```bash
PYTHONVERBOSE=1 uv run main.py
```

---

#### Inspect Raw API Responses

**Check exact API responses**:
```python
import requests
import json

# Test Integration API
url = "https://YOUR_IP:443/proxy/network/integrations/v1/sites"
headers = {"X-API-KEY": "YOUR_API_KEY"}
response = requests.get(url, headers=headers, verify=False)

print(f"Status: {response.status_code}")
print(f"Headers: {response.headers}")
print(f"Body: {json.dumps(response.json(), indent=2)}")
```

**Test Legacy API**:
```python
session = requests.Session()

# Login
login_url = "https://YOUR_IP:443/api/auth/login"
login_data = {"username": "admin", "password": "password"}
login_resp = session.post(login_url, json=login_data, verify=False)
print(f"Login: {login_resp.status_code}")

# Get sites
sites_url = "https://YOUR_IP:443/proxy/network/api/self/sites"
sites_resp = session.get(sites_url, verify=False)
print(f"Sites: {json.dumps(sites_resp.json(), indent=2)}")
```

---

#### Network Packet Analysis

**Capture traffic with tcpdump**:
```bash
# Capture HTTPS traffic to controller
sudo tcpdump -i any -n host YOUR_CONTROLLER_IP and port 443 -w unifi.pcap

# Analyze with Wireshark
wireshark unifi.pcap
```

**Check TLS handshake**:
```bash
openssl s_client -connect YOUR_CONTROLLER_IP:443 -showcerts
```

---

#### Controller-Side Debugging

**Check UniFi controller logs**:

1. **SSH into controller**:
```bash
ssh admin@YOUR_CONTROLLER_IP
```

2. **View logs**:
```bash
# System logs
tail -f /var/log/syslog

# UniFi Network logs
tail -f /usr/lib/unifi/logs/server.log

# API access logs
tail -f /usr/lib/unifi/logs/access.log
```

3. **Check for errors**:
```bash
grep -i error /usr/lib/unifi/logs/server.log
grep -i "api" /usr/lib/unifi/logs/server.log
```

---

### API Compatibility Issues

#### Integration API Not Available

**Symptoms**: 404 errors on Integration API endpoints

**Cause**: Older UniFi controller versions don't support Integration API

**Check Controller Version**:
```python
from main import _get, _h_key
response = _get(f"https://{UNIFI_HOST}:{UNIFI_PORT}/proxy/network/api/self", _h_key())
print(f"Version: {response.get('meta', {}).get('server_version')}")
```

**Solutions**:
1. **Update controller** to latest version (recommended)
2. **Use Legacy API** fallback (automatic in most tools)
3. **Check feature compatibility** in NETWORK_PLAYBOOK.md

**Minimum Versions**:
- Integration API: UniFi Network 7.0+
- Full A2A support: UniFi Network 7.4+

---

#### Missing Features/Endpoints

**Symptoms**: Specific endpoint returns 404 or "not found"

**Example**:
```
POST /devices/{id}/locate -> 404 Not Found
```

**Solutions**:

1. **Check if feature is supported**:
```python
from main import debug_registry
registry = debug_registry()
# Check available tools and resources
```

2. **Use alternative approach**:
   - Some features only available via web UI
   - Some require Legacy API instead of Integration API
   - See NETWORK_PLAYBOOK.md for alternatives

3. **File feature request**:
   - Check if others have same issue
   - Open GitHub issue with details
   - Include controller version and logs

---

### SSL/TLS Certificate Issues

#### Self-Signed Certificate Problems

**Symptoms**: SSL verification errors, certificate warnings

**Current Setting** (in code):
```python
VERIFY_TLS = False  # Disabled in secrets.env
```

**If you want to enable TLS verification**:

1. **Export controller certificate**:
```bash
# From UniFi controller
openssl s_client -connect YOUR_CONTROLLER_IP:443 -showcerts
```

2. **Save certificate to file**:
```bash
echo "-----BEGIN CERTIFICATE-----" > unifi-cert.pem
# ... paste certificate ...
echo "-----END CERTIFICATE-----" >> unifi-cert.pem
```

3. **Update code to use certificate**:
```python
# In main.py
VERIFY_TLS = "/path/to/unifi-cert.pem"
```

**Or install official certificate** on UniFi controller

---

### Multi-Site Configuration

#### Managing Multiple Controllers

**Symptoms**: Need to manage multiple UniFi controllers

**Solution 1 - Multiple Config Files**:
```bash
# Create separate configs
cp secrets.env secrets-site1.env
cp secrets.env secrets-site2.env

# Edit each with different credentials
# Run with specific config:
export $(cat secrets-site1.env | xargs)
uv run main.py
```

**Solution 2 - Environment Variables**:
```bash
# Site 1
UNIFI_GATEWAY_HOST=site1.example.com uv run main.py

# Site 2
UNIFI_GATEWAY_HOST=site2.example.com uv run main.py
```

**Future Feature**: Multi-controller support is planned (see roadmap.md)

---

## Error Reference

### Common Error Messages

#### `UniFiHTTPError: 401 Unauthorized`

**Meaning**: Authentication failed
**Causes**:
- Invalid or expired API key
- Wrong username/password
- 2FA required but not provided
**Fix**: Regenerate API key, check credentials

---

#### `UniFiHTTPError: 404 Not Found`

**Meaning**: Endpoint doesn't exist
**Causes**:
- Wrong URL or site ID
- Feature not supported by controller version
- Endpoint not available in Integration API
**Fix**: Check site ID, verify controller version, try Legacy API

---

#### `Site ID 'default' is not valid`

**Meaning**: Site ID doesn't exist on controller
**Causes**:
- Hardcoded "default" site ID
- Site was renamed or deleted
**Fix**: Use `discover_sites()` or auto-discovery tools

---

#### `Connection timeout` / `Connection refused`

**Meaning**: Cannot reach controller
**Causes**:
- Controller offline
- Network firewall blocking
- Wrong IP address or port
- Network routing issue
**Fix**: Check connectivity, verify IP, check firewall

---

#### `2fa required`

**Meaning**: Two-factor authentication needed
**Causes**:
- Account has 2FA enabled
- Legacy API login attempt
**Fix**: Use Integration API, or create local admin without 2FA

---

#### `SSRF protection: blocked`

**Meaning**: URL validation blocked request
**Causes**:
- Trying to access non-whitelisted host
- Security protection triggered
**Fix**: Check ALLOWED_HOSTS in main.py, verify URL is correct

---

#### `No endpoint POST /integration/v1/...`

**Meaning**: Integration API doesn't support this operation
**Causes**:
- Controller version too old
- Feature not exposed via Integration API
**Fix**: Update controller, use Legacy API, or use web UI

---

### Python/Environment Errors

#### `ModuleNotFoundError: No module named 'mcp'`

**Fix**:
```bash
uv sync  # Reinstall dependencies
```

---

#### `Python version too old`

**Fix**:
```bash
# Install Python 3.12+
# On macOS with Homebrew:
brew install python@3.12

# On Ubuntu/Debian:
sudo apt install python3.12
```

---

#### `uv: command not found`

**Fix**:
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Restart shell
source ~/.bashrc  # or ~/.zshrc
```

---

## Getting Help

### Before Asking for Help

1. ✅ Run `debug_api_connectivity()` and save output
2. ✅ Check this troubleshooting guide
3. ✅ Search existing GitHub issues
4. ✅ Collect relevant error messages
5. ✅ Note your UniFi controller version
6. ✅ Document steps you've already tried

---

### How to Get Help

#### GitHub Issues (Recommended)
**Best for**: Bug reports, feature requests, general questions

**Include**:
- UniFi controller version
- Python version (`python3 --version`)
- Error messages (full stack trace)
- Output from `debug_api_connectivity()`
- Steps to reproduce
- What you've already tried

**Link**: https://github.com/ry-ops/unifi-mcp-server/issues

---

#### Documentation
- 📖 **README.md** - Setup and installation
- 📚 **NETWORK_PLAYBOOK.md** - All commands and examples
- 🗺️ **roadmap.md** - Features and future plans
- 📝 **commands.md** - Command reference

---

#### Community Resources
- UniFi Community Forums (for controller-specific questions)
- MCP Protocol Documentation (for MCP/AI integration questions)
- Python Documentation (for coding questions)

---

### What to Include in Bug Reports

**Good Bug Report Example**:
```markdown
## Bug Description
Cannot list devices - getting 401 Unauthorized error

## Environment
- UniFi Controller: UDM Pro, Network 7.5.187
- Python: 3.12.3
- OS: macOS 14.0

## Error Message
```
UniFiHTTPError: GET https://10.88.1.1:443/proxy/network/integrations/v1/sites/default/devices -> 401 Unauthorized
```

## Steps to Reproduce
1. Set API key in secrets.env
2. Run: `uv run python -c "from main import get_system_status; print(get_system_status())"`
3. Error occurs

## Debug Output
```json
{
  "timestamp": "2025-10-28T12:00:00",
  "tests": {
    "local_controller": {
      "status": "failed",
      "status_code": 401
    }
  }
}
```

## What I've Tried
- Regenerated API key (3 times)
- Verified IP address is correct
- Tested with curl - same error
- Checked controller logs - no errors shown
```

---

## Diagnostic Command Reference

### Quick Tests
```bash
# Full API diagnostics
uv run python -c "from main import debug_api_connectivity; print(debug_api_connectivity())"

# Discover sites
uv run python -c "from main import discover_sites; print(discover_sites())"

# System health
uv run python -c "from main import get_system_status; print(get_system_status())"

# Quick status
uv run python -c "from main import get_quick_status; print(get_quick_status())"
```

### Detailed Tests
```bash
# List devices
uv run python -c "from main import paginate_integration; print(paginate_integration('/sites/SITE_ID/devices'))"

# List clients
uv run python -c "from main import list_active_clients; print(list_active_clients())"

# Test cloud API
uv run python -c "from main import list_hosts_cloud; print(list_hosts_cloud())"

# Show all registered tools
uv run python -c "from main import debug_registry; print(debug_registry())"
```

---

## Tips for Success

### Best Practices

1. **Always use auto-discovery tools**
   - Prefer `working_list_hosts_example()` over manual site IDs
   - Use `discover_sites()` to find correct IDs

2. **Check controller compatibility**
   - Keep controller updated to latest version
   - Check minimum version requirements

3. **Use Integration API when possible**
   - Faster than Legacy API
   - No 2FA issues
   - Better security (API keys vs passwords)

4. **Enable proper logging**
   - Helps diagnose issues
   - Save output from debug commands

5. **Test incrementally**
   - Test connectivity first
   - Then test auth
   - Then test specific features

6. **Keep credentials secure**
   - Never commit `secrets.env` to git
   - Rotate API keys regularly
   - Use least-privilege principles

---

## Still Having Issues?

If you've tried everything in this guide and still have problems:

1. **Double-check basics**:
   - Secrets.env has correct values
   - Controller is accessible
   - API key is valid and has permissions

2. **Try minimal test**:
```bash
# Simplest possible test
curl -k -H "X-API-KEY: YOUR_KEY" https://YOUR_IP:443/proxy/network/integrations/v1/sites
```

3. **Open GitHub Issue** with:
   - Full error output
   - Debug diagnostics output
   - Controller version
   - Steps to reproduce

4. **Check for known issues**:
   - Search GitHub issues
   - Check UniFi release notes for API changes

---

**Last Updated**: October 28, 2025
**Version**: 1.0
