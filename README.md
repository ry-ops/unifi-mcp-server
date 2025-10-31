# UniFi MCP Server

A Model Context Protocol (MCP) server that integrates UniFi network equipment with AI assistants, exposing UniFi Network, Access, and Protect APIs through a standardized interface.

## Overview

This MCP server enables AI assistants to interact with UniFi controllers, providing:

- **Resources** (read-only): Sites, devices, clients, networks, cameras, access control
- **Tools** (safe write operations): Block/kick clients, locate devices, unlock doors, reboot cameras
- **Prompts** (AI guidance): Step-by-step workflows for common tasks

### Supported UniFi Products

- UniFi Network (switches, access points, gateways)
- UniFi Access (door locks, readers)
- UniFi Protect (cameras, NVR)

## Features

- Dual authentication (API key + legacy cookie fallback)
- Automatic pagination for large datasets
- Health check endpoints for monitoring
- Safe operation design (confirmation required for destructive actions)
- TLS verification configurable for self-signed certificates

## Prerequisites

- Python 3.12 or higher
- UniFi Controller/Gateway (Cloud Key, Dream Machine, or self-hosted)
- UniFi API key (recommended) or username/password (legacy)
- Network access to UniFi controller

## Installation

### 1. Clone or download this repository

```bash
git clone <repository-url>
cd mcp-server-unifi
```

### 2. Install uv package manager (if not already installed)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 3. Create virtual environment and install dependencies

```bash
uv venv
uv pip install -e .
```

### 4. Configure credentials

Create a `secrets.env` file in the project root:

```bash
# UniFi Controller Settings
UNIFI_API_KEY=your_actual_api_key_here
UNIFI_GATEWAY_HOST=192.168.1.1
UNIFI_GATEWAY_PORT=443
UNIFI_VERIFY_TLS=false

# Legacy credentials (optional, for endpoints not in Integration API)
UNIFI_USERNAME=admin
UNIFI_PASSWORD=your_password

# Site Manager Settings (optional, for cloud API)
UNIFI_SITEMGR_BASE=https://api.ui.com
UNIFI_SITEMGR_TOKEN=your_site_manager_api_key
UNIFI_SITEMGR_PREFIX=/v1

# Request timeout (optional, default 15 seconds)
UNIFI_TIMEOUT_S=15
```

**Important:** Never commit `secrets.env` to version control. This file is excluded in `.gitignore`.

## Getting Your UniFi API Key

### Method 1: UniFi OS Console (Recommended)

1. Log into your UniFi controller web interface
2. Navigate to **Settings** > **System** > **API**
3. Click **Create New API Key**
4. Give it a name (e.g., "MCP Server")
5. Copy the generated key immediately (it won't be shown again)

### Method 2: Legacy Username/Password

If your controller doesn't support API keys, you can use username/password authentication:

1. Use your existing UniFi admin username and password
2. Set `UNIFI_USERNAME` and `UNIFI_PASSWORD` in `secrets.env`
3. The server will automatically use cookie-based authentication

**Note:** API key authentication is more secure and recommended for production use.

## Usage

### Running the Server

```bash
python main.py
```

The server runs on stdio transport, suitable for integration with MCP clients.

### Testing Connection

Use the health check to verify connectivity:

```python
# Resource endpoints:
# - unifi://health
# - health://unifi
# - status://unifi

# Or use the tool:
unifi_health()
```

### Available Resources

Resources are read-only data endpoints:

```
sites://                              # List all sites
sites://{site_id}/devices             # List devices
sites://{site_id}/clients             # List all clients
sites://{site_id}/clients/active      # List active clients only
sites://{site_id}/wlans               # List wireless networks
sites://{site_id}/search/devices/{query}   # Search devices
sites://{site_id}/search/clients/{query}   # Search clients

access://doors                        # List access control doors
access://readers                      # List access control readers
access://users                        # List access control users
access://events                       # List access control events

protect://nvr                         # Get NVR status
protect://cameras                     # List all cameras
protect://camera/{camera_id}          # Get specific camera
protect://events                      # List motion/smart detection events
protect://events/range/{start}/{end}  # Get events in time range
protect://streams/{camera_id}         # Get camera stream URLs

unifi://capabilities                  # Test all API endpoints
```

### Available Tools

Tools perform safe write operations:

#### Network Tools
- `block_client(site_id, mac)` - Block a client from the network
- `unblock_client(site_id, mac)` - Unblock a previously blocked client
- `kick_client(site_id, mac)` - Force disconnect a client
- `locate_device(site_id, device_id, seconds=30)` - Flash device LEDs

#### Legacy Network Tools
- `wlan_set_enabled_legacy(site_id, wlan_id, enabled)` - Toggle wireless network

#### Access Control Tools
- `access_unlock_door(door_id, seconds=5)` - Momentarily unlock a door

#### Protect Tools
- `protect_camera_reboot(camera_id)` - Reboot a camera
- `protect_camera_led(camera_id, enabled)` - Toggle camera LED
- `protect_toggle_privacy(camera_id, enabled)` - Toggle privacy mode

#### Utility Tools
- `unifi_health()` - Check controller connectivity and validate credentials
- `debug_registry()` - List all registered resources/tools/prompts
- `get_rate_limit_stats(endpoint="global")` - Get rate limiting statistics
- `get_session_info()` - Get legacy session status and expiration (Week 3)
- `invalidate_session()` - Force session invalidation for testing (Week 3)

### Available Prompts

Prompts guide AI assistants through common workflows:

- `how_to_check_unifi_health` - Verify controller connectivity
- `how_to_find_device` - Search and locate a network device
- `how_to_block_client` - Find and block a problematic client
- `how_to_toggle_wlan` - Enable/disable a wireless network
- `how_to_manage_access` - Control door access
- `how_to_find_camera` - Find camera streams
- `how_to_review_motion` - Review motion detection events
- `how_to_reboot_camera` - Safely reboot a camera

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `UNIFI_API_KEY` | Yes* | - | Integration API key from controller |
| `UNIFI_GATEWAY_HOST` | Yes | - | Controller IP address or hostname |
| `UNIFI_GATEWAY_PORT` | No | 443 | Controller HTTPS port |
| `UNIFI_VERIFY_TLS` | No | **true** | Verify TLS certificates (CHANGED in Week 2) |
| `UNIFI_USERNAME` | No** | - | Legacy username for cookie auth |
| `UNIFI_PASSWORD` | No** | - | Legacy password for cookie auth |
| `UNIFI_TIMEOUT_S` | No | 15 | HTTP request timeout in seconds |
| `UNIFI_RATE_LIMIT_PER_MINUTE` | No | 60 | Max API calls per minute per endpoint |
| `UNIFI_RATE_LIMIT_PER_HOUR` | No | 1000 | Max API calls per hour per endpoint |
| `UNIFI_LOG_LEVEL` | No | INFO | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `UNIFI_LOG_FILE` | No | unifi_mcp_audit.log | Audit log file location |
| `UNIFI_LOG_TO_FILE` | No | true | Enable file logging |
| `UNIFI_SESSION_TIMEOUT_S` | No | 3600 | Legacy session timeout in seconds (Week 3) |
| `UNIFI_SITEMGR_BASE` | No | - | Site Manager cloud API base URL |
| `UNIFI_SITEMGR_TOKEN` | No | - | Site Manager API token |

\* Either `UNIFI_API_KEY` or `UNIFI_USERNAME`/`UNIFI_PASSWORD` required
\*\* Required if API key not available or for legacy endpoints

### TLS Certificate Verification

**IMPORTANT SECURITY CHANGE:** As of Week 2 security improvements, TLS verification is **ENABLED BY DEFAULT** (`UNIFI_VERIFY_TLS=true`).

#### Why TLS Verification Matters

TLS verification protects against man-in-the-middle (MITM) attacks by ensuring you're communicating with the actual UniFi controller and not an attacker. Disabling TLS verification makes your credentials and data vulnerable to interception.

#### When to Disable TLS Verification

Only disable TLS verification if:
1. You're using self-signed certificates in a trusted network
2. You understand the security risks
3. You cannot add certificates to your system trust store

To disable TLS verification:

```bash
UNIFI_VERIFY_TLS=false
```

**WARNING:** When disabled, you'll see security warnings in the logs. This is intentional.

#### Proper Certificate Management (Recommended)

Instead of disabling verification, properly manage certificates:

**Option 1: Add Self-Signed Certificate to Trust Store**

```bash
# macOS
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain /path/to/cert.pem

# Linux
sudo cp /path/to/cert.pem /usr/local/share/ca-certificates/unifi.crt
sudo update-ca-certificates
```

**Option 2: Use Valid Certificates**

Use Let's Encrypt or another CA to get valid certificates for your UniFi controller.

**Option 3: Point Verification at Custom CA Bundle**

```bash
# Set custom CA bundle (future enhancement)
export REQUESTS_CA_BUNDLE=/path/to/ca-bundle.crt
```

## Architecture

### Authentication Strategy

The server uses a dual-mode authentication approach:

1. **Primary: API Key** - Modern Integration API endpoints
2. **Fallback: Cookie Auth** - Legacy endpoints and older controllers

The server automatically tries API key first, then falls back to cookie authentication if needed.

### API Coverage

- **Integration API** (`/proxy/network/integrations/v1/...`) - Primary interface for sites, devices, clients
- **Legacy API** (`/proxy/network/api/s/{site}/...`) - Fallback for WLANs, firewall rules
- **Access API** (`/proxy/access/api/v1/...`) - Door locks and access control
- **Protect API** (`/proxy/protect/api/...`) - Cameras and NVR

### URL Building

All URLs are built using safe joining to prevent line-wrap identifier breaks:

```python
url = "/".join([base, "path", "component"])
```

## Security Features (Week 2 Improvements)

This server implements comprehensive security measures to protect your UniFi infrastructure:

### 1. Rate Limiting

Prevents API abuse and denial-of-service attacks against your UniFi controller.

**Configuration:**
```bash
# In secrets.env
UNIFI_RATE_LIMIT_PER_MINUTE=60    # Max 60 requests/minute per endpoint (default)
UNIFI_RATE_LIMIT_PER_HOUR=1000    # Max 1000 requests/hour per endpoint (default)
```

**Features:**
- Per-endpoint rate limiting (prevents single endpoint abuse)
- Sliding time window (not fixed buckets)
- Thread-safe concurrent request handling
- Detailed error messages with retry timing
- Rate limit statistics via `get_rate_limit_stats()` tool

**When rate limits are exceeded:**
```
Rate limit exceeded: 60 calls/minute. Retry in 45.2s
```

### 2. Comprehensive Audit Logging

All API requests, responses, and security events are logged with sensitive data automatically sanitized.

**Configuration:**
```bash
# In secrets.env
UNIFI_LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR, CRITICAL
UNIFI_LOG_FILE=unifi_mcp_audit.log     # Log file location
UNIFI_LOG_TO_FILE=true                  # Write logs to file (default: true)
```

**What is logged:**
- All API requests with sanitized parameters
- All API responses with success/failure status
- Rate limit violations with details
- Authentication attempts
- TLS verification status
- Input validation failures
- HTTP errors with sanitized details

**What is NOT logged:**
- Passwords, API keys, tokens (automatically redacted as `[REDACTED]`)
- Session cookies
- Authorization headers (values redacted)
- Sensitive URL parameters

**Log Format:**
```json
{
  "timestamp": "2024-10-31T12:34:56.789Z",
  "action": "api_request",
  "success": true,
  "details": {
    "method": "POST",
    "endpoint": "/sites/default/clients/block",
    "body": {"mac": "aa:bb:cc:dd:ee:ff"}
  }
}
```

### 3. Input Validation and Sanitization

All tool inputs are validated before use to prevent injection attacks and malformed requests.

**Validation Functions:**
- `validate_site_id()` - Alphanumeric + hyphens/underscores, 1-64 chars
- `validate_mac_address()` - Standard MAC formats with normalization
- `validate_device_id()` - 6-64 character device IDs
- `validate_duration()` - Integer seconds with min/max bounds
- `validate_boolean()` - Type-safe boolean coercion

**Protection Against:**
- SQL injection attempts
- Path traversal attacks (`../../../etc/passwd`)
- Command injection (`;`, `|`, `` ` ``)
- XSS attempts (`<script>`, `javascript:`)
- Invalid data types
- Oversized inputs

**Example:**
```python
# Automatically validated in all tools
block_client("site'; DROP TABLE--", "invalid-mac")
# Returns: {"success": False, "error": "Validation failed: site_id contains invalid characters"}
```

### 4. Request/Response Sanitization

Error messages and logs are automatically sanitized to prevent information disclosure.

**Features:**
- Automatic redaction of sensitive patterns in errors
- Truncation of oversized error messages
- Recursive sanitization of nested data structures
- Protection against log injection
- Depth limits to prevent deep recursion attacks

**Example Sanitization:**
```
Before: Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9
After:  Authorization: Bearer [REDACTED]

Before: POST /api?api_key=sk_live_abc123&password=secret
After:  POST /api?api_key=[REDACTED]&password=[REDACTED]
```

### 5. TLS Verification (Enabled by Default)

See [TLS Certificate Verification](#tls-certificate-verification) section above.

### 6. Session Management (Week 3 Enhancement)

Legacy cookie-based authentication includes automatic session management:

**Features:**
- Automatic session timeout (configurable via `UNIFI_SESSION_TIMEOUT_S`)
- Automatic session refresh at 80% of timeout
- Thread-safe session operations
- Session age tracking and invalidation
- Manual session invalidation for credential rotation testing

**Configuration:**
```bash
# In secrets.env
UNIFI_SESSION_TIMEOUT_S=3600  # 1 hour (default)
```

**Monitoring session health:**
```python
# Get current session status
get_session_info()

# Returns:
{
  "success": true,
  "session": {
    "active": true,
    "created_at": "2025-10-31T14:00:00",
    "age_seconds": 1800,
    "timeout_seconds": 3600,
    "remaining_seconds": 1800,
    "expires_at": "2025-10-31T15:00:00",
    "should_refresh": false
  },
  "session_timeout_configured": 3600
}

# Force session invalidation (useful for credential rotation)
invalidate_session()
```

### 7. Security Vulnerability Scanning (Week 3)

Automated security scanning with Bandit and Safety:

```bash
# Run Bandit (Python code security linter)
bandit -c .bandit -r main.py

# Run Safety (dependency vulnerability scanner)
safety check -r requirements.txt

# Install and run pre-commit hooks (includes Bandit)
pre-commit install
pre-commit run --all-files
```

**What's scanned:**
- SQL injection vulnerabilities
- Shell injection risks
- Hard-coded secrets
- Insecure cryptography
- Known vulnerabilities in dependencies (CVE database)
- Try/except/pass patterns
- Assert statement usage

See `SECURITY.md` for complete security documentation.

### 8. Security Testing

Comprehensive pytest test suite with 85+ security-focused tests:

```bash
# Run security tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=main --cov-report=html

# Run specific security test categories
pytest tests/test_validation.py -v            # Input validation tests
pytest tests/test_sanitization.py -v          # Sanitization tests
pytest tests/test_rate_limiting.py -v         # Rate limiting tests
pytest tests/test_integration_auth.py -v      # Authentication flow tests (Week 3)
pytest tests/test_integration_errors.py -v    # Error handling tests (Week 3)
```

**Test Coverage:**
- Input validation edge cases
- SQL injection attempts
- Path traversal attempts
- XSS attempts
- Command injection attempts
- Rate limiting behavior
- Concurrent access patterns
- Sanitization effectiveness
- Error handling

## Security Best Practices

### Credential Management

1. **Never commit secrets**: The `secrets.env` file is git-ignored
2. **Use API keys**: Preferred over username/password for better security
3. **Restrict API key permissions**: Create keys with minimal required permissions
4. **Rotate credentials regularly**: Update API keys every 90 days (see `SECURITY.md`)
5. **Test before rotating**: Use `test_credentials.py` to validate new credentials
6. **Use environment isolation**: Keep production and development credentials separate
7. **Monitor sessions**: Check session health with `get_session_info()`

### Credential Rotation (Week 3 Feature)

Before rotating credentials in production:

```bash
# Test new API key
python test_credentials.py --api-key NEW_API_KEY

# Test new legacy credentials
python test_credentials.py --username admin --password newpass

# Test all configured credentials
python test_credentials.py --all
```

See `SECURITY.md` for complete credential rotation workflow and zero-downtime procedures.

### Network Security

1. **Use TLS verification**: Enable `UNIFI_VERIFY_TLS=true` with valid certificates
2. **Restrict network access**: Run server on trusted networks only
3. **Firewall rules**: Limit controller access to authorized IPs
4. **VPN recommended**: Access controllers through VPN when possible

### Operational Security

1. **Confirm destructive actions**: Tools require explicit confirmation
2. **Monitor audit logs**: Review UniFi controller logs regularly
3. **Limit tool usage**: Only enable tools your workflow requires
4. **Test in staging**: Verify operations in non-production environment first

## Troubleshooting

### Connection Issues

**Problem:** Server can't connect to controller

```bash
# Check controller is reachable
ping <UNIFI_GATEWAY_HOST>

# Check port is open
nc -zv <UNIFI_GATEWAY_HOST> 443

# Verify API key/credentials
# Run health check: unifi_health()
```

**Problem:** TLS certificate errors

```bash
# Temporarily disable verification for self-signed certs
UNIFI_VERIFY_TLS=false
```

### Authentication Issues

**Problem:** 401 Unauthorized errors

- Verify API key is correct and active
- Check API key hasn't expired
- Ensure API key has required permissions
- Try legacy username/password as fallback

**Problem:** 403 Forbidden errors

- API key may lack permissions for specific endpoint
- Check UniFi controller user role and permissions
- Some endpoints require admin-level access

### Resource Not Found

**Problem:** Resource shows as unavailable

```bash
# Check what's registered
debug_registry()

# Test API endpoint availability
# Access: unifi://capabilities
```

### Legacy API Fallback

**Problem:** WLANs or other features not working

- Ensure `UNIFI_USERNAME` and `UNIFI_PASSWORD` are set
- Legacy credentials required for endpoints not in Integration API
- Check controller version supports required endpoints

## Development

### Project Structure

```
mcp-server-unifi/
   main.py              # Main server implementation
   secrets.env          # Credentials (not in git)
   pyproject.toml       # Python dependencies
   uv.lock              # Locked dependency versions
   .gitignore           # Git exclusions
   .python-version      # Python version specification
   README.md            # This file
   CLAUDE.md            # Development guidance for AI assistants
```

### Adding New Features

#### Adding a Resource

```python
@mcp.resource("custom://resource/{param}")
async def my_resource(param: str) -> Dict[str, Any]:
    # Fetch data from UniFi API
    return data
```

#### Adding a Tool

```python
@mcp.tool()
def my_tool(param: str) -> Dict[str, Any]:
    """Clear description of what this tool does."""
    # Validate inputs
    # Perform operation
    # Return structured response
    return {"success": True, "message": "Operation completed"}
```

#### Adding a Prompt

```python
@mcp.prompt("how_to_do_something")
def my_prompt():
    return {
        "description": "Brief description",
        "messages": [{
            "role": "system",
            "content": "Step-by-step workflow instructions"
        }]
    }
```

### Code Quality

```bash
# Format code
black main.py

# Lint
ruff check main.py

# Type check
mypy main.py
```

## Known Limitations

1. **Single-file architecture**: May need refactoring for large-scale features
2. **Limited Protect support**: Basic camera operations only
3. **Site Manager stub**: Cloud API not fully implemented
4. **No CI/CD**: Manual deployment required (Week 4 roadmap)
5. **Safety 3.x requires auth**: Dependency scanning needs authentication or use deprecated command

## Roadmap

### Week 1 (Critical Fixes) - COMPLETED
- [x] Fix filename typo (secreds.ev → secrets.env)
- [x] Update .gitignore for credential files
- [x] Create comprehensive README
- [x] Add input validation for tool parameters

### Week 2 (Security Improvements) - COMPLETED
- [x] Add comprehensive input validation and sanitization
- [x] Implement rate limiting for API calls (60/min, 1000/hour configurable)
- [x] Add comprehensive audit logging with sanitization
- [x] Enable TLS verification by default with clear override docs
- [x] Implement pytest test suite with 71+ security tests
- [x] Add request/response sanitization
- [x] Protect against SQL injection, XSS, path traversal, command injection
- [x] Add rate limit statistics tool
- [x] Document all security features

### Week 3 (Testing & Hardening) - COMPLETED
- [x] Add security vulnerability scanning (Bandit, Safety)
- [x] Configure pre-commit hooks for automated security checks
- [x] Implement session timeout and refresh for legacy auth
- [x] Add automatic session refresh before expiration (80% threshold)
- [x] Validate all environment variables at startup
- [x] Add environment variable format validation (host, port, timeouts)
- [x] Create integration tests with mock UniFi controller
- [x] Test authentication flows (API key and legacy)
- [x] Test error handling for various HTTP status codes
- [x] Comprehensive secrets rotation workflow documentation
- [x] Create credential testing utility script
- [x] Add health check with credential validation
- [x] Document security scanning procedures

### Week 4 (Production Readiness)
- [ ] Performance optimization for high-volume deployments
- [ ] Add metrics and monitoring capabilities
- [ ] CI/CD pipeline setup
- [ ] Docker containerization
- [ ] Kubernetes deployment manifests

### Future Enhancements
- [ ] Support for UniFi Talk (VoIP)
- [ ] Advanced Protect features (video clips, timelapse)
- [ ] Firewall rule management
- [ ] Network topology mapping
- [ ] Real-time event streaming
- [ ] Multi-controller support
- [ ] Web dashboard for monitoring

## Contributing

Contributions welcome! Please:

1. Follow existing code style
2. Add tests for new features
3. Update documentation
4. Never commit secrets or credentials
5. Test against real UniFi hardware if possible

## License

[Specify your license here]

## Support

For issues, questions, or contributions:

- Open an issue on GitHub
- Check UniFi documentation: https://help.ui.com
- Review MCP specification: https://modelcontextprotocol.io

## Acknowledgments

- Built with [FastMCP](https://github.com/jlowin/fastmcp)
- UniFi API documentation and community
- Model Context Protocol specification

---

**Security Notice:** This server provides direct access to your UniFi network infrastructure. Use appropriate security measures and only run in trusted environments.
