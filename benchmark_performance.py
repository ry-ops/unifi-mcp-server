#!/usr/bin/env python3
"""
Performance benchmarking for UniFi MCP Server

Measures:
1. Rate limiting performance
2. Sanitization performance
3. Validation performance
4. Memory usage during operations
"""
import time
import sys
from typing import Dict, Any, List
from memory_profiler import profile

# Import components to benchmark
import main

def benchmark_rate_limiting(iterations: int = 1000) -> Dict[str, float]:
    """Benchmark rate limiting check performance"""
    limiter = main.RateLimiter(calls_per_minute=60, calls_per_hour=1000)

    start = time.time()
    for i in range(iterations):
        allowed, error = limiter.check_rate_limit(f"endpoint_{i % 10}")
    elapsed = time.time() - start

    return {
        "total_time": elapsed,
        "avg_per_check": elapsed / iterations,
        "checks_per_second": iterations / elapsed
    }

def benchmark_sanitization(iterations: int = 1000) -> Dict[str, float]:
    """Benchmark sanitization performance"""
    test_data = {
        "user": "testuser",
        "password": "secret123",
        "api_key": "sk_test_123",
        "nested": {
            "token": "bearer_xyz",
            "data": ["item1", "item2", "item3"]
        },
        "list": [
            {"id": 1, "secret": "value1"},
            {"id": 2, "password": "value2"}
        ]
    }

    start = time.time()
    for _ in range(iterations):
        result = main.sanitize_for_logging(test_data)
    elapsed = time.time() - start

    return {
        "total_time": elapsed,
        "avg_per_call": elapsed / iterations,
        "calls_per_second": iterations / elapsed
    }

def benchmark_validation(iterations: int = 1000) -> Dict[str, float]:
    """Benchmark input validation performance"""
    test_cases = [
        ("default", main.validate_site_id),
        ("aa:bb:cc:dd:ee:ff", main.validate_mac_address),
        ("device123", main.validate_device_id),
        (30, main.validate_duration),
        (True, main.validate_boolean),
    ]

    start = time.time()
    for _ in range(iterations):
        for value, validator in test_cases:
            try:
                validator(value)
            except:
                pass
    elapsed = time.time() - start

    return {
        "total_time": elapsed,
        "avg_per_validation": elapsed / (iterations * len(test_cases)),
        "validations_per_second": (iterations * len(test_cases)) / elapsed
    }

@profile
def test_memory_usage():
    """Profile memory usage during typical operations"""
    # Create rate limiter with many endpoints
    limiter = main.RateLimiter(calls_per_minute=60, calls_per_hour=1000)

    # Simulate 1000 requests across 50 endpoints
    for i in range(1000):
        endpoint = f"/api/endpoint_{i % 50}"
        limiter.check_rate_limit(endpoint)

    # Test sanitization with large datasets
    large_data = {
        f"key_{i}": {
            "password": f"secret_{i}",
            "data": [{"id": j, "value": f"val_{j}"} for j in range(10)]
        }
        for i in range(100)
    }

    result = main.sanitize_for_logging(large_data)

    return result

def main_benchmark():
    """Run all benchmarks"""
    print("=" * 60)
    print("UniFi MCP Server Performance Benchmarks")
    print("=" * 60)

    # Rate limiting
    print("\n1. Rate Limiting Performance:")
    print("-" * 60)
    rl_results = benchmark_rate_limiting(10000)
    print(f"  Total time: {rl_results['total_time']:.4f}s")
    print(f"  Avg per check: {rl_results['avg_per_check']*1000:.4f}ms")
    print(f"  Checks/sec: {rl_results['checks_per_second']:.0f}")

    # Sanitization
    print("\n2. Sanitization Performance:")
    print("-" * 60)
    san_results = benchmark_sanitization(5000)
    print(f"  Total time: {san_results['total_time']:.4f}s")
    print(f"  Avg per call: {san_results['avg_per_call']*1000:.4f}ms")
    print(f"  Calls/sec: {san_results['calls_per_second']:.0f}")

    # Validation
    print("\n3. Validation Performance:")
    print("-" * 60)
    val_results = benchmark_validation(5000)
    print(f"  Total time: {val_results['total_time']:.4f}s")
    print(f"  Avg per validation: {val_results['avg_per_validation']*1000:.4f}ms")
    print(f"  Validations/sec: {val_results['validations_per_second']:.0f}")

    # Performance recommendations
    print("\n" + "=" * 60)
    print("Performance Analysis:")
    print("=" * 60)

    if rl_results['avg_per_check'] > 0.001:  # > 1ms
        print("⚠️  Rate limiting: Consider optimization if >10k requests/sec expected")
    else:
        print("✅ Rate limiting: Performance is good")

    if san_results['avg_per_call'] > 0.01:  # > 10ms
        print("⚠️  Sanitization: Consider caching for repeated data structures")
    else:
        print("✅ Sanitization: Performance is good")

    if val_results['avg_per_validation'] > 0.001:  # > 1ms
        print("⚠️  Validation: Consider compiled regex patterns")
    else:
        print("✅ Validation: Performance is good")

    print("\n" + "=" * 60)
    print("Memory Profiling:")
    print("=" * 60)
    print("Run with: python -m memory_profiler benchmark_performance.py")
    print("=" * 60)

if __name__ == "__main__":
    main_benchmark()
