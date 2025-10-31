"""
Integration tests for error handling.

Tests various HTTP error codes, timeouts, and failure scenarios.
"""

import pytest
import responses
import requests
from unittest.mock import patch
from tests.mock_unifi import MockUniFiController


@pytest.fixture
def mock_env(monkeypatch):
    """Set up mock environment variables."""
    monkeypatch.setenv("UNIFI_API_KEY", "test_api_key_12345")
    monkeypatch.setenv("UNIFI_GATEWAY_HOST", "192.168.1.1")
    monkeypatch.setenv("UNIFI_GATEWAY_PORT", "443")
    monkeypatch.setenv("UNIFI_VERIFY_TLS", "false")
    monkeypatch.setenv("UNIFI_TIMEOUT_S", "2")  # Short timeout for tests


class TestHTTPErrorHandling:
    """Test handling of various HTTP error codes."""

    @responses.activate
    def test_401_unauthorized(self, mock_env):
        """Test 401 Unauthorized error."""
        responses.add(
            responses.GET,
            "https://192.168.1.1:443/proxy/network/integrations/v1/sites",
            json={"error": "Unauthorized"},
            status=401
        )

        from main import _get, _h_key, NET_INTEGRATION_BASE, UniFiHTTPError

        with pytest.raises(UniFiHTTPError) as exc_info:
            _get(f"{NET_INTEGRATION_BASE}/sites", _h_key())

        error_msg = str(exc_info.value)
        assert "401" in error_msg

    @responses.activate
    def test_403_forbidden(self, mock_env):
        """Test 403 Forbidden error."""
        responses.add(
            responses.GET,
            "https://192.168.1.1:443/proxy/network/integrations/v1/sites",
            json={"error": "Forbidden"},
            status=403
        )

        from main import _get, _h_key, NET_INTEGRATION_BASE, UniFiHTTPError

        with pytest.raises(UniFiHTTPError) as exc_info:
            _get(f"{NET_INTEGRATION_BASE}/sites", _h_key())

        assert "403" in str(exc_info.value)

    @responses.activate
    def test_404_not_found(self, mock_env):
        """Test 404 Not Found error."""
        responses.add(
            responses.GET,
            "https://192.168.1.1:443/proxy/network/integrations/v1/sites/nonexistent",
            json={"error": "Not found"},
            status=404
        )

        from main import _get, _h_key, UniFiHTTPError

        with pytest.raises(UniFiHTTPError) as exc_info:
            _get("https://192.168.1.1:443/proxy/network/integrations/v1/sites/nonexistent", _h_key())

        assert "404" in str(exc_info.value)

    @responses.activate
    def test_500_internal_server_error(self, mock_env):
        """Test 500 Internal Server Error."""
        responses.add(
            responses.GET,
            "https://192.168.1.1:443/proxy/network/integrations/v1/sites",
            json={"error": "Internal server error"},
            status=500
        )

        from main import _get, _h_key, NET_INTEGRATION_BASE, UniFiHTTPError

        with pytest.raises(UniFiHTTPError) as exc_info:
            _get(f"{NET_INTEGRATION_BASE}/sites", _h_key())

        assert "500" in str(exc_info.value)

    @responses.activate
    def test_503_service_unavailable(self, mock_env):
        """Test 503 Service Unavailable."""
        responses.add(
            responses.GET,
            "https://192.168.1.1:443/proxy/network/integrations/v1/sites",
            body="Service Unavailable",
            status=503
        )

        from main import _get, _h_key, NET_INTEGRATION_BASE, UniFiHTTPError

        with pytest.raises(UniFiHTTPError) as exc_info:
            _get(f"{NET_INTEGRATION_BASE}/sites", _h_key())

        assert "503" in str(exc_info.value)


class TestTimeoutHandling:
    """Test timeout scenarios."""

    def test_request_timeout(self, mock_env):
        """Test request timeout handling."""
        from main import _get, _h_key, UniFiHTTPError

        # Mock a very slow endpoint
        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout("Request timed out")

            with pytest.raises(Exception):  # Could be wrapped in UniFiHTTPError or direct Timeout
                _get("https://192.168.1.1:443/proxy/network/integrations/v1/sites", _h_key(), timeout=1)


class TestSensitiveDataRedaction:
    """Test that sensitive data is redacted from error messages."""

    @responses.activate
    def test_api_key_redacted_in_errors(self, mock_env):
        """Test that API keys are redacted from error messages."""
        responses.add(
            responses.GET,
            "https://192.168.1.1:443/proxy/network/integrations/v1/sites",
            json={"error": "Invalid API key: test_api_key_12345"},
            status=401
        )

        from main import _get, _h_key, NET_INTEGRATION_BASE, UniFiHTTPError

        with pytest.raises(UniFiHTTPError) as exc_info:
            _get(f"{NET_INTEGRATION_BASE}/sites", _h_key())

        error_msg = str(exc_info.value)

        # API key should be redacted
        assert "test_api_key_12345" not in error_msg or "[REDACTED]" in error_msg

    @responses.activate
    def test_password_redacted_in_errors(self, mock_env):
        """Test that passwords are redacted from error messages."""
        responses.add(
            responses.POST,
            "https://192.168.1.1:443/api/auth/login",
            json={"error": "Invalid password: password"},
            status=401
        )

        from main import LegacySessionManager, UniFiHTTPError

        manager = LegacySessionManager(session_timeout_s=3600)

        with pytest.raises(UniFiHTTPError) as exc_info:
            manager.login()

        error_msg = str(exc_info.value)

        # Password should be redacted
        # Note: The actual password value "password" is generic, but the pattern should catch it
        assert "[REDACTED]" in error_msg or "password:" not in error_msg.lower()


class TestConnectionErrors:
    """Test connection error handling."""

    def test_connection_refused(self, mock_env):
        """Test handling of connection refused errors."""
        from main import _get, _h_key

        # Override host to non-existent address
        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")

            with pytest.raises(requests.exceptions.ConnectionError):
                _get("https://192.168.1.1:443/proxy/network/integrations/v1/sites", _h_key())

    def test_dns_resolution_failure(self, mock_env):
        """Test handling of DNS resolution failures."""
        from main import _get, _h_key

        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.ConnectionError("Name or service not known")

            with pytest.raises(requests.exceptions.ConnectionError):
                _get("https://invalid-host:443/proxy/network/integrations/v1/sites", _h_key())


class TestInputValidation:
    """Test input validation and error handling."""

    def test_invalid_mac_address(self):
        """Test validation of invalid MAC addresses."""
        from main import validate_mac_address, ValidationError

        with pytest.raises(ValidationError) as exc_info:
            validate_mac_address("invalid")

        assert "Invalid MAC address" in str(exc_info.value)

    def test_invalid_site_id(self):
        """Test validation of invalid site IDs."""
        from main import validate_site_id, ValidationError

        # Too long
        with pytest.raises(ValidationError) as exc_info:
            validate_site_id("a" * 100)

        assert "too long" in str(exc_info.value)

        # Invalid characters
        with pytest.raises(ValidationError) as exc_info:
            validate_site_id("site@#$%")

        assert "invalid characters" in str(exc_info.value)

    def test_invalid_duration(self):
        """Test validation of invalid durations."""
        from main import validate_duration, ValidationError

        # Too short
        with pytest.raises(ValidationError) as exc_info:
            validate_duration(0, min_val=1)

        assert "too short" in str(exc_info.value)

        # Too long
        with pytest.raises(ValidationError) as exc_info:
            validate_duration(1000, max_val=300)

        assert "too long" in str(exc_info.value)


class TestMalformedResponses:
    """Test handling of malformed or unexpected responses."""

    @responses.activate
    def test_empty_response_body(self, mock_env):
        """Test handling of empty response body."""
        responses.add(
            responses.GET,
            "https://192.168.1.1:443/proxy/network/integrations/v1/sites",
            body="",
            status=200
        )

        from main import _get, _h_key, NET_INTEGRATION_BASE

        # Should handle empty response gracefully
        result = _get(f"{NET_INTEGRATION_BASE}/sites", _h_key())
        assert result == {}

    @responses.activate
    def test_non_json_response(self, mock_env):
        """Test handling of non-JSON response."""
        responses.add(
            responses.GET,
            "https://192.168.1.1:443/proxy/network/integrations/v1/sites",
            body="<html>Not JSON</html>",
            status=200,
            content_type="text/html"
        )

        from main import _get, _h_key, NET_INTEGRATION_BASE

        with pytest.raises(Exception):  # JSONDecodeError or similar
            _get(f"{NET_INTEGRATION_BASE}/sites", _h_key())


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
