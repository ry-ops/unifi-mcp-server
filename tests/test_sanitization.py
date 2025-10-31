"""
Test suite for data sanitization functionality.
Tests sanitization of sensitive data in logs, errors, and responses.
"""

import pytest
import sys
import os

# Add parent directory to path to import main module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import sanitize_for_logging, sanitize_error_message
from unittest.mock import Mock


class TestSanitizeForLogging:
    """Test sanitization of sensitive data for logging."""

    def test_sanitize_password_field(self):
        """Test that password fields are redacted."""
        data = {"username": "admin", "password": "secret123"}
        result = sanitize_for_logging(data)
        assert result["username"] == "admin"
        assert result["password"] == "[REDACTED]"

    def test_sanitize_api_key_field(self):
        """Test that API key fields are redacted."""
        data = {
            "api_key": "abc123",
            "apiKey": "def456",
            "apikey": "ghi789",
            "x-api-key": "jkl012",
        }
        result = sanitize_for_logging(data)
        assert all(v == "[REDACTED]" for v in result.values())

    def test_sanitize_token_fields(self):
        """Test that token fields are redacted."""
        data = {
            "token": "token123",
            "access_token": "access456",
            "refresh_token": "refresh789",
            "csrf-token": "csrf012",
        }
        result = sanitize_for_logging(data)
        assert all(v == "[REDACTED]" for v in result.values())

    def test_sanitize_authorization_fields(self):
        """Test that authorization fields are redacted."""
        data = {
            "authorization": "Bearer token123",
            "Authorization": "Basic dXNlcjpwYXNz",
        }
        result = sanitize_for_logging(data)
        assert all(v == "[REDACTED]" for v in result.values())

    def test_sanitize_nested_objects(self):
        """Test sanitization of nested objects."""
        data = {
            "user": {
                "username": "admin",
                "password": "secret",
                "profile": {"email": "user@example.com", "api_key": "key123"},
            }
        }
        result = sanitize_for_logging(data)
        assert result["user"]["username"] == "admin"
        assert result["user"]["password"] == "[REDACTED]"
        assert result["user"]["profile"]["email"] == "user@example.com"
        assert result["user"]["profile"]["api_key"] == "[REDACTED]"

    def test_sanitize_lists(self):
        """Test sanitization of lists."""
        data = {
            "users": [
                {"name": "user1", "password": "pass1"},
                {"name": "user2", "password": "pass2"},
            ]
        }
        result = sanitize_for_logging(data)
        assert result["users"][0]["name"] == "user1"
        assert result["users"][0]["password"] == "[REDACTED]"
        assert result["users"][1]["name"] == "user2"
        assert result["users"][1]["password"] == "[REDACTED]"

    def test_truncate_long_strings(self):
        """Test that long strings are truncated."""
        long_string = "x" * 2000
        result = sanitize_for_logging(long_string)
        assert len(result) < 200  # Should be truncated
        assert "[TRUNCATED" in result

    def test_max_depth_protection(self):
        """Test protection against deeply nested objects."""
        # Create deeply nested object
        data = {"level": 1}
        current = data
        for i in range(15):
            current["nested"] = {"level": i + 2}
            current = current["nested"]

        result = sanitize_for_logging(data)
        # Should stop at max depth
        assert "[MAX_DEPTH_REACHED]" in str(result)

    def test_preserve_non_sensitive_data(self):
        """Test that non-sensitive data is preserved."""
        data = {
            "username": "admin",
            "email": "admin@example.com",
            "role": "administrator",
            "last_login": "2024-01-01T00:00:00Z",
            "settings": {"theme": "dark", "notifications": True},
        }
        result = sanitize_for_logging(data)
        assert result == data  # Should be unchanged

    def test_case_insensitive_matching(self):
        """Test that sensitive field matching is case-insensitive."""
        data = {
            "PASSWORD": "secret",
            "Password": "secret",
            "ApiKey": "key123",
            "API_KEY": "key456",
        }
        result = sanitize_for_logging(data)
        assert all(v == "[REDACTED]" for v in result.values())

    def test_partial_field_name_matching(self):
        """Test that partial matches in field names are caught."""
        data = {
            "user_password": "secret",
            "api_key_prod": "key123",
            "oauth_token": "token456",
            "session_secret": "session789",
        }
        result = sanitize_for_logging(data)
        assert all(v == "[REDACTED]" for v in result.values())


class TestSanitizeErrorMessage:
    """Test sanitization of error messages."""

    def test_sanitize_api_key_in_url(self):
        """Test that API keys in URLs are redacted."""
        mock_response = Mock()
        error_msg = "GET https://example.com/api?api_key=secret123 -> 404"
        result = sanitize_error_message(error_msg, mock_response)
        assert "secret123" not in result
        assert "[REDACTED]" in result

    def test_sanitize_bearer_token(self):
        """Test that Bearer tokens are redacted."""
        mock_response = Mock()
        error_msg = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        result = sanitize_error_message(error_msg, mock_response)
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in result
        assert "[REDACTED]" in result

    def test_sanitize_basic_auth(self):
        """Test that Basic auth credentials are redacted."""
        mock_response = Mock()
        error_msg = "Authorization: Basic dXNlcjpwYXNzd29yZA=="
        result = sanitize_error_message(error_msg, mock_response)
        assert "dXNlcjpwYXNzd29yZA==" not in result
        assert "[REDACTED]" in result

    def test_sanitize_password_parameter(self):
        """Test that password parameters are redacted."""
        mock_response = Mock()
        error_msg = "POST /login?username=admin&password=secret123 -> 401"
        result = sanitize_error_message(error_msg, mock_response)
        assert "secret123" not in result
        assert "password=[redacted]" in result.lower()

    def test_truncate_long_errors(self):
        """Test that long error messages are truncated."""
        mock_response = Mock()
        error_msg = "Error: " + ("x" * 1000)
        result = sanitize_error_message(error_msg, mock_response)
        assert len(result) <= 520  # 500 + "[TRUNCATED]"
        assert "[TRUNCATED]" in result

    def test_multiple_sensitive_patterns(self):
        """Test sanitization of multiple sensitive patterns in one message."""
        mock_response = Mock()
        error_msg = (
            "Request failed: api_key=abc123, password=secret, "
            "Authorization: Bearer token456, X-API-Key: key789"
        )
        result = sanitize_error_message(error_msg, mock_response)
        assert "abc123" not in result
        assert "secret" not in result
        assert "token456" not in result
        assert "key789" not in result
        assert result.count("[REDACTED]") >= 4


class TestSanitizationSecurity:
    """Test security aspects of sanitization."""

    def test_prevent_credential_leakage(self):
        """Test that credentials don't leak in any form."""
        sensitive_data = {
            "api_key": "sk_live_51234567890abcdef",
            "password": "SuperSecret123!",
            "token": "ghp_1234567890abcdefghijklmnopqrstu",
            "secret": "secret_key_base_development",
        }

        result = sanitize_for_logging(sensitive_data)

        # Verify no sensitive values appear in sanitized output
        result_str = str(result)
        for key, value in sensitive_data.items():
            assert value not in result_str

    def test_prevent_sql_injection_in_logs(self):
        """Test that SQL injection attempts in data don't bypass sanitization."""
        data = {
            "username": "admin",
            "password": "secret' OR '1'='1",
            "query": "SELECT * FROM users WHERE password='secret'",
        }
        result = sanitize_for_logging(data)
        assert result["password"] == "[REDACTED]"
        # Query is not a sensitive field, so it's preserved
        assert result["query"] == data["query"]

    def test_prevent_log_injection(self):
        """Test that log injection attempts are handled."""
        # Newlines and special chars in sensitive fields should be redacted anyway
        data = {"password": "secret\n[FORGED LOG ENTRY]\npassword: disclosed"}
        result = sanitize_for_logging(data)
        assert result["password"] == "[REDACTED]"
        assert "disclosed" not in str(result)

    def test_handle_binary_data(self):
        """Test handling of binary data."""
        data = {"file": b"binary data here", "password": "secret"}
        result = sanitize_for_logging(data)
        # Binary should be preserved (or handled gracefully)
        assert result["password"] == "[REDACTED]"

    def test_handle_none_values(self):
        """Test handling of None values."""
        data = {"username": "admin", "password": None, "api_key": None}
        result = sanitize_for_logging(data)
        assert result["username"] == "admin"
        assert result["password"] == "[REDACTED]"
        assert result["api_key"] == "[REDACTED]"

    def test_session_cookie_sanitization(self):
        """Test that session cookies are sanitized."""
        data = {
            "headers": {
                "Cookie": "session=abc123; csrf_token=def456",
                "Set-Cookie": "session=new_session_id",
            }
        }
        result = sanitize_for_logging(data)
        # Cookie headers should be redacted
        assert result["headers"]["Cookie"] == "[REDACTED]"
        assert result["headers"]["Set-Cookie"] == "[REDACTED]"


class TestEdgeCases:
    """Test edge cases in sanitization."""

    def test_empty_dict(self):
        """Test sanitization of empty dict."""
        result = sanitize_for_logging({})
        assert result == {}

    def test_empty_list(self):
        """Test sanitization of empty list."""
        result = sanitize_for_logging([])
        assert result == []

    def test_none_input(self):
        """Test sanitization of None."""
        result = sanitize_for_logging(None)
        assert result is None

    def test_primitive_types(self):
        """Test sanitization of primitive types."""
        assert sanitize_for_logging(123) == 123
        assert sanitize_for_logging(45.67) == 45.67
        assert sanitize_for_logging(True) is True
        assert sanitize_for_logging("string") == "string"

    def test_circular_reference_protection(self):
        """Test protection against circular references."""
        data = {"key": "value"}
        data["self"] = data  # Create circular reference

        # Should not crash, but handle gracefully
        try:
            result = sanitize_for_logging(data)
            # If it completes, verify it worked
            assert "key" in result
        except RecursionError:
            # Should be prevented by max depth check
            pytest.fail("Should not raise RecursionError")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
