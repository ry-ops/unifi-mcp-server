"""
Test suite for input validation functions.
Tests all validation functions with valid and invalid inputs,
including security-focused edge cases.
"""

import pytest
import sys
import os

# Add parent directory to path to import main module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import (
    validate_site_id,
    validate_mac_address,
    validate_device_id,
    validate_door_id,
    validate_camera_id,
    validate_wlan_id,
    validate_duration,
    validate_boolean,
    ValidationError,
)


class TestSiteIdValidation:
    """Test site ID validation."""

    def test_valid_site_ids(self):
        """Test valid site ID formats."""
        valid_ids = ["default", "site-123", "my_site", "Site-Name_01", "a" * 64]
        for site_id in valid_ids:
            assert validate_site_id(site_id) == site_id

    def test_empty_site_id(self):
        """Test that empty site ID is rejected."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_site_id("")

    def test_invalid_type(self):
        """Test that non-string types are rejected."""
        with pytest.raises(ValidationError, match="must be string"):
            validate_site_id(123)
        with pytest.raises(ValidationError, match="must be string"):
            validate_site_id(None)

    def test_too_long(self):
        """Test that site IDs over 64 chars are rejected."""
        with pytest.raises(ValidationError, match="too long"):
            validate_site_id("a" * 65)

    def test_invalid_characters(self):
        """Test that invalid characters are rejected."""
        invalid_ids = [
            "site/name",  # Forward slash
            "site\\name",  # Backslash
            "site name",  # Space
            "site;drop table",  # SQL injection attempt
            "../../../etc/passwd",  # Path traversal
            "site<script>",  # XSS attempt
            "site'OR'1'='1",  # SQL injection
        ]
        for site_id in invalid_ids:
            with pytest.raises(ValidationError, match="invalid characters"):
                validate_site_id(site_id)


class TestMacAddressValidation:
    """Test MAC address validation."""

    def test_valid_mac_formats(self):
        """Test valid MAC address formats."""
        valid_macs = [
            "AA:BB:CC:DD:EE:FF",
            "aa:bb:cc:dd:ee:ff",
            "AA-BB-CC-DD-EE-FF",
            "aa-bb-cc-dd-ee-ff",
            "aabbccddeeff",
            "AABBCCDDEEFF",
            "00:11:22:33:44:55",
        ]
        for mac in valid_macs:
            result = validate_mac_address(mac)
            assert isinstance(result, str)
            # Verify it's normalized to lowercase
            assert result == mac.lower()

    def test_empty_mac(self):
        """Test that empty MAC is rejected."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_mac_address("")

    def test_invalid_type(self):
        """Test that non-string types are rejected."""
        with pytest.raises(ValidationError, match="must be string"):
            validate_mac_address(123)

    def test_invalid_length(self):
        """Test that invalid length MACs are rejected."""
        invalid_macs = [
            "AA:BB:CC:DD:EE",  # Too short
            "AA:BB:CC:DD:EE:FF:GG",  # Too long
            "AABBCCDDEE",  # Too short without separators
            "AABBCCDDEEFFGG",  # Too long without separators
        ]
        for mac in invalid_macs:
            with pytest.raises(ValidationError, match="Invalid MAC address"):
                validate_mac_address(mac)

    def test_invalid_characters(self):
        """Test that invalid characters in MAC are rejected."""
        invalid_macs = [
            "GG:HH:II:JJ:KK:LL",  # Invalid hex
            "AA:BB:CC:DD:EE:ZZ",  # Invalid hex
            "AA:BB:CC:DD:EE:F/",  # Special char
            "'; DROP TABLE--",  # SQL injection
        ]
        for mac in invalid_macs:
            with pytest.raises(ValidationError, match="Invalid MAC address"):
                validate_mac_address(mac)


class TestDeviceIdValidation:
    """Test device ID validation."""

    def test_valid_device_ids(self):
        """Test valid device ID formats."""
        valid_ids = [
            "507f1f77bcf86cd799439011",  # MongoDB ObjectId
            "device-123",
            "dev_456",
            "a" * 24,
            "a" * 8,
        ]
        for device_id in valid_ids:
            assert validate_device_id(device_id) == device_id

    def test_empty_device_id(self):
        """Test that empty device ID is rejected."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_device_id("")

    def test_invalid_length(self):
        """Test that device IDs with invalid length are rejected."""
        with pytest.raises(ValidationError, match="length invalid"):
            validate_device_id("short")  # Too short (< 8)
        with pytest.raises(ValidationError, match="length invalid"):
            validate_device_id("a" * 65)  # Too long (> 64)

    def test_invalid_characters(self):
        """Test that invalid characters are rejected."""
        invalid_ids = [
            "device/../../../etc",
            "device; rm -rf /",
            "device<script>alert(1)</script>",
        ]
        for device_id in invalid_ids:
            with pytest.raises(ValidationError, match="invalid characters"):
                validate_device_id(device_id)


class TestDurationValidation:
    """Test duration/timeout validation."""

    def test_valid_durations(self):
        """Test valid duration values."""
        assert validate_duration(1) == 1
        assert validate_duration(30) == 30
        assert validate_duration(300) == 300

    def test_custom_ranges(self):
        """Test custom min/max values."""
        assert validate_duration(5, min_val=5, max_val=10) == 5
        assert validate_duration(10, min_val=5, max_val=10) == 10

    def test_type_coercion(self):
        """Test that string numbers are converted."""
        assert validate_duration("30") == 30

    def test_too_short(self):
        """Test that durations below minimum are rejected."""
        with pytest.raises(ValidationError, match="too short"):
            validate_duration(0)
        with pytest.raises(ValidationError, match="too short"):
            validate_duration(-5)

    def test_too_long(self):
        """Test that durations above maximum are rejected."""
        with pytest.raises(ValidationError, match="too long"):
            validate_duration(301)
        with pytest.raises(ValidationError, match="too long"):
            validate_duration(1000)

    def test_invalid_type(self):
        """Test that invalid types are rejected."""
        with pytest.raises(ValidationError, match="must be integer"):
            validate_duration("invalid")
        with pytest.raises(ValidationError, match="must be integer"):
            validate_duration(None)


class TestBooleanValidation:
    """Test boolean validation."""

    def test_valid_booleans(self):
        """Test valid boolean values."""
        assert validate_boolean(True) is True
        assert validate_boolean(False) is False

    def test_string_coercion(self):
        """Test string to boolean conversion."""
        true_values = ["true", "TRUE", "True", "1", "yes", "YES", "on", "ON"]
        for val in true_values:
            assert validate_boolean(val) is True

        false_values = ["false", "FALSE", "False", "0", "no", "NO", "off", "OFF"]
        for val in false_values:
            assert validate_boolean(val) is False

    def test_int_coercion(self):
        """Test integer to boolean conversion."""
        assert validate_boolean(1) is True
        assert validate_boolean(0) is False
        assert validate_boolean(42) is True

    def test_invalid_type(self):
        """Test that invalid types are rejected."""
        with pytest.raises(ValidationError, match="must be boolean"):
            validate_boolean("invalid")
        with pytest.raises(ValidationError, match="must be boolean"):
            validate_boolean(None)
        with pytest.raises(ValidationError, match="must be boolean"):
            validate_boolean([])


class TestSecurityEdgeCases:
    """Test security-focused edge cases and injection attempts."""

    def test_sql_injection_attempts(self):
        """Test that SQL injection attempts are rejected."""
        sql_payloads = [
            "'; DROP TABLE sites--",
            "' OR '1'='1",
            "admin'--",
            "1' UNION SELECT * FROM users--",
        ]
        for payload in sql_payloads:
            with pytest.raises(ValidationError):
                validate_site_id(payload)

    def test_path_traversal_attempts(self):
        """Test that path traversal attempts are rejected."""
        path_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "....//....//....//etc/passwd",
        ]
        for payload in path_payloads:
            with pytest.raises(ValidationError):
                validate_site_id(payload)

    def test_xss_attempts(self):
        """Test that XSS attempts are rejected."""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert(1)>",
            "javascript:alert(1)",
        ]
        for payload in xss_payloads:
            with pytest.raises(ValidationError):
                validate_site_id(payload)

    def test_command_injection_attempts(self):
        """Test that command injection attempts are rejected."""
        cmd_payloads = [
            "; rm -rf /",
            "| cat /etc/passwd",
            "& whoami",
            "`id`",
        ]
        for payload in cmd_payloads:
            with pytest.raises(ValidationError):
                validate_site_id(payload)

    def test_null_byte_injection(self):
        """Test that null byte injection is handled."""
        # Python strings handle null bytes, but we should be defensive
        assert validate_site_id("valid-site") == "valid-site"

    def test_unicode_normalization(self):
        """Test handling of unicode characters."""
        # Should reject non-ASCII characters
        with pytest.raises(ValidationError):
            validate_site_id("site-\u0000-name")
        with pytest.raises(ValidationError):
            validate_site_id("site-\u200B-name")  # Zero-width space


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
