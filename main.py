# main.py
# UniFi MCP Server – Integration + Legacy + Access + Protect (+ Site Manager stubs)
# - Rich resources for reads, curated tools for safe actions, prompt playbooks
# - Dual-mode auth (API key first; fall back to legacy cookie where needed)
# - Includes health alias (health://unifi) and debug_registry tool
# - Safer URL building to avoid line-wrap identifier breaks

from typing import Any, Dict, List, Optional
import os, json, requests, urllib3, time, threading, logging
from pathlib import Path
from mcp.server.fastmcp import FastMCP
from collections import defaultdict, deque
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ========= Load Environment Variables from secrets.env =========
def load_env_file(env_file: str = "secrets.env") -> None:
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

# ========= Environment Variable Validation =========
class ConfigurationError(Exception):
    """Raised when environment configuration is invalid."""
    pass

def validate_environment_config() -> Dict[str, Any]:
    """
    Validate all environment variables at startup.
    Returns dict of validated config or raises ConfigurationError.
    """
    errors = []
    warnings = []

    # Validate UNIFI_HOST
    host = os.getenv("UNIFI_GATEWAY_HOST", "")
    if not host or host == "HOST":
        errors.append("UNIFI_GATEWAY_HOST is required and must be set to your UniFi controller IP or hostname")
    else:
        # Basic hostname/IP validation
        import re
        # Allow IPv4, IPv6, or hostname
        ipv4_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        ipv6_pattern = r'^([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}$'
        hostname_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'

        if not (re.match(ipv4_pattern, host) or re.match(ipv6_pattern, host) or re.match(hostname_pattern, host)):
            errors.append(f"UNIFI_GATEWAY_HOST has invalid format: {host}")
        elif re.match(ipv4_pattern, host):
            # Validate IPv4 octets are 0-255
            octets = [int(x) for x in host.split('.')]
            if not all(0 <= octet <= 255 for octet in octets):
                errors.append(f"UNIFI_GATEWAY_HOST has invalid IPv4 address: {host}")

    # Validate UNIFI_PORT
    port_str = os.getenv("UNIFI_GATEWAY_PORT", "443")
    try:
        port = int(port_str)
        if port < 1 or port > 65535:
            errors.append(f"UNIFI_GATEWAY_PORT must be between 1 and 65535, got: {port}")
    except ValueError:
        errors.append(f"UNIFI_GATEWAY_PORT must be a valid integer, got: {port_str}")

    # Validate UNIFI_API_KEY
    api_key = os.getenv("UNIFI_API_KEY", "")
    if not api_key or api_key == "API":
        warnings.append("UNIFI_API_KEY not set - Integration API calls will fail. Set this for API key authentication.")
    elif len(api_key) < 10:
        warnings.append(f"UNIFI_API_KEY seems too short ({len(api_key)} chars) - may be invalid")

    # Validate timeout
    timeout_str = os.getenv("UNIFI_TIMEOUT_S", "15")
    try:
        timeout = int(timeout_str)
        if timeout < 1:
            errors.append(f"UNIFI_TIMEOUT_S must be positive, got: {timeout}")
        elif timeout > 300:
            warnings.append(f"UNIFI_TIMEOUT_S is very high ({timeout}s) - may cause long waits")
    except ValueError:
        errors.append(f"UNIFI_TIMEOUT_S must be a valid integer, got: {timeout_str}")

    # Validate rate limits
    rate_minute_str = os.getenv("UNIFI_RATE_LIMIT_PER_MINUTE", "60")
    try:
        rate_minute = int(rate_minute_str)
        if rate_minute < 1:
            errors.append(f"UNIFI_RATE_LIMIT_PER_MINUTE must be positive, got: {rate_minute}")
        elif rate_minute > 1000:
            warnings.append(f"UNIFI_RATE_LIMIT_PER_MINUTE is very high ({rate_minute}) - may stress controller")
    except ValueError:
        errors.append(f"UNIFI_RATE_LIMIT_PER_MINUTE must be a valid integer, got: {rate_minute_str}")

    rate_hour_str = os.getenv("UNIFI_RATE_LIMIT_PER_HOUR", "1000")
    try:
        rate_hour = int(rate_hour_str)
        if rate_hour < 1:
            errors.append(f"UNIFI_RATE_LIMIT_PER_HOUR must be positive, got: {rate_hour}")
        elif rate_hour > 100000:
            warnings.append(f"UNIFI_RATE_LIMIT_PER_HOUR is very high ({rate_hour}) - may stress controller")
    except ValueError:
        errors.append(f"UNIFI_RATE_LIMIT_PER_HOUR must be a valid integer, got: {rate_hour_str}")

    # Validate TLS setting
    verify_tls_str = os.getenv("UNIFI_VERIFY_TLS", "true").lower()
    if verify_tls_str not in ("1", "true", "yes", "0", "false", "no"):
        warnings.append(f"UNIFI_VERIFY_TLS has unexpected value: {verify_tls_str} (using default: true)")

    # Validate log level
    log_level = os.getenv("UNIFI_LOG_LEVEL", "INFO").upper()
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if log_level not in valid_levels:
        warnings.append(f"UNIFI_LOG_LEVEL has invalid value: {log_level} (using INFO). Valid: {', '.join(valid_levels)}")

    # Validate legacy credentials (if provided)
    legacy_user = os.getenv("UNIFI_USERNAME", "")
    legacy_pass = os.getenv("UNIFI_PASSWORD", "")
    if (legacy_user and not legacy_pass) or (legacy_pass and not legacy_user):
        warnings.append("Legacy auth partially configured - both UNIFI_USERNAME and UNIFI_PASSWORD required for legacy API")
    if legacy_user == "USERNAME" or legacy_pass == "PASSWORD":
        warnings.append("Legacy credentials appear to be placeholder values - update with real credentials")

    # Validate session timeout (new parameter for Week 3)
    session_timeout_str = os.getenv("UNIFI_SESSION_TIMEOUT_S", "3600")
    try:
        session_timeout = int(session_timeout_str)
        if session_timeout < 60:
            errors.append(f"UNIFI_SESSION_TIMEOUT_S must be >= 60 seconds, got: {session_timeout}")
        elif session_timeout > 86400:
            warnings.append(f"UNIFI_SESSION_TIMEOUT_S is very high ({session_timeout}s = {session_timeout/3600:.1f}h)")
    except ValueError:
        errors.append(f"UNIFI_SESSION_TIMEOUT_S must be a valid integer, got: {session_timeout_str}")

    # Report errors and warnings
    if errors:
        error_msg = "Environment configuration errors:\n" + "\n".join(f"  - {e}" for e in errors)
        raise ConfigurationError(error_msg)

    if warnings:
        print("⚠️  Environment configuration warnings:")
        for w in warnings:
            print(f"  - {w}")

    print("✅ Environment configuration validated successfully")
    return {
        "host": host,
        "port": int(port_str),
        "timeout": int(timeout_str),
        "rate_limit_per_minute": int(rate_minute_str),
        "rate_limit_per_hour": int(rate_hour_str),
        "verify_tls": verify_tls_str in ("1", "true", "yes"),
        "log_level": log_level,
        "session_timeout": int(session_timeout_str)
    }

# Validate configuration at startup
try:
    validated_config = validate_environment_config()
except ConfigurationError as e:
    print(f"❌ Configuration validation failed:\n{e}")
    print("\nPlease fix the errors in your secrets.env file and try again.")
    import sys
    sys.exit(1)

# ========= Logging Configuration =========
LOG_LEVEL = os.getenv("UNIFI_LOG_LEVEL", "INFO").upper()
LOG_FILE = os.getenv("UNIFI_LOG_FILE", "unifi_mcp_audit.log")
LOG_TO_FILE = os.getenv("UNIFI_LOG_TO_FILE", "true").lower() in ("1", "true", "yes")

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ] if not LOG_TO_FILE else [
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE)
    ]
)

logger = logging.getLogger("unifi-mcp")

# Sensitive fields to redact from logs
SENSITIVE_FIELDS = {
    "password", "api_key", "token", "secret", "apiKey", "apikey",
    "authorization", "x-api-key", "csrf-token", "session", "cookie"
}

def sanitize_for_logging(data: Any, depth: int = 0) -> Any:
    """
    Recursively sanitize sensitive data from logs.
    Redacts passwords, API keys, tokens, and other sensitive fields.
    """
    if depth > 10:  # Prevent deep recursion
        return "[MAX_DEPTH_REACHED]"

    if isinstance(data, dict):
        sanitized = {}
        for key, value in data.items():
            key_lower = str(key).lower()
            if any(sensitive in key_lower for sensitive in SENSITIVE_FIELDS):
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = sanitize_for_logging(value, depth + 1)
        return sanitized
    elif isinstance(data, list):
        return [sanitize_for_logging(item, depth + 1) for item in data]
    elif isinstance(data, str) and len(data) > 1000:
        return f"{data[:100]}...[TRUNCATED {len(data)} chars]"
    else:
        return data

def audit_log(action: str, details: Dict[str, Any], success: bool = True, error: Optional[str] = None) -> None:
    """
    Log auditable actions with sanitized details.
    """
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "action": action,
        "success": success,
        "details": sanitize_for_logging(details)
    }
    if error:
        log_entry["error"] = str(error)

    if success:
        logger.info(f"AUDIT: {json.dumps(log_entry)}")
    else:
        logger.warning(f"AUDIT: {json.dumps(log_entry)}")

# ========= Rate Limiting =========
class RateLimiter:
    """
    Token bucket rate limiter for API calls.
    Prevents API abuse and DoS attacks against UniFi controller.
    """
    def __init__(self, calls_per_minute: int, calls_per_hour: int):
        self.calls_per_minute = calls_per_minute
        self.calls_per_hour = calls_per_hour
        # Use deque for O(1) append and popleft operations
        self.minute_calls: Dict[str, deque] = defaultdict(lambda: deque())
        self.hour_calls: Dict[str, deque] = defaultdict(lambda: deque())
        self.lock = threading.Lock()

    def _cleanup_old_calls(self, endpoint: str) -> None:
        """Remove calls older than the time window - optimized with deque."""
        now = time.time()

        # Efficiently remove old calls from the left of deque (oldest first)
        minute_queue = self.minute_calls[endpoint]
        while minute_queue and now - minute_queue[0] >= 60:
            minute_queue.popleft()

        hour_queue = self.hour_calls[endpoint]
        while hour_queue and now - hour_queue[0] >= 3600:
            hour_queue.popleft()

    def check_rate_limit(self, endpoint: str) -> tuple[bool, Optional[str]]:
        """
        Check if the request is within rate limits.
        Returns: (allowed: bool, error_message: Optional[str])
        """
        with self.lock:
            self._cleanup_old_calls(endpoint)

            minute_count = len(self.minute_calls[endpoint])
            hour_count = len(self.hour_calls[endpoint])

            if minute_count >= self.calls_per_minute:
                if self.minute_calls[endpoint]:  # Check if list is not empty
                    wait_time = 60 - (time.time() - self.minute_calls[endpoint][0])
                else:
                    wait_time = 60
                return False, f"Rate limit exceeded: {self.calls_per_minute} calls/minute. Retry in {wait_time:.1f}s"

            if hour_count >= self.calls_per_hour:
                if self.hour_calls[endpoint]:  # Check if list is not empty
                    wait_time = 3600 - (time.time() - self.hour_calls[endpoint][0])
                else:
                    wait_time = 3600
                return False, f"Rate limit exceeded: {self.calls_per_hour} calls/hour. Retry in {wait_time:.1f}s"

            # Record this call
            now = time.time()
            self.minute_calls[endpoint].append(now)
            self.hour_calls[endpoint].append(now)

            return True, None

    def get_stats(self, endpoint: str) -> Dict[str, Any]:
        """Get current rate limit statistics for an endpoint."""
        with self.lock:
            self._cleanup_old_calls(endpoint)
            return {
                "endpoint": endpoint,
                "calls_last_minute": len(self.minute_calls[endpoint]),
                "calls_last_hour": len(self.hour_calls[endpoint]),
                "limit_per_minute": self.calls_per_minute,
                "limit_per_hour": self.calls_per_hour,
                "minute_remaining": self.calls_per_minute - len(self.minute_calls[endpoint]),
                "hour_remaining": self.calls_per_hour - len(self.hour_calls[endpoint])
            }

# Initialize rate limiter with configurable limits
RATE_LIMIT_PER_MINUTE = int(os.getenv("UNIFI_RATE_LIMIT_PER_MINUTE", "60"))
RATE_LIMIT_PER_HOUR = int(os.getenv("UNIFI_RATE_LIMIT_PER_HOUR", "1000"))
rate_limiter = RateLimiter(RATE_LIMIT_PER_MINUTE, RATE_LIMIT_PER_HOUR)

# Rate limit error exception
class RateLimitError(RuntimeError):
    pass

# ========= Configuration =========
UNIFI_API_KEY   = os.getenv("UNIFI_API_KEY", "API")
UNIFI_HOST      = os.getenv("UNIFI_GATEWAY_HOST", "HOST")
UNIFI_PORT      = os.getenv("UNIFI_GATEWAY_PORT", "443")

# TLS Verification - NOW ENABLED BY DEFAULT for security
# Set UNIFI_VERIFY_TLS=false explicitly to disable (not recommended for production)
VERIFY_TLS = os.getenv("UNIFI_VERIFY_TLS", "true").lower() in ("1", "true", "yes")

if not VERIFY_TLS:
    logger.warning(
        "⚠️  TLS CERTIFICATE VERIFICATION IS DISABLED! ⚠️\n"
        "   This makes your connection vulnerable to man-in-the-middle attacks.\n"
        "   Only use UNIFI_VERIFY_TLS=false in trusted networks with self-signed certificates.\n"
        "   For production, use valid certificates or add self-signed cert to system trust store."
    )
    audit_log("tls_verification_disabled", {
        "host": UNIFI_HOST,
        "port": UNIFI_PORT,
        "warning": "TLS verification disabled - security risk"
    }, success=True)

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

def sanitize_error_message(error_msg: str, response: requests.Response) -> str:
    """
    Sanitize error messages to prevent information disclosure.
    Removes sensitive data like API keys, tokens, passwords from error output.
    """
    sanitized = error_msg

    # Redact common sensitive patterns
    import re
    patterns = [
        # API keys and tokens in URLs or headers
        (r'(api[_-]?key|apikey)[=:]\s*[^\s&]+', r'\1=[REDACTED]'),
        (r'(password|passwd|pwd)[=:]\s*[^\s&]+', r'\1=[REDACTED]'),

        # Authorization headers - capture everything after the header name
        (r'(Authorization:\s+Bearer\s+)[^\s,;]+', r'\1[REDACTED]'),
        (r'(Authorization:\s+Basic\s+)[^\s,;]+', r'\1[REDACTED]'),
        (r'(Authorization:\s+)[^\s,;]+', r'\1[REDACTED]'),

        # X-API-Key header
        (r'(X-API-Key:\s+)[^\s,;]+', r'\1[REDACTED]'),

        # Token parameters
        (r'(token|auth)[=:]\s*[^\s&,;]+', r'\1=[REDACTED]'),
    ]

    for pattern, replacement in patterns:
        sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)

    # Limit body size to prevent massive error dumps
    if len(sanitized) > 500:
        sanitized = sanitized[:500] + "...[TRUNCATED]"

    return sanitized

def _raise_for(r: requests.Response) -> Dict[str, Any]:
    try:
        r.raise_for_status()
        return r.json() if r.text.strip() else {}
    except requests.exceptions.HTTPError as e:
        body = (r.text or "")[:800]
        error_msg = f"{r.request.method} {r.url} -> {r.status_code} {r.reason}; body: {body}"
        sanitized_error = sanitize_error_message(error_msg, r)

        # Audit log the error
        audit_log("http_error", {
            "method": r.request.method,
            "url": str(r.url),
            "status_code": r.status_code,
            "reason": r.reason
        }, success=False, error=sanitized_error)

        raise UniFiHTTPError(sanitized_error) from e

def _h_key() -> Dict[str, str]:
    return {"X-API-Key": UNIFI_API_KEY, "Content-Type": "application/json"}

def _get(url: str, headers: Dict[str, str], params: Optional[Dict[str, Any]] = None, timeout: int = REQUEST_TIMEOUT_S) -> Dict[str, Any]:
    # Extract endpoint for rate limiting (use path without query params)
    from urllib.parse import urlparse
    parsed = urlparse(url)
    endpoint = parsed.path

    # Check rate limit
    allowed, error_msg = rate_limiter.check_rate_limit(endpoint)
    if not allowed:
        audit_log("rate_limit_exceeded", {
            "endpoint": endpoint,
            "method": "GET",
            "error": error_msg
        }, success=False, error=error_msg)
        raise RateLimitError(error_msg)

    # Audit log the request
    audit_log("api_request", {
        "method": "GET",
        "endpoint": endpoint,
        "params": sanitize_for_logging(params) if params else None
    }, success=True)

    try:
        result = _raise_for(requests.get(url, headers=headers, params=params, verify=VERIFY_TLS, timeout=timeout))
        # Audit log success
        audit_log("api_response", {
            "method": "GET",
            "endpoint": endpoint,
            "status": "success"
        }, success=True)
        return result
    except Exception as e:
        # Error already logged in _raise_for
        raise

def _post(url: str, headers: Dict[str, str], body: Optional[Dict[str, Any]] = None, timeout: int = REQUEST_TIMEOUT_S) -> Dict[str, Any]:
    # Extract endpoint for rate limiting
    from urllib.parse import urlparse
    parsed = urlparse(url)
    endpoint = parsed.path

    # Check rate limit
    allowed, error_msg = rate_limiter.check_rate_limit(endpoint)
    if not allowed:
        audit_log("rate_limit_exceeded", {
            "endpoint": endpoint,
            "method": "POST",
            "error": error_msg
        }, success=False, error=error_msg)
        raise RateLimitError(error_msg)

    # Audit log the request (with sanitized body)
    audit_log("api_request", {
        "method": "POST",
        "endpoint": endpoint,
        "body": sanitize_for_logging(body) if body else None
    }, success=True)

    try:
        result = _raise_for(requests.post(url, headers=headers, json=body, verify=VERIFY_TLS, timeout=timeout))
        # Audit log success
        audit_log("api_response", {
            "method": "POST",
            "endpoint": endpoint,
            "status": "success"
        }, success=True)
        return result
    except Exception as e:
        # Error already logged in _raise_for
        raise

# ========= Legacy Session Management with Timeout/Refresh =========
class LegacySessionManager:
    """
    Manages legacy cookie-based authentication with session timeout and refresh.
    Tracks session age and automatically refreshes before expiration.
    """
    def __init__(self, session_timeout_s: int = 3600):
        self.session = requests.Session()
        self.session_timeout_s = session_timeout_s
        self.session_created_at: Optional[float] = None
        self.session_last_used: Optional[float] = None
        self.lock = threading.Lock()

    def is_session_valid(self) -> bool:
        """Check if current session is valid (not expired)."""
        if not self.session.cookies:
            return False
        if self.session_created_at is None:
            return False

        now = time.time()
        age = now - self.session_created_at

        # Check if session has exceeded timeout
        if age >= self.session_timeout_s:
            logger.info(f"Legacy session expired (age: {age:.0f}s, timeout: {self.session_timeout_s}s)")
            return False

        return True

    def should_refresh(self) -> bool:
        """Check if session should be refreshed (approaching expiration)."""
        if not self.session_created_at:
            return False

        now = time.time()
        age = now - self.session_created_at
        # Refresh when 80% of timeout has elapsed
        refresh_threshold = self.session_timeout_s * 0.8

        return age >= refresh_threshold

    def login(self, force: bool = False) -> None:
        """
        Perform legacy cookie authentication.
        Args:
            force: Force re-authentication even if session appears valid
        """
        with self.lock:
            # Skip if session is still valid and not forcing
            if not force and self.is_session_valid():
                logger.debug("Legacy session still valid, skipping login")
                return

            if not (LEGACY_USER and LEGACY_PASS):
                raise UniFiHTTPError("Legacy login requires UNIFI_USERNAME and UNIFI_PASSWORD.")

            logger.info("Performing legacy cookie authentication")
            audit_log("legacy_login_attempt", {
                "host": UNIFI_HOST,
                "user": LEGACY_USER,
                "force": force
            }, success=True)

            try:
                r = self.session.post(
                    f"https://{UNIFI_HOST}:{UNIFI_PORT}/api/auth/login",
                    json={"username": LEGACY_USER, "password": LEGACY_PASS},
                    verify=VERIFY_TLS,
                    timeout=REQUEST_TIMEOUT_S,
                )
                _raise_for(r)

                # Update session timestamps
                now = time.time()
                self.session_created_at = now
                self.session_last_used = now

                logger.info(f"Legacy authentication successful (timeout: {self.session_timeout_s}s)")
                audit_log("legacy_login_success", {
                    "host": UNIFI_HOST,
                    "session_timeout": self.session_timeout_s,
                    "expires_at": datetime.fromtimestamp(now + self.session_timeout_s).isoformat()
                }, success=True)

            except Exception as e:
                logger.error(f"Legacy authentication failed: {e}")
                audit_log("legacy_login_failed", {
                    "host": UNIFI_HOST,
                    "error": str(e)
                }, success=False, error=str(e))
                raise

    def refresh_if_needed(self) -> None:
        """Refresh session if approaching expiration."""
        if self.should_refresh():
            logger.info("Legacy session approaching expiration, refreshing...")
            self.login(force=True)

    def invalidate(self) -> None:
        """Invalidate the current session."""
        with self.lock:
            self.session.cookies.clear()
            self.session_created_at = None
            self.session_last_used = None
            logger.info("Legacy session invalidated")
            audit_log("legacy_session_invalidated", {}, success=True)

    def get_session_info(self) -> Dict[str, Any]:
        """Get information about the current session."""
        if not self.session_created_at:
            return {
                "active": False,
                "message": "No active session"
            }

        now = time.time()
        age = now - self.session_created_at
        remaining = self.session_timeout_s - age

        return {
            "active": self.is_session_valid(),
            "created_at": datetime.fromtimestamp(self.session_created_at).isoformat(),
            "age_seconds": int(age),
            "timeout_seconds": self.session_timeout_s,
            "remaining_seconds": int(remaining) if remaining > 0 else 0,
            "expires_at": datetime.fromtimestamp(self.session_created_at + self.session_timeout_s).isoformat(),
            "should_refresh": self.should_refresh()
        }

# Initialize legacy session manager with configured timeout
SESSION_TIMEOUT_S = int(os.getenv("UNIFI_SESSION_TIMEOUT_S", "3600"))
LEGACY = LegacySessionManager(session_timeout_s=SESSION_TIMEOUT_S)

def legacy_login() -> None:
    """Legacy login wrapper for backward compatibility."""
    LEGACY.login()

def legacy_get(path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Perform GET request with legacy cookie auth.
    Automatically refreshes session if needed.
    """
    # Check if session needs refresh before making request
    LEGACY.refresh_if_needed()

    # Ensure we have a valid session
    if not LEGACY.is_session_valid():
        LEGACY.login()

    r = LEGACY.session.get(f"{LEGACY_BASE}{path}", params=params, verify=VERIFY_TLS, timeout=REQUEST_TIMEOUT_S)
    return _raise_for(r)

def legacy_post(path: str, body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Perform POST request with legacy cookie auth.
    Automatically refreshes session if needed.
    """
    # Check if session needs refresh before making request
    LEGACY.refresh_if_needed()

    # Ensure we have a valid session
    if not LEGACY.is_session_valid():
        LEGACY.login()

    r = LEGACY.session.post(f"{LEGACY_BASE}{path}", json=body, verify=VERIFY_TLS, timeout=REQUEST_TIMEOUT_S)
    return _raise_for(r)

# ========= UniFi Protect helpers =========
def protect_get(path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Try API key first; if unauthorized, fall back to legacy cookie session.
    """
    try:
        r = requests.get(f"{PROTECT_BASE}{path}", headers=_h_key(), params=params, verify=VERIFY_TLS, timeout=REQUEST_TIMEOUT_S)
        if r.status_code == 200:
            return _raise_for(r)
        if r.status_code not in (401, 403):
            return _raise_for(r)
    except Exception:  # nosec B110 - Intentional fallback to legacy auth
        pass  # fall back

    # Fallback to legacy session with auto-refresh
    LEGACY.refresh_if_needed()
    if not LEGACY.is_session_valid():
        LEGACY.login()

    r = LEGACY.session.get(f"{PROTECT_BASE}{path}", params=params, verify=VERIFY_TLS, timeout=REQUEST_TIMEOUT_S)
    return _raise_for(r)

def protect_post(path: str, body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    try:
        r = requests.post(f"{PROTECT_BASE}{path}", headers=_h_key(), json=body, verify=VERIFY_TLS, timeout=REQUEST_TIMEOUT_S)
        if r.status_code in (200, 204):
            return _raise_for(r)
        if r.status_code not in (401, 403):
            return _raise_for(r)
    except Exception:  # nosec B110 - Intentional fallback to legacy auth
        pass

    # Fallback to legacy session with auto-refresh
    LEGACY.refresh_if_needed()
    if not LEGACY.is_session_valid():
        LEGACY.login()

    r = LEGACY.session.post(f"{PROTECT_BASE}{path}", json=body, verify=VERIFY_TLS, timeout=REQUEST_TIMEOUT_S)
    return _raise_for(r)

# ========= UniFi Health (triple-registered) =========

def _health_check() -> Dict[str, Any]:
    """
    Minimal controller sanity check against Integration API.
    Returns ok: True with sites count, or ok: False with error.
    Also validates credentials and session status.
    """
    result: Dict[str, Any] = {
        "base": NET_INTEGRATION_BASE,
        "verify_tls": VERIFY_TLS,
        "credentials": {}
    }

    # Check Integration API (API key authentication)
    try:
        resp = _get("/".join([NET_INTEGRATION_BASE, "sites"]), _h_key())
        result["ok"] = True
        result["integration_sites_count"] = resp.get("count")
        result["credentials"]["api_key"] = {
            "configured": bool(UNIFI_API_KEY and UNIFI_API_KEY != "API"),
            "valid": True
        }
    except Exception as e:
        result["ok"] = False
        result["error"] = str(e)
        result["credentials"]["api_key"] = {
            "configured": bool(UNIFI_API_KEY and UNIFI_API_KEY != "API"),
            "valid": False,
            "error": str(e)
        }

    # Check legacy credentials if configured
    if LEGACY_USER and LEGACY_PASS and LEGACY_USER != "USERNAME":
        try:
            # Try legacy authentication
            LEGACY.login(force=True)
            session_info = LEGACY.get_session_info()
            result["credentials"]["legacy"] = {
                "configured": True,
                "valid": session_info.get("active", False),
                "session": session_info
            }
        except Exception as e:
            result["credentials"]["legacy"] = {
                "configured": True,
                "valid": False,
                "error": str(e)
            }
    else:
        result["credentials"]["legacy"] = {
            "configured": False,
            "valid": None
        }

    return result

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

# Tool fallback (always visible in Tools tab)
@mcp.tool()
def unifi_health() -> Dict[str, Any]:
    """Ping the UniFi Integration API and report basic health."""
    return _health_check()

# Prompt so agents know how to call it
@mcp.prompt("how_to_check_unifi_health")
def how_to_check_unifi_health() -> Dict[str, Any]:
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

# ========= Input Validation =========
class ValidationError(ValueError):
    """Raised when input validation fails."""
    pass

def validate_site_id(site_id: str) -> str:
    """
    Validate site ID format.
    Site IDs must be alphanumeric with hyphens/underscores, 1-64 chars.
    """
    if not isinstance(site_id, str):
        raise ValidationError(f"site_id must be string, got {type(site_id).__name__}")
    if not site_id:
        raise ValidationError("site_id cannot be empty")
    if len(site_id) > 64:
        raise ValidationError(f"site_id too long: {len(site_id)} chars (max 64)")
    if not all(c.isalnum() or c in ('-', '_') for c in site_id):
        raise ValidationError(f"site_id contains invalid characters: {site_id}")
    return site_id

def validate_mac_address(mac: str) -> str:
    """
    Validate MAC address format.
    Accepts formats: AA:BB:CC:DD:EE:FF, aa:bb:cc:dd:ee:ff, aa-bb-cc-dd-ee-ff, aabbccddeeff
    """
    if not mac:
        raise ValidationError("MAC address cannot be empty")
    if not isinstance(mac, str):
        raise ValidationError(f"MAC address must be string, got {type(mac).__name__}")

    # Remove common separators
    clean_mac = mac.replace(':', '').replace('-', '').replace('.', '')

    if len(clean_mac) != 12:
        raise ValidationError(f"Invalid MAC address length: {mac}")
    if not all(c in '0123456789abcdefABCDEF' for c in clean_mac):
        raise ValidationError(f"Invalid MAC address format: {mac}")

    return mac.lower()

def validate_device_id(device_id: str) -> str:
    """
    Validate device ID format.
    Device IDs are typically 24-char hex strings (MongoDB ObjectId format).
    """
    if not device_id:
        raise ValidationError("device_id cannot be empty")
    if not isinstance(device_id, str):
        raise ValidationError(f"device_id must be string, got {type(device_id).__name__}")
    if len(device_id) < 6 or len(device_id) > 64:
        raise ValidationError(f"device_id length invalid: {len(device_id)} chars")
    if not all(c.isalnum() or c in ('-', '_') for c in device_id):
        raise ValidationError(f"device_id contains invalid characters: {device_id}")
    return device_id

def validate_door_id(door_id: str) -> str:
    """
    Validate door ID format.
    """
    if not door_id:
        raise ValidationError("door_id cannot be empty")
    if not isinstance(door_id, str):
        raise ValidationError(f"door_id must be string, got {type(door_id).__name__}")
    if len(door_id) > 64:
        raise ValidationError(f"door_id too long: {len(door_id)} chars")
    if not all(c.isalnum() or c in ('-', '_') for c in door_id):
        raise ValidationError(f"door_id contains invalid characters: {door_id}")
    return door_id

def validate_camera_id(camera_id: str) -> str:
    """
    Validate camera ID format.
    """
    if not camera_id:
        raise ValidationError("camera_id cannot be empty")
    if not isinstance(camera_id, str):
        raise ValidationError(f"camera_id must be string, got {type(camera_id).__name__}")
    if len(camera_id) > 64:
        raise ValidationError(f"camera_id too long: {len(camera_id)} chars")
    if not all(c.isalnum() or c in ('-', '_') for c in camera_id):
        raise ValidationError(f"camera_id contains invalid characters: {camera_id}")
    return camera_id

def validate_wlan_id(wlan_id: str) -> str:
    """
    Validate WLAN ID format.
    """
    if not wlan_id:
        raise ValidationError("wlan_id cannot be empty")
    if not isinstance(wlan_id, str):
        raise ValidationError(f"wlan_id must be string, got {type(wlan_id).__name__}")
    if len(wlan_id) > 64:
        raise ValidationError(f"wlan_id too long: {len(wlan_id)} chars")
    if not all(c.isalnum() or c in ('-', '_') for c in wlan_id):
        raise ValidationError(f"wlan_id contains invalid characters: {wlan_id}")
    return wlan_id

def validate_duration(seconds: int, min_val: int = 1, max_val: int = 300) -> int:
    """
    Validate duration/timeout values.
    Default: 1-300 seconds (5 minutes max)
    """
    if not isinstance(seconds, int):
        try:
            seconds = int(seconds)  # type: ignore[arg-type]
        except (ValueError, TypeError):
            raise ValidationError(f"Duration must be integer, got {type(seconds).__name__}")

    if seconds < min_val:
        raise ValidationError(f"Duration too short: {seconds}s (minimum {min_val}s)")
    if seconds > max_val:
        raise ValidationError(f"Duration too long: {seconds}s (maximum {max_val}s)")

    return seconds

def validate_boolean(value: Any, param_name: str = "value") -> bool:
    """
    Validate boolean parameters with type coercion.
    Accepts bool, str, or int and coerces to bool.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        if value.lower() in ('true', '1', 'yes', 'on'):
            return True
        if value.lower() in ('false', '0', 'no', 'off'):
            return False
    if isinstance(value, int):
        return bool(value)

    raise ValidationError(f"{param_name} must be boolean, got {type(value).__name__}: {value}")

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
    try_get("integration.devices_default", "/".join([NET_INTEGRATION_BASE, "sites", "default", "devices"]), _h_key())
    try_get("integration.clients_default", "/".join([NET_INTEGRATION_BASE, "sites", "default", "clients"]), _h_key())
    try_get("integration.wlans_default", "/".join([NET_INTEGRATION_BASE, "sites", "default", "wlans"]), _h_key())

    # Access
    try_get("access.doors", "/".join([ACCESS_BASE, "doors"]), _h_key())
    try_get("access.readers", "/".join([ACCESS_BASE, "readers"]), _h_key())
    try_get("access.events", "/".join([ACCESS_BASE, "events"]), _h_key())

    # Legacy quick check
    try:
        LEGACY.login()
        r = LEGACY.session.get("/".join([LEGACY_BASE, "s", "default", "stat", "sta"]), verify=VERIFY_TLS, timeout=6)
        out["legacy.stat_sta"] = {"url": r.request.url, "status": r.status_code}
    except Exception as e:
        out["legacy.stat_sta"] = {"error": str(e)}

    # Protect
    def try_get_protect(label: str, path: str):
        try:
            r = requests.get(f"{PROTECT_BASE}{path}", headers=_h_key(), verify=VERIFY_TLS, timeout=6)
            if r.status_code in (401, 403) and LEGACY_USER and LEGACY_PASS:
                LEGACY.login()
                r = LEGACY.session.get(f"{PROTECT_BASE}{path}", verify=VERIFY_TLS, timeout=6)
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

# ========= Health (consolidated) =========
# Note: The individual health resources are defined above in the triple-registered section

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

@mcp.tool()
def get_rate_limit_stats(endpoint: str = "global") -> Dict[str, Any]:
    """
    Get current rate limit statistics for a specific endpoint or global stats.
    Useful for monitoring API usage and avoiding rate limit errors.
    """
    try:
        if endpoint == "global":
            # Return summary of all endpoints
            all_endpoints = set(rate_limiter.minute_calls.keys()) | set(rate_limiter.hour_calls.keys())
            return {
                "rate_limits": {
                    "per_minute": RATE_LIMIT_PER_MINUTE,
                    "per_hour": RATE_LIMIT_PER_HOUR
                },
                "tracked_endpoints": len(all_endpoints),
                "endpoints": {ep: rate_limiter.get_stats(ep) for ep in sorted(all_endpoints)}
            }
        else:
            return rate_limiter.get_stats(endpoint)
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def get_session_info() -> Dict[str, Any]:
    """
    Get information about the current legacy authentication session.
    Shows session age, expiration time, and whether session needs refresh.
    Useful for monitoring session health and debugging authentication issues.
    """
    try:
        info = LEGACY.get_session_info()
        return {
            "success": True,
            "session": info,
            "session_timeout_configured": SESSION_TIMEOUT_S
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def invalidate_session() -> Dict[str, Any]:
    """
    Manually invalidate the current legacy authentication session.
    Forces re-authentication on next API call requiring legacy auth.
    Useful for testing credential rotation or clearing stale sessions.
    """
    try:
        LEGACY.invalidate()
        return {
            "success": True,
            "message": "Legacy session invalidated successfully. Next request will re-authenticate."
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# ========= Network Integration: resources =========
@mcp.resource("sites://")
async def sites() -> List[Dict[str, Any]]:
    return paginate_integration("/sites")

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
async def wlans(site_id: str) -> List[Dict[str, Any]] | Dict[str, Any]:
    # 1) Integration attempt (often 404/not exposed)
    try:
        url = "/".join([NET_INTEGRATION_BASE, "sites", site_id, "wlans"])
        res = _get(url, _h_key())
        data: List[Dict[str, Any]] = res.get("data", [])
        return data
    except UniFiHTTPError as e:
        if "404" not in str(e):
            raise
    # 2) Legacy fallback
    if LEGACY_USER and LEGACY_PASS:
        lr = legacy_get(f"/s/{site_id}/rest/wlanconf")
        data_or_error: List[Dict[str, Any]] | Dict[str, Any] = lr.get("data", lr)
        return data_or_error
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
async def search_clients(site_id: str, query: str) -> List[Dict[str, Any]]:
    cs = await clients(site_id)
    q = query.lower()
    def hit(c): return any(q in str(c.get(k, "")).lower() for k in ("hostname", "name", "mac", "ip", "user"))
    return [c for c in cs if hit(c)]

@mcp.resource("sites://{site_id}/search/devices/{query}")
async def search_devices(site_id: str, query: str) -> List[Dict[str, Any]]:
    ds = await devices(site_id)
    q = query.lower()
    def hit(d): return any(q in str(d.get(k, "")).lower() for k in ("name", "model", "mac", "ip", "ip_address"))
    return [d for d in ds if hit(d)]

# ========= UniFi Access: resources =========
@mcp.resource("access://doors")
async def access_doors() -> List[Dict[str, Any]]:
    res = _get("/".join([ACCESS_BASE, "doors"]), _h_key())
    data: List[Dict[str, Any]] = res.get("data", res)
    return data

@mcp.resource("access://readers")
async def access_readers() -> List[Dict[str, Any]]:
    res = _get("/".join([ACCESS_BASE, "readers"]), _h_key())
    data: List[Dict[str, Any]] = res.get("data", res)
    return data

@mcp.resource("access://users")
async def access_users() -> List[Dict[str, Any]]:
    res = _get("/".join([ACCESS_BASE, "users"]), _h_key())
    data: List[Dict[str, Any]] = res.get("data", res)
    return data

@mcp.resource("access://events")
async def access_events() -> List[Dict[str, Any]]:
    res = _get("/".join([ACCESS_BASE, "events"]), _h_key())
    data: List[Dict[str, Any]] = res.get("data", res)
    return data

# ========= UniFi Protect: resources =========
@mcp.resource("protect://nvr")
async def protect_nvr() -> Dict[str, Any]:
    return protect_get("/bootstrap")

@mcp.resource("protect://cameras")
async def protect_cameras() -> List[Dict[str, Any]]:
    res = protect_get("/cameras")
    if isinstance(res, dict) and "cameras" in res:
        cameras: List[Dict[str, Any]] = res["cameras"]
        return cameras
    # Fallback: return empty list if structure unexpected
    return []

@mcp.resource("protect://camera/{camera_id}")
async def protect_camera(camera_id: str) -> Dict[str, Any]:
    return protect_get(f"/cameras/{camera_id}")

@mcp.resource("protect://events")
async def protect_events() -> List[Dict[str, Any]]:
    res = protect_get("/events")
    if isinstance(res, dict) and "events" in res:
        events: List[Dict[str, Any]] = res["events"]
        return events
    # Fallback: return empty list if structure unexpected
    return []

@mcp.resource("protect://events/range/{start_ts}/{end_ts}")
async def protect_events_range(start_ts: str, end_ts: str) -> List[Dict[str, Any]]:
    res = protect_get("/events", params={"start": start_ts, "end": end_ts})
    if isinstance(res, dict) and "events" in res:
        events: List[Dict[str, Any]] = res["events"]
        return events
    # Fallback: return empty list if structure unexpected
    return []

@mcp.resource("protect://streams/{camera_id}")
async def protect_streams(camera_id: str) -> Dict[str, Any]:
    cam = protect_get(f"/cameras/{camera_id}")
    return {
        "id": cam.get("id"),
        "name": cam.get("name"),
        "channels": cam.get("channels"),
        "isRtspEnabled": cam.get("isRtspEnabled")
    }

# ========= Action tools =========
# Integration API – safe set
@mcp.tool()
def block_client(site_id: str, mac: str) -> Dict[str, Any]:
    """Block a client from the network by MAC address."""
    try:
        site_id = validate_site_id(site_id)
        mac = validate_mac_address(mac)
        return _post("/".join([NET_INTEGRATION_BASE, "sites", site_id, "clients", "block"]), _h_key(), {"mac": mac})
    except ValidationError as e:
        return {"success": False, "error": f"Validation failed: {str(e)}"}

@mcp.tool()
def unblock_client(site_id: str, mac: str) -> Dict[str, Any]:
    """Unblock a previously blocked client by MAC address."""
    try:
        site_id = validate_site_id(site_id)
        mac = validate_mac_address(mac)
        return _post("/".join([NET_INTEGRATION_BASE, "sites", site_id, "clients", "unblock"]), _h_key(), {"mac": mac})
    except ValidationError as e:
        return {"success": False, "error": f"Validation failed: {str(e)}"}

@mcp.tool()
def kick_client(site_id: str, mac: str) -> Dict[str, Any]:
    """Force disconnect a client from the network by MAC address."""
    try:
        site_id = validate_site_id(site_id)
        mac = validate_mac_address(mac)
        return _post("/".join([NET_INTEGRATION_BASE, "sites", site_id, "clients", "kick"]), _h_key(), {"mac": mac})
    except ValidationError as e:
        return {"success": False, "error": f"Validation failed: {str(e)}"}

@mcp.tool()
def locate_device(site_id: str, device_id: str, seconds: int = 30) -> Dict[str, Any]:
    """Flash the LEDs on a device to help locate it physically."""
    try:
        site_id = validate_site_id(site_id)
        device_id = validate_device_id(device_id)
        seconds = validate_duration(seconds, min_val=5, max_val=300)
        return _post("/".join([NET_INTEGRATION_BASE, "sites", site_id, "devices", device_id, "locate"]), _h_key(), {"duration": seconds})
    except ValidationError as e:
        return {"success": False, "error": f"Validation failed: {str(e)}"}

# Legacy-only example for WLAN toggle
@mcp.tool()
def wlan_set_enabled_legacy(site_id: str, wlan_id: str, enabled: bool) -> Dict[str, Any]:
    """Toggle WLAN (legacy API) when Integration API doesn't expose WLANs."""
    try:
        site_id = validate_site_id(site_id)
        wlan_id = validate_wlan_id(wlan_id)
        enabled = validate_boolean(enabled, "enabled")
        body = {"_id": wlan_id, "enabled": enabled}
        return legacy_post(f"/s/{site_id}/rest/wlanconf/{wlan_id}", body)
    except ValidationError as e:
        return {"success": False, "error": f"Validation failed: {str(e)}"}

# Access – sample action (varies by build)
@mcp.tool()
def access_unlock_door(door_id: str, seconds: int = 5) -> Dict[str, Any]:
    """Momentarily unlock an access control door."""
    try:
        door_id = validate_door_id(door_id)
        seconds = validate_duration(seconds, min_val=1, max_val=60)
        return _post("/".join([ACCESS_BASE, "doors", door_id, "unlock"]), _h_key(), {"duration": seconds})
    except ValidationError as e:
        return {"success": False, "error": f"Validation failed: {str(e)}"}

# Protect – safe starters
@mcp.tool()
def protect_camera_reboot(camera_id: str) -> Dict[str, Any]:
    """Reboot a Protect camera (causes brief downtime)."""
    try:
        camera_id = validate_camera_id(camera_id)
        return protect_post(f"/cameras/{camera_id}/reboot")
    except ValidationError as e:
        return {"success": False, "error": f"Validation failed: {str(e)}"}

@mcp.tool()
def protect_camera_led(camera_id: str, enabled: bool) -> Dict[str, Any]:
    """Toggle the status LED on a Protect camera."""
    try:
        camera_id = validate_camera_id(camera_id)
        enabled = validate_boolean(enabled, "enabled")
        body = {"ledSettings": {"isEnabled": enabled}}
        return protect_post(f"/cameras/{camera_id}", body)
    except ValidationError as e:
        return {"success": False, "error": f"Validation failed: {str(e)}"}

@mcp.tool()
def protect_toggle_privacy(camera_id: str, enabled: bool) -> Dict[str, Any]:
    """Toggle privacy mode on a Protect camera (disables recording when enabled)."""
    try:
        camera_id = validate_camera_id(camera_id)
        enabled = validate_boolean(enabled, "enabled")
        body = {"privacyMode": enabled}
        return protect_post(f"/cameras/{camera_id}", body)
    except ValidationError as e:
        return {"success": False, "error": f"Validation failed: {str(e)}"}

# ========= Prompt playbooks =========
@mcp.prompt("how_to_find_device")
def how_to_find_device() -> Dict[str, Any]:
    return {
        "description": "Find a network device and flash its LEDs.",
        "messages": [{"role": "system",
                      "content": "Search device via 'sites://{site_id}/search/devices/{query}', confirm, then call 'locate_device' for ~30s."}]
    }

@mcp.prompt("how_to_block_client")
def how_to_block_client() -> Dict[str, Any]:
    return {
        "description": "Find & block a client safely.",
        "messages": [{"role": "system",
                      "content": "List 'sites://{site_id}/clients/active', match MAC/host, confirm with user, then call 'block_client'. Offer 'unblock_client' as a reversal."}]
    }

@mcp.prompt("how_to_toggle_wlan")
def how_to_toggle_wlan() -> Dict[str, Any]:
    return {
        "description": "Toggle a WLAN using Integration if available, else Legacy.",
        "messages": [{"role": "system",
                      "content": "Fetch 'sites://{site_id}/wlans'. If returns an error object with ok:false, request legacy creds, then call 'wlan_set_enabled_legacy'."}]
    }

@mcp.prompt("how_to_manage_access")
def how_to_manage_access() -> Dict[str, Any]:
    return {
        "description": "Check doors/readers and perform a momentary unlock.",
        "messages": [{"role": "system",
                      "content": "List 'access://doors' to choose a door, confirm with the user, then call 'access_unlock_door' with a short duration."}]
    }

@mcp.prompt("how_to_find_camera")
def how_to_find_camera() -> Dict[str, Any]:
    return {
        "description": "Find a Protect camera and show its streams.",
        "messages": [{"role": "system",
                      "content": "Call 'protect://cameras', match by name/model, then 'protect://streams/{camera_id}' to present channels/RTSP."}]
    }

@mcp.prompt("how_to_review_motion")
def how_to_review_motion() -> Dict[str, Any]:
    return {
        "description": "Review recent motion/smart events in Protect.",
        "messages": [{"role": "system",
                      "content": "Fetch 'protect://events' or 'protect://events/range/{start_ts}/{end_ts}', then summarize by camera and type."}]
    }

@mcp.prompt("how_to_reboot_camera")
def how_to_reboot_camera() -> Dict[str, Any]:
    return {
        "description": "Safely reboot a Protect camera after confirmation.",
        "messages": [{"role": "system",
                      "content": "List 'protect://cameras', confirm the camera with the user, then call 'protect_camera_reboot' and warn about brief downtime."}]
    }

# ========= Entrypoint =========
if __name__ == "__main__":
    print("🚀 UniFi MCP – Integration + Legacy + Access + Protect (+ Site Manager stubs)")
    print(f"→ Controller: https://{UNIFI_HOST}:{UNIFI_PORT}  TLS verify={VERIFY_TLS}")
    if not UNIFI_API_KEY:
        print("⚠️ UNIFI_API_KEY not set — Integration/Access/Protect key-based calls may fail.")
    mcp.run(transport="stdio")
