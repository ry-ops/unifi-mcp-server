#!/usr/bin/env python3
"""
UniFi MCP Server - Credential Testing Utility

This script helps test UniFi credentials before rotating them in production.
It validates both API key and legacy username/password authentication without
affecting the running server or existing sessions.

Usage:
    python test_credentials.py --api-key YOUR_NEW_API_KEY
    python test_credentials.py --username admin --password newpass
    python test_credentials.py --all  # Test all configured credentials
"""

import os
import sys
import argparse
import requests
import urllib3
from pathlib import Path
from typing import Dict, Any, Tuple

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def load_env_file(env_file: str = "secrets.env") -> Dict[str, str]:
    """Load environment variables from file."""
    env_vars = {}
    env_path = Path(env_file)
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    env_vars[key] = value
    return env_vars

def test_api_key(host: str, port: str, api_key: str, verify_tls: bool = False, timeout: int = 15) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Test API key authentication against Integration API.

    Returns:
        (success: bool, message: str, details: dict)
    """
    print(f"Testing API key authentication...")
    print(f"  Host: {host}:{port}")
    print(f"  TLS Verify: {verify_tls}")

    try:
        url = f"https://{host}:{port}/proxy/network/integrations/v1/sites"
        headers = {"X-API-Key": api_key, "Content-Type": "application/json"}

        print(f"  Request: GET {url}")
        response = requests.get(url, headers=headers, verify=verify_tls, timeout=timeout)

        print(f"  Response: {response.status_code} {response.reason}")

        if response.status_code == 200:
            data = response.json()
            sites_count = data.get("count", 0)
            return True, f"API key authentication successful! Found {sites_count} sites.", {
                "status_code": 200,
                "sites_count": sites_count,
                "data_keys": list(data.keys())
            }
        elif response.status_code == 401:
            return False, "API key authentication failed: Invalid or expired API key", {
                "status_code": 401,
                "error": "Unauthorized"
            }
        elif response.status_code == 403:
            return False, "API key authentication failed: Access forbidden (insufficient permissions)", {
                "status_code": 403,
                "error": "Forbidden"
            }
        else:
            return False, f"API key authentication failed: HTTP {response.status_code}", {
                "status_code": response.status_code,
                "error": response.text[:200]
            }

    except requests.exceptions.Timeout:
        return False, f"API key test timed out after {timeout}s", {"error": "Timeout"}
    except requests.exceptions.ConnectionError as e:
        return False, f"Connection error: {str(e)}", {"error": "ConnectionError"}
    except Exception as e:
        return False, f"API key test error: {str(e)}", {"error": str(e)}

def test_legacy_auth(host: str, port: str, username: str, password: str, verify_tls: bool = False, timeout: int = 15) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Test legacy username/password authentication.

    Returns:
        (success: bool, message: str, details: dict)
    """
    print(f"Testing legacy cookie authentication...")
    print(f"  Host: {host}:{port}")
    print(f"  Username: {username}")
    print(f"  TLS Verify: {verify_tls}")

    session = requests.Session()

    try:
        # Step 1: Login
        login_url = f"https://{host}:{port}/api/auth/login"
        login_data = {"username": username, "password": password}

        print(f"  Request: POST {login_url}")
        response = session.post(login_url, json=login_data, verify=verify_tls, timeout=timeout)

        print(f"  Response: {response.status_code} {response.reason}")

        if response.status_code != 200:
            return False, f"Legacy authentication failed: HTTP {response.status_code}", {
                "status_code": response.status_code,
                "error": response.text[:200]
            }

        # Step 2: Test authenticated request
        test_url = f"https://{host}:{port}/proxy/network/api/s/default/stat/device"
        print(f"  Testing session: GET {test_url}")

        test_response = session.get(test_url, verify=verify_tls, timeout=timeout)
        print(f"  Response: {test_response.status_code} {test_response.reason}")

        if test_response.status_code == 200:
            data = test_response.json()
            devices_count = len(data.get("data", []))
            return True, f"Legacy authentication successful! Session active, found {devices_count} devices.", {
                "status_code": 200,
                "devices_count": devices_count,
                "cookies_set": len(session.cookies)
            }
        else:
            return False, f"Legacy session test failed: HTTP {test_response.status_code}", {
                "status_code": test_response.status_code,
                "error": test_response.text[:200]
            }

    except requests.exceptions.Timeout:
        return False, f"Legacy auth test timed out after {timeout}s", {"error": "Timeout"}
    except requests.exceptions.ConnectionError as e:
        return False, f"Connection error: {str(e)}", {"error": "ConnectionError"}
    except Exception as e:
        return False, f"Legacy auth test error: {str(e)}", {"error": str(e)}
    finally:
        session.close()

def main():
    parser = argparse.ArgumentParser(description="Test UniFi credentials before rotation")
    parser.add_argument("--api-key", help="API key to test")
    parser.add_argument("--username", help="Legacy username to test")
    parser.add_argument("--password", help="Legacy password to test")
    parser.add_argument("--all", action="store_true", help="Test all configured credentials from secrets.env")
    parser.add_argument("--host", help="Override UniFi controller host")
    parser.add_argument("--port", help="Override UniFi controller port")
    parser.add_argument("--verify-tls", action="store_true", help="Enable TLS certificate verification")
    parser.add_argument("--timeout", type=int, default=15, help="Request timeout in seconds (default: 15)")

    args = parser.parse_args()

    # Load environment configuration
    env_vars = load_env_file()

    host = args.host or env_vars.get("UNIFI_GATEWAY_HOST", "")
    port = args.port or env_vars.get("UNIFI_GATEWAY_PORT", "443")
    verify_tls = args.verify_tls or env_vars.get("UNIFI_VERIFY_TLS", "false").lower() in ("true", "1", "yes")

    if not host or host == "HOST":
        print("Error: UNIFI_GATEWAY_HOST not configured. Set in secrets.env or use --host")
        sys.exit(1)

    print("=" * 60)
    print("UniFi Credential Testing Utility")
    print("=" * 60)
    print()

    results = []

    # Test API key
    if args.api_key or args.all:
        api_key = args.api_key or env_vars.get("UNIFI_API_KEY", "")
        if api_key and api_key != "API":
            success, message, details = test_api_key(host, port, api_key, verify_tls, args.timeout)
            results.append(("API Key", success, message, details))
            print()
        elif args.all:
            print("Skipping API key test: Not configured")
            print()

    # Test legacy credentials
    if (args.username and args.password) or args.all:
        username = args.username or env_vars.get("UNIFI_USERNAME", "")
        password = args.password or env_vars.get("UNIFI_PASSWORD", "")
        if username and password and username != "USERNAME":
            success, message, details = test_legacy_auth(host, port, username, password, verify_tls, args.timeout)
            results.append(("Legacy Auth", success, message, details))
            print()
        elif args.all:
            print("Skipping legacy auth test: Not configured")
            print()

    # Print summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)

    if not results:
        print("No credentials tested. Use --api-key, --username/--password, or --all")
        sys.exit(1)

    all_passed = True
    for test_name, success, message, details in results:
        status = "PASS" if success else "FAIL"
        print(f"{test_name:15} [{status}] {message}")
        all_passed = all_passed and success

    print()
    if all_passed:
        print("All credential tests passed! Safe to rotate credentials.")
        sys.exit(0)
    else:
        print("Some credential tests failed! Do NOT rotate failing credentials.")
        sys.exit(1)

if __name__ == "__main__":
    main()
