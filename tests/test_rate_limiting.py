"""
Test suite for rate limiting functionality.
Tests rate limiter behavior, limits, and security aspects.
"""

import pytest
import time
import sys
import os
from threading import Thread

# Add parent directory to path to import main module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import RateLimiter, RateLimitError


class TestRateLimiter:
    """Test rate limiter functionality."""

    def test_basic_rate_limiting(self):
        """Test basic rate limiting behavior."""
        limiter = RateLimiter(calls_per_minute=5, calls_per_hour=10)

        # Should allow first 5 calls
        for i in range(5):
            allowed, error = limiter.check_rate_limit("/test/endpoint")
            assert allowed is True
            assert error is None

        # Should block 6th call
        allowed, error = limiter.check_rate_limit("/test/endpoint")
        assert allowed is False
        assert error is not None
        assert "calls/minute" in error

    def test_per_endpoint_limiting(self):
        """Test that rate limits are per-endpoint."""
        limiter = RateLimiter(calls_per_minute=3, calls_per_hour=10)

        # Endpoint 1: Use all 3 calls
        for i in range(3):
            allowed, _ = limiter.check_rate_limit("/endpoint1")
            assert allowed is True

        # Endpoint 1: Should be blocked
        allowed, _ = limiter.check_rate_limit("/endpoint1")
        assert allowed is False

        # Endpoint 2: Should still have calls available
        for i in range(3):
            allowed, _ = limiter.check_rate_limit("/endpoint2")
            assert allowed is True

    def test_hourly_rate_limit(self):
        """Test hourly rate limiting."""
        limiter = RateLimiter(calls_per_minute=100, calls_per_hour=5)

        # Should allow first 5 calls
        for i in range(5):
            allowed, error = limiter.check_rate_limit("/test")
            assert allowed is True

        # Should block 6th call due to hourly limit
        allowed, error = limiter.check_rate_limit("/test")
        assert allowed is False
        assert "calls/hour" in error

    def test_time_window_cleanup(self):
        """Test that old calls are cleaned up after time window."""
        limiter = RateLimiter(calls_per_minute=2, calls_per_hour=10)

        # Use up the minute limit
        limiter.check_rate_limit("/test")
        limiter.check_rate_limit("/test")

        # Should be blocked
        allowed, _ = limiter.check_rate_limit("/test")
        assert allowed is False

        # Simulate time passing by manually manipulating timestamps
        # (In real scenario, would wait 60 seconds)
        limiter.minute_calls["/test"] = [time.time() - 61, time.time() - 61]

        # Should be allowed again after cleanup
        allowed, _ = limiter.check_rate_limit("/test")
        assert allowed is True

    def test_get_stats(self):
        """Test rate limiter statistics."""
        limiter = RateLimiter(calls_per_minute=10, calls_per_hour=50)

        # Make some calls
        for i in range(3):
            limiter.check_rate_limit("/test")

        stats = limiter.get_stats("/test")
        assert stats["endpoint"] == "/test"
        assert stats["calls_last_minute"] == 3
        assert stats["calls_last_hour"] == 3
        assert stats["limit_per_minute"] == 10
        assert stats["limit_per_hour"] == 50
        assert stats["minute_remaining"] == 7
        assert stats["hour_remaining"] == 47

    def test_concurrent_access(self):
        """Test thread-safe concurrent access to rate limiter."""
        limiter = RateLimiter(calls_per_minute=50, calls_per_hour=100)
        results = []

        def make_calls():
            for _ in range(10):
                allowed, _ = limiter.check_rate_limit("/test")
                results.append(allowed)

        # Create 5 threads making 10 calls each = 50 total
        threads = [Thread(target=make_calls) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All 50 calls should succeed (within minute limit)
        assert sum(results) == 50

    def test_error_message_format(self):
        """Test that error messages are properly formatted."""
        limiter = RateLimiter(calls_per_minute=1, calls_per_hour=5)

        # Use up minute limit
        limiter.check_rate_limit("/test")

        # Get error message
        allowed, error = limiter.check_rate_limit("/test")
        assert allowed is False
        assert "Rate limit exceeded" in error
        assert "calls/minute" in error
        assert "Retry in" in error

    def test_zero_limits(self):
        """Test behavior with zero limits (effectively disabled)."""
        limiter = RateLimiter(calls_per_minute=0, calls_per_hour=0)

        # Should block immediately
        allowed, error = limiter.check_rate_limit("/test")
        assert allowed is False

    def test_high_limits(self):
        """Test behavior with very high limits."""
        limiter = RateLimiter(calls_per_minute=10000, calls_per_hour=100000)

        # Should allow many calls
        for i in range(100):
            allowed, _ = limiter.check_rate_limit("/test")
            assert allowed is True


class TestRateLimitSecurity:
    """Test security aspects of rate limiting."""

    def test_dos_protection(self):
        """Test that rate limiter protects against DoS."""
        limiter = RateLimiter(calls_per_minute=5, calls_per_hour=20)

        # Simulate rapid-fire requests
        blocked_count = 0
        for i in range(100):
            allowed, _ = limiter.check_rate_limit("/api/expensive")
            if not allowed:
                blocked_count += 1

        # Should block most requests
        assert blocked_count >= 80  # At least 80 out of 100 blocked

    def test_different_endpoints_isolation(self):
        """Test that different endpoints don't interfere with each other."""
        limiter = RateLimiter(calls_per_minute=3, calls_per_hour=10)

        # Exhaust one endpoint
        for i in range(3):
            limiter.check_rate_limit("/admin/users")

        allowed, _ = limiter.check_rate_limit("/admin/users")
        assert allowed is False

        # Other endpoints should still work
        allowed, _ = limiter.check_rate_limit("/public/info")
        assert allowed is True

    def test_malicious_endpoint_names(self):
        """Test handling of malicious or unusual endpoint names."""
        limiter = RateLimiter(calls_per_minute=5, calls_per_hour=20)

        # Should handle unusual but valid endpoint names
        unusual_endpoints = [
            "/../../etc/passwd",
            "/api/../admin",
            "/test;DROP TABLE;",
            "/test?param=value",
            "/test#fragment",
        ]

        for endpoint in unusual_endpoints:
            allowed, _ = limiter.check_rate_limit(endpoint)
            assert allowed is True  # First call should work

            # Stats should track the endpoint as-is
            stats = limiter.get_stats(endpoint)
            assert stats["calls_last_minute"] == 1


class TestRateLimitIntegration:
    """Integration tests for rate limiting with HTTP functions."""

    def test_rate_limit_error_exception(self):
        """Test that RateLimitError can be raised and caught."""
        limiter = RateLimiter(calls_per_minute=1, calls_per_hour=5)

        # Use up the limit
        limiter.check_rate_limit("/test")

        # Check that we can detect the limit
        allowed, error_msg = limiter.check_rate_limit("/test")
        assert not allowed

        # Verify we can raise an exception with the error message
        try:
            raise RateLimitError(error_msg)
        except RateLimitError as e:
            assert "Rate limit exceeded" in str(e)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
