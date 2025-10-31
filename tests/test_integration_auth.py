"""
Integration tests for authentication flows.

Tests both API key and legacy cookie authentication with the mock controller.
"""

import pytest
import responses
import time
from unittest.mock import Mock, patch
from tests.mock_unifi import MockUniFiController


@pytest.fixture
def mock_controller():
    """Create a fresh mock controller for each test."""
    return MockUniFiController()


@pytest.fixture
def mock_env(monkeypatch):
    """Set up mock environment variables."""
    monkeypatch.setenv("UNIFI_API_KEY", "test_api_key_12345")
    monkeypatch.setenv("UNIFI_GATEWAY_HOST", "192.168.1.1")
    monkeypatch.setenv("UNIFI_GATEWAY_PORT", "443")
    monkeypatch.setenv("UNIFI_VERIFY_TLS", "false")
    monkeypatch.setenv("UNIFI_USERNAME", "admin")
    monkeypatch.setenv("UNIFI_PASSWORD", "password")
    monkeypatch.setenv("UNIFI_SESSION_TIMEOUT_S", "3600")
    monkeypatch.setenv("UNIFI_TIMEOUT_S", "15")


class TestAPIKeyAuthentication:
    """Test API key authentication flows."""

    @responses.activate
    def test_valid_api_key(self, mock_controller, mock_env):
        """Test successful API key authentication."""
        # Setup mock response
        responses.add(
            responses.GET,
            "https://192.168.1.1:443/proxy/network/integrations/v1/sites",
            json=mock_controller.get_sites(),
            status=200
        )

        # Import after env is mocked
        from main import _get, _h_key, NET_INTEGRATION_BASE

        # Make request
        result = _get(f"{NET_INTEGRATION_BASE}/sites", _h_key())

        # Verify
        assert result["count"] == 1
        assert len(responses.calls) == 1
        assert responses.calls[0].request.headers["X-API-Key"] == "test_api_key_12345"

    @responses.activate
    def test_invalid_api_key(self, mock_controller, mock_env):
        """Test failed API key authentication."""
        # Setup mock response for invalid key
        responses.add(
            responses.GET,
            "https://192.168.1.1:443/proxy/network/integrations/v1/sites",
            json={"error": "Unauthorized"},
            status=401
        )

        from main import _get, NET_INTEGRATION_BASE, UniFiHTTPError

        # Override API key to invalid value
        headers = {"X-API-Key": "invalid_key", "Content-Type": "application/json"}

        # Make request and expect failure
        with pytest.raises(UniFiHTTPError) as exc_info:
            _get(f"{NET_INTEGRATION_BASE}/sites", headers)

        assert "401" in str(exc_info.value)

    @responses.activate
    def test_missing_api_key(self, mock_controller, mock_env):
        """Test request without API key."""
        responses.add(
            responses.GET,
            "https://192.168.1.1:443/proxy/network/integrations/v1/sites",
            json={"error": "Unauthorized"},
            status=401
        )

        from main import _get, NET_INTEGRATION_BASE, UniFiHTTPError

        # No API key header
        headers = {"Content-Type": "application/json"}

        with pytest.raises(UniFiHTTPError) as exc_info:
            _get(f"{NET_INTEGRATION_BASE}/sites", headers)

        assert "401" in str(exc_info.value)


class TestLegacyAuthentication:
    """Test legacy cookie-based authentication flows."""

    def test_legacy_session_creation(self, mock_env):
        """Test creating a new legacy session."""
        from main import LegacySessionManager

        manager = LegacySessionManager(session_timeout_s=3600)

        assert manager.session_created_at is None
        assert not manager.is_session_valid()
        assert not manager.should_refresh()

    @responses.activate
    def test_legacy_login_success(self, mock_controller, mock_env):
        """Test successful legacy login."""
        # Mock login endpoint
        responses.add(
            responses.POST,
            "https://192.168.1.1:443/api/auth/login",
            json={"success": True},
            status=200,
            headers={"Set-Cookie": "session=test_session_123"}
        )

        from main import LegacySessionManager

        manager = LegacySessionManager(session_timeout_s=3600)
        manager.login()

        # Verify session was created
        assert manager.session_created_at is not None
        assert manager.is_session_valid()
        assert not manager.should_refresh()

    @responses.activate
    def test_legacy_login_failure(self, mock_controller, mock_env):
        """Test failed legacy login."""
        responses.add(
            responses.POST,
            "https://192.168.1.1:443/api/auth/login",
            json={"error": "Invalid credentials"},
            status=401
        )

        from main import LegacySessionManager, UniFiHTTPError

        manager = LegacySessionManager(session_timeout_s=3600)

        with pytest.raises(UniFiHTTPError):
            manager.login()

    def test_session_timeout_detection(self, mock_env):
        """Test session timeout detection."""
        from main import LegacySessionManager

        manager = LegacySessionManager(session_timeout_s=2)  # 2 second timeout for testing

        # Manually set session as created 3 seconds ago
        manager.session_created_at = time.time() - 3
        manager.session.cookies.set("session", "test_session")

        # Session should be expired
        assert not manager.is_session_valid()

    def test_session_refresh_threshold(self, mock_env):
        """Test session refresh threshold (80% of timeout)."""
        from main import LegacySessionManager

        manager = LegacySessionManager(session_timeout_s=100)

        # Set session created 85 seconds ago (85% of timeout)
        manager.session_created_at = time.time() - 85
        manager.session.cookies.set("session", "test_session")

        # Should need refresh (>80%)
        assert manager.should_refresh()

        # Set session created 70 seconds ago (70% of timeout)
        manager.session_created_at = time.time() - 70

        # Should not need refresh (<80%)
        assert not manager.should_refresh()

    @responses.activate
    def test_automatic_session_refresh(self, mock_controller, mock_env):
        """Test automatic session refresh when approaching expiration."""
        # Mock login endpoint for both initial and refresh
        responses.add(
            responses.POST,
            "https://192.168.1.1:443/api/auth/login",
            json={"success": True},
            status=200
        )
        responses.add(
            responses.POST,
            "https://192.168.1.1:443/api/auth/login",
            json={"success": True},
            status=200
        )

        from main import LegacySessionManager

        manager = LegacySessionManager(session_timeout_s=100)

        # Initial login
        manager.login()
        first_created = manager.session_created_at

        # Simulate time passing (85% of timeout)
        manager.session_created_at = time.time() - 85

        # Call refresh_if_needed
        manager.refresh_if_needed()

        # Session should have been refreshed
        assert manager.session_created_at > first_created

    def test_session_invalidation(self, mock_env):
        """Test manual session invalidation."""
        from main import LegacySessionManager

        manager = LegacySessionManager(session_timeout_s=3600)

        # Set up session
        manager.session_created_at = time.time()
        manager.session.cookies.set("session", "test_session")

        assert manager.is_session_valid()

        # Invalidate
        manager.invalidate()

        # Session should be cleared
        assert manager.session_created_at is None
        assert not manager.is_session_valid()
        assert len(manager.session.cookies) == 0

    def test_get_session_info(self, mock_env):
        """Test getting session information."""
        from main import LegacySessionManager

        manager = LegacySessionManager(session_timeout_s=3600)

        # No session
        info = manager.get_session_info()
        assert info["active"] is False
        assert "No active session" in info["message"]

        # With session
        manager.session_created_at = time.time()
        manager.session.cookies.set("session", "test_session")

        info = manager.get_session_info()
        assert info["active"] is True
        assert info["timeout_seconds"] == 3600
        assert "created_at" in info
        assert "expires_at" in info


class TestDualAuthFallback:
    """Test fallback from API key to legacy auth."""

    @responses.activate
    def test_protect_api_key_to_legacy_fallback(self, mock_controller, mock_env):
        """Test Protect endpoints falling back from API key to legacy auth."""
        # First attempt with API key fails
        responses.add(
            responses.GET,
            "https://192.168.1.1:443/proxy/protect/api/cameras",
            json={"error": "Unauthorized"},
            status=401
        )

        # Legacy login succeeds
        responses.add(
            responses.POST,
            "https://192.168.1.1:443/api/auth/login",
            json={"success": True},
            status=200
        )

        # Second attempt with session succeeds
        responses.add(
            responses.GET,
            "https://192.168.1.1:443/proxy/protect/api/cameras",
            json={"cameras": []},
            status=200
        )

        from main import protect_get

        result = protect_get("/cameras")

        # Should have made 3 requests: API key attempt, login, session attempt
        assert len(responses.calls) == 3
        assert responses.calls[0].request.url.endswith("/cameras")  # API key attempt
        assert responses.calls[1].request.url.endswith("/login")    # Legacy login
        assert responses.calls[2].request.url.endswith("/cameras")  # Session attempt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
