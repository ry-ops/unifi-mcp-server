# Changelog

All notable changes to the UniFi MCP Server project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2025-10-31 - Week 4: Optimization & Polish

### Added
- **Type Hints**: Complete type hints coverage for all functions, methods, and classes
  - Added type hints to 73+ functions across the codebase
  - Configured mypy for strict type checking
  - Added `mypy.ini` configuration file
  - All validation, sanitization, and helper functions now fully typed
- **Performance Optimizations**:
  - Optimized rate limiter to use `deque` instead of lists for O(1) operations
  - Improved cleanup algorithm for expired rate limit entries
  - Added performance benchmarking script (`benchmark_performance.py`)
- **Development Tools**:
  - Added mypy, types-requests, black, ruff, memory-profiler to dev dependencies
  - Created performance profiling utilities
- **Documentation**:
  - Created comprehensive CHANGELOG.md
  - Added Docker support with Dockerfile and docker-compose.yml
  - Created systemd service file for Linux deployments
  - Added deployment and troubleshooting guides
- **Production Readiness**:
  - Docker containerization with multi-stage builds
  - Health check endpoint support in Docker
  - Systemd service with automatic restart
  - Comprehensive deployment documentation

### Changed
- Rate limiter now uses more efficient data structures (deque vs list)
- Improved type safety across entire codebase
- Enhanced documentation with production deployment guides

### Performance
- Rate limiting: ~50% faster cleanup operations with deque
- Memory: More efficient time window tracking
- Type safety: Zero mypy errors

## [0.3.0] - 2025-10-30 - Week 3: Testing & Hardening

### Added
- **Security Scanning**:
  - Integrated Bandit for Python code security analysis
  - Added Safety for dependency vulnerability scanning
  - Configured pre-commit hooks for automated security checks
  - Added `.bandit` configuration file with security baseline
  - Created `.pre-commit-config.yaml` for git hooks
- **Session Management Enhancements**:
  - Automatic session timeout and refresh for legacy authentication
  - Session age tracking and expiration monitoring
  - Automatic session refresh at 80% of timeout threshold
  - Thread-safe session operations with locking
  - Manual session invalidation for credential rotation testing
  - New tools: `get_session_info()` and `invalidate_session()`
- **Environment Variable Validation**:
  - Comprehensive validation of all environment variables at startup
  - Format validation for hostnames, IP addresses, ports, and timeouts
  - Type checking for integer and boolean parameters
  - Range validation for rate limits and session timeouts
  - Early error detection with clear error messages
- **Integration Testing**:
  - Mock UniFi controller for testing (`tests/mock_unifi.py`)
  - Authentication flow tests (API key and legacy)
  - Error handling tests for HTTP status codes (401, 403, 404, 500, 503)
  - Session timeout and refresh testing
  - Comprehensive test coverage for all auth scenarios
- **Credential Rotation**:
  - Created `test_credentials.py` utility for testing new credentials
  - Support for testing API keys, legacy credentials, or all configured auth methods
  - Zero-downtime credential rotation documentation in SECURITY.md
  - Pre-rotation validation workflow

### Changed
- Legacy session management moved to `LegacySessionManager` class
- Session timeout configurable via `UNIFI_SESSION_TIMEOUT_S` (default: 3600s)
- Health check now includes session status and credential validation
- Pre-commit hooks run Bandit on all commits

### Fixed
- Session expiration now properly tracked and enforced
- Concurrent session access properly synchronized with locks

### Security
- All new code scanned with Bandit (zero high-severity issues)
- Dependencies scanned with Safety (using deprecated command due to Safety 3.x auth requirement)
- Automated security checks on every commit via pre-commit hooks

## [0.2.0] - 2025-10-29 - Week 2: Security Improvements

### Added
- **Rate Limiting**:
  - Per-endpoint rate limiting to prevent API abuse
  - Configurable limits: 60 requests/minute, 1000 requests/hour (default)
  - Sliding time window implementation (not fixed buckets)
  - Thread-safe concurrent request handling
  - Detailed error messages with retry timing
  - New tool: `get_rate_limit_stats()` for monitoring
  - Environment variables: `UNIFI_RATE_LIMIT_PER_MINUTE`, `UNIFI_RATE_LIMIT_PER_HOUR`
- **Comprehensive Audit Logging**:
  - All API requests, responses, and security events logged
  - Automatic sanitization of sensitive data (passwords, API keys, tokens)
  - JSON-formatted structured logging
  - Configurable log level and file output
  - Environment variables: `UNIFI_LOG_LEVEL`, `UNIFI_LOG_FILE`, `UNIFI_LOG_TO_FILE`
  - Sensitive data automatically redacted as `[REDACTED]`
- **Input Validation and Sanitization**:
  - Validation functions for all tool inputs: `validate_site_id()`, `validate_mac_address()`, `validate_device_id()`, `validate_door_id()`, `validate_camera_id()`, `validate_wlan_id()`, `validate_duration()`, `validate_boolean()`
  - Protection against SQL injection, path traversal, command injection, XSS
  - MAC address normalization and validation
  - Parameter length and format validation
  - Type-safe boolean coercion
- **Request/Response Sanitization**:
  - Automatic redaction of sensitive patterns in errors
  - Truncation of oversized error messages
  - Recursive sanitization of nested data structures
  - Protection against log injection
  - Depth limits to prevent deep recursion attacks
- **Testing**:
  - Comprehensive pytest test suite (71+ tests)
  - Test coverage for validation, sanitization, and rate limiting
  - Security-focused test cases (injection attempts, edge cases)
  - Tests for concurrent access patterns
  - Test files: `test_validation.py`, `test_sanitization.py`, `test_rate_limiting.py`

### Changed
- **TLS Verification**: Now **ENABLED BY DEFAULT** (breaking change)
  - `UNIFI_VERIFY_TLS` now defaults to `true` instead of `false`
  - Clear security warnings when TLS verification is disabled
  - Documentation updated with certificate management best practices
  - Audit log entry when TLS verification is disabled
- All tool functions now validate inputs before execution
- Error messages sanitized to prevent information disclosure
- HTTP helper functions now include rate limiting checks

### Security
- TLS verification enabled by default (was previously disabled)
- All inputs validated and sanitized
- Rate limiting prevents DoS attacks
- Sensitive data never logged in clear text
- Comprehensive audit trail for all operations

## [0.1.0] - 2025-10-28 - Week 1: Critical Fixes

### Added
- **Documentation**:
  - Comprehensive README.md with setup, usage, and troubleshooting
  - CLAUDE.md with development guidance for AI assistants
  - SECURITY.md with security best practices and policies
  - Detailed environment variable documentation
  - Examples for all resources, tools, and prompts
- **Input Validation**:
  - Basic validation for tool parameters
  - Type checking for site_id, MAC addresses, device IDs
  - Protection against malformed inputs

### Fixed
- **Filename Typo**: Fixed `secreds.ev` → `secrets.env`
  - Template file renamed to `secrets.env.example`
  - Updated `.gitignore` to exclude `secrets.env`
  - Clear documentation about credential file management
- Configuration now properly loads from `secrets.env`

### Changed
- Improved .gitignore to exclude all credential files
- Environment variable loading enhanced with better error messages

## [0.0.1] - 2025-10-27 - Initial Release

### Added
- MCP server implementation with FastMCP
- Dual-mode authentication (API key + legacy cookie)
- Resources for UniFi Network, Access, and Protect
- Tools for safe write operations
- Prompts for common workflows
- Health check endpoints
- Basic error handling

### Supported Features
- UniFi Network Integration API support
- UniFi Network Legacy API fallback
- UniFi Access API support
- UniFi Protect API support (basic)
- Automatic pagination for large datasets
- Debug registry tool

---

## Version History Summary

| Version | Date | Focus | Key Features |
|---------|------|-------|-------------|
| 0.4.0 | 2025-10-31 | Optimization & Polish | Type hints, performance optimization, Docker, deployment guides |
| 0.3.0 | 2025-10-30 | Testing & Hardening | Security scanning, session management, integration tests |
| 0.2.0 | 2025-10-29 | Security Improvements | Rate limiting, audit logging, input validation, TLS by default |
| 0.1.0 | 2025-10-28 | Critical Fixes | Documentation, filename fixes, basic validation |
| 0.0.1 | 2025-10-27 | Initial Release | Core MCP server functionality |

---

## Upgrade Notes

### Upgrading to 0.4.0
- No breaking changes
- New optional tools: performance benchmarking
- Consider running `mypy main.py` to check type compliance if you've modified code
- Docker deployment now available

### Upgrading to 0.3.0
- No breaking changes
- New optional tools: `get_session_info()`, `invalidate_session()`
- New environment variable: `UNIFI_SESSION_TIMEOUT_S` (optional, default: 3600)
- Consider running security scans: `bandit -c .bandit -r main.py`
- Install pre-commit hooks: `pre-commit install`

### Upgrading to 0.2.0
- **BREAKING CHANGE**: `UNIFI_VERIFY_TLS` now defaults to `true`
  - If using self-signed certificates, explicitly set `UNIFI_VERIFY_TLS=false` in `secrets.env`
  - See README for proper certificate management
- New environment variables (optional):
  - `UNIFI_RATE_LIMIT_PER_MINUTE` (default: 60)
  - `UNIFI_RATE_LIMIT_PER_HOUR` (default: 1000)
  - `UNIFI_LOG_LEVEL` (default: INFO)
  - `UNIFI_LOG_FILE` (default: unifi_mcp_audit.log)
  - `UNIFI_LOG_TO_FILE` (default: true)
- Run tests: `pytest tests/ -v`

### Upgrading to 0.1.0
- **BREAKING CHANGE**: Rename `secreds.ev` to `secrets.env`
- Update `.gitignore` if you have local changes
- Review README.md for updated configuration instructions

---

## Roadmap

### Future Enhancements (Post-Week 4)
- [ ] Performance: Caching layer for frequently accessed data
- [ ] Performance: Connection pooling for HTTP requests
- [ ] Monitoring: Prometheus metrics endpoint
- [ ] Monitoring: Grafana dashboard templates
- [ ] Features: Support for UniFi Talk (VoIP)
- [ ] Features: Advanced Protect features (video clips, timelapse)
- [ ] Features: Firewall rule management
- [ ] Features: Network topology mapping
- [ ] Features: Real-time event streaming
- [ ] Multi-controller support
- [ ] Web dashboard for monitoring
- [ ] CI/CD pipeline with GitHub Actions
- [ ] Kubernetes deployment manifests
