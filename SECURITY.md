# Security Guide

This document provides security best practices, credential rotation procedures, and security scanning instructions for the UniFi MCP Server.

## Table of Contents

1. [Security Scanning](#security-scanning)
2. [Credential Management](#credential-management)
3. [Secrets Rotation Workflow](#secrets-rotation-workflow)
4. [Session Management](#session-management)
5. [Rate Limiting](#rate-limiting)
6. [Logging and Auditing](#logging-and-auditing)
7. [TLS Configuration](#tls-configuration)
8. [Security Hardening Checklist](#security-hardening-checklist)

---

## Security Scanning

### Running Security Scans

The project includes two security scanning tools:

#### 1. Bandit (Python Code Security Linter)

Bandit scans Python code for common security issues.

```bash
# Install dev dependencies
uv pip install -e ".[dev]"

# Run Bandit scan
bandit -c .bandit -r main.py

# Run on all Python files
bandit -c .bandit -r .
```

**What Bandit checks:**
- SQL injection vulnerabilities
- Shell injection risks
- Hard-coded passwords/secrets
- Insecure cryptography usage
- Assert statement usage
- Insecure temporary files

**Configuration:** `.bandit` file in project root

#### 2. Safety (Dependency Vulnerability Scanner)

Safety checks dependencies for known security vulnerabilities.

```bash
# Generate requirements file
uv pip freeze > requirements.txt

# Run Safety scan (deprecated command, still works)
safety check -r requirements.txt

# Alternative: Use pip-audit (no auth required)
pip install pip-audit
pip-audit --desc
```

**Note:** Safety 3.x requires authentication for full features. For CI/CD without auth, use the deprecated `check` command or switch to `pip-audit`.

#### 3. Pre-commit Hooks

Install pre-commit hooks to run security scans automatically:

```bash
# Install pre-commit
pip install pre-commit

# Install git hooks
pre-commit install

# Run manually on all files
pre-commit run --all-files
```

**Hooks configured:**
- Trailing whitespace removal
- End-of-file fixer
- YAML/JSON/TOML validation
- Large file detection
- Private key detection
- Bandit security scanning

---

## Credential Management

### Types of Credentials

The UniFi MCP Server supports two authentication methods:

1. **API Key Authentication** (Recommended)
   - Used for Integration API, Access API
   - Set via `UNIFI_API_KEY` environment variable
   - No session management required
   - More secure and modern

2. **Legacy Cookie Authentication** (Fallback)
   - Used for legacy endpoints and Protect API
   - Requires `UNIFI_USERNAME` and `UNIFI_PASSWORD`
   - Session-based with automatic timeout/refresh
   - Required for WLANs, firewall rules, etc.

### Storing Credentials Securely

**DO:**
- Store credentials in `secrets.env` file (git-ignored)
- Use environment variables in production
- Use a secrets manager (Vault, AWS Secrets Manager, etc.) for production
- Restrict file permissions: `chmod 600 secrets.env`
- Never commit `secrets.env` to version control

**DON'T:**
- Hard-code credentials in source code
- Share credentials in plain text (email, chat, etc.)
- Use the same credentials across environments
- Store credentials in public repositories

### Generating API Keys

To create a UniFi API key:

1. Log into your UniFi controller web interface
2. Navigate to **Settings → Admins**
3. Select your admin user
4. Click **"API Keys"** tab
5. Click **"Generate New Key"**
6. Copy the key (shown only once!)
7. Set `UNIFI_API_KEY` in `secrets.env`

---

## Secrets Rotation Workflow

### When to Rotate Credentials

Rotate credentials in these scenarios:
- **Scheduled rotation:** Every 90 days (best practice)
- **Suspected compromise:** Immediately
- **Employee offboarding:** Within 24 hours
- **Security audit findings:** As required
- **Before production deployment:** Always use fresh credentials

### Pre-Rotation: Testing New Credentials

**CRITICAL:** Always test new credentials before rotating them in production!

```bash
# Test new API key
python test_credentials.py --api-key YOUR_NEW_API_KEY

# Test new legacy credentials
python test_credentials.py --username admin --password new_password

# Test all configured credentials
python test_credentials.py --all

# Test against specific host
python test_credentials.py --all --host 192.168.1.1 --port 443
```

**Expected output for successful test:**
```
============================================================
UniFi Credential Testing Utility
============================================================

Testing API key authentication...
  Host: 192.168.1.1:443
  TLS Verify: False
  Request: GET https://192.168.1.1:443/proxy/network/integrations/v1/sites
  Response: 200 OK

============================================================
Test Summary
============================================================
API Key         [PASS] API key authentication successful! Found 1 sites.

All credential tests passed! Safe to rotate credentials.
```

### Zero-Downtime Credential Rotation

#### For API Keys (Recommended Method)

1. **Generate new API key** in UniFi controller
2. **Test new key:**
   ```bash
   python test_credentials.py --api-key NEW_API_KEY
   ```
3. **Update secrets.env:**
   ```bash
   # Keep old key temporarily
   UNIFI_API_KEY_OLD=old_key_here
   UNIFI_API_KEY=new_key_here
   ```
4. **Restart server** with new key
5. **Verify server health:**
   ```bash
   # Use MCP tool to check health
   get_session_info()
   unifi_health()
   ```
6. **Delete old key** from UniFi controller after 24 hours
7. **Remove from secrets.env:**
   ```bash
   # Delete UNIFI_API_KEY_OLD line
   UNIFI_API_KEY=new_key_here
   ```

#### For Legacy Credentials

1. **Create new admin user** in UniFi controller with different username
2. **Test new credentials:**
   ```bash
   python test_credentials.py --username newadmin --password newpass
   ```
3. **Update secrets.env:**
   ```bash
   UNIFI_USERNAME=newadmin
   UNIFI_PASSWORD=newpass
   ```
4. **Invalidate old sessions:**
   ```bash
   # Use MCP tool
   invalidate_session()
   ```
5. **Restart server**
6. **Disable old admin user** after 24 hours

### Emergency Credential Revocation

If credentials are compromised:

1. **Immediately revoke in UniFi controller:**
   - Delete API key
   - Disable/delete admin user
   - Force logout all sessions

2. **Invalidate all server sessions:**
   ```bash
   # Use MCP tool
   invalidate_session()
   ```

3. **Generate new credentials** following rotation procedure

4. **Audit logs** for unauthorized access:
   ```bash
   grep "AUDIT" unifi_mcp_audit.log | grep -i "login\|auth"
   ```

5. **Rotate other credentials** if cross-contamination suspected

---

## Session Management

### Legacy Session Behavior

Legacy cookie-based authentication includes automatic session management:

- **Session Timeout:** Configured via `UNIFI_SESSION_TIMEOUT_S` (default: 3600s / 1 hour)
- **Auto-Refresh:** Sessions refresh at 80% of timeout (default: 48 minutes)
- **Thread-Safe:** All session operations are protected by locks
- **Audit Logging:** All auth events logged to audit log

### Checking Session Status

```python
# Use MCP tool
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
```

### Manually Invalidating Sessions

```python
# Use MCP tool
invalidate_session()

# Returns:
{
  "success": true,
  "message": "Legacy session invalidated successfully. Next request will re-authenticate."
}
```

### Session Configuration

In `secrets.env`:

```bash
# Session timeout in seconds (default: 3600 = 1 hour)
UNIFI_SESSION_TIMEOUT_S=3600

# Shorter timeout for high-security environments
# UNIFI_SESSION_TIMEOUT_S=900  # 15 minutes

# Longer timeout for development
# UNIFI_SESSION_TIMEOUT_S=7200  # 2 hours
```

**Recommendations:**
- **Production:** 1800-3600 seconds (30-60 minutes)
- **High-security:** 900-1800 seconds (15-30 minutes)
- **Development:** 3600-7200 seconds (1-2 hours)
- **Minimum:** 60 seconds (enforced by validation)

---

## Rate Limiting

### Configuration

```bash
# In secrets.env
UNIFI_RATE_LIMIT_PER_MINUTE=60    # Max 60 requests per minute
UNIFI_RATE_LIMIT_PER_HOUR=1000    # Max 1000 requests per hour
```

### Checking Rate Limit Status

```python
# Use MCP tool
get_rate_limit_stats("global")

# Returns stats for all endpoints
get_rate_limit_stats("/sites")

# Returns stats for specific endpoint
```

### Rate Limit Best Practices

- **Default limits:** Suitable for most use cases
- **Increase for batch operations:** Temporarily increase during bulk operations
- **Monitor usage:** Check stats regularly to avoid hitting limits
- **Handle errors gracefully:** Implement retry logic with exponential backoff

---

## Logging and Auditing

### Audit Log

All security-relevant events are logged to `unifi_mcp_audit.log`:

- Authentication attempts (success/failure)
- Session creation/invalidation
- API requests (method, endpoint, params)
- Rate limit violations
- Configuration errors
- TLS verification warnings

### Sensitive Data Redaction

The server automatically redacts sensitive data from logs:
- API keys
- Passwords
- Tokens
- Session cookies
- Authorization headers

### Log Configuration

```bash
# In secrets.env
UNIFI_LOG_LEVEL=INFO              # DEBUG, INFO, WARNING, ERROR, CRITICAL
UNIFI_LOG_TO_FILE=true            # Enable file logging
UNIFI_LOG_FILE=unifi_mcp_audit.log
```

### Reviewing Audit Logs

```bash
# View recent auth events
grep "AUDIT" unifi_mcp_audit.log | grep "auth\|login" | tail -20

# View failed requests
grep "AUDIT" unifi_mcp_audit.log | grep '"success": false'

# View rate limit violations
grep "rate_limit_exceeded" unifi_mcp_audit.log

# View session events
grep "legacy_session" unifi_mcp_audit.log
```

---

## TLS Configuration

### Production: Enable TLS Verification

```bash
# In secrets.env
UNIFI_VERIFY_TLS=true
```

**Requirements:**
- Valid TLS certificate on UniFi controller
- Certificate signed by trusted CA
- Or: Add self-signed cert to system trust store

### Development: Self-Signed Certificates

```bash
# In secrets.env
UNIFI_VERIFY_TLS=false
```

**Warning:** Disabling TLS verification exposes you to man-in-the-middle attacks. Only use in trusted networks.

### Adding Self-Signed Certificate to Trust Store

#### macOS:
```bash
# Download certificate
openssl s_client -connect 192.168.1.1:443 -showcerts < /dev/null | openssl x509 -outform PEM > unifi.crt

# Add to keychain
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain unifi.crt
```

#### Linux:
```bash
# Copy certificate
sudo cp unifi.crt /usr/local/share/ca-certificates/

# Update trust store
sudo update-ca-certificates
```

---

## Security Hardening Checklist

### Initial Setup

- [ ] Generate unique API key for production
- [ ] Set strong admin password (16+ chars, mixed case, numbers, symbols)
- [ ] Configure `secrets.env` with appropriate permissions (`chmod 600`)
- [ ] Enable TLS verification (`UNIFI_VERIFY_TLS=true`)
- [ ] Set appropriate session timeout (30-60 minutes)
- [ ] Configure reasonable rate limits
- [ ] Enable audit logging (`UNIFI_LOG_TO_FILE=true`)

### Regular Maintenance

- [ ] Rotate API key every 90 days
- [ ] Review audit logs weekly
- [ ] Update dependencies monthly (`uv pip install --upgrade`)
- [ ] Run security scans before releases
- [ ] Monitor rate limit usage
- [ ] Check for session anomalies

### Before Production Deployment

- [ ] Test all credentials with `test_credentials.py`
- [ ] Run security scans (Bandit + Safety)
- [ ] Review audit log configuration
- [ ] Verify TLS settings
- [ ] Validate environment configuration
- [ ] Document credential rotation procedures
- [ ] Set up secrets manager integration
- [ ] Configure monitoring/alerting

### Incident Response

If security incident detected:

1. **Isolate:** Stop server immediately
2. **Revoke:** Disable all API keys and admin accounts
3. **Analyze:** Review audit logs for unauthorized access
4. **Rotate:** Generate new credentials
5. **Verify:** Test new credentials
6. **Redeploy:** Restart with new credentials
7. **Monitor:** Watch logs for 24 hours
8. **Document:** Record incident and response

---

## Additional Resources

- [UniFi Controller API Documentation](https://ubntwiki.com/products/software/unifi-controller/api)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)
- [NIST Password Guidelines](https://pages.nist.gov/800-63-3/)

---

## Support and Reporting

For security vulnerabilities:
- **DO NOT** open public GitHub issues
- Report privately to maintainers
- Include detailed reproduction steps
- Allow reasonable time for fix before disclosure
