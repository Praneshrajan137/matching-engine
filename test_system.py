"""
GoQuant System Test Script
Tests end-to-end functionality of the trading system
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuration
ORDER_GATEWAY_URL = "http://localhost:8000"
MARKET_DATA_URL = "http://localhost:8001"

# Color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"


def print_header(title):
    """Print section header"""
    print()
    print("=" * 70)
    print(f"  {title}")
    print("=" * 70)
    print()


def print_test(test_name, passed, details=""):
    """Print test result"""
    status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
    print(f"{status} {test_name}")
    if details:
        print(f"       {CYAN}{details}{RESET}")


def test_health_checks():
    """Test 1: Health check endpoints"""
    print_header("Test 1: Health Checks")

    # Test Order Gateway
    try:
        response = requests.get(f"{ORDER_GATEWAY_URL}/health", timeout=5)
        order_gateway_healthy = response.status_code in [200, 503]
        redis_status = response.json().get("redis", "unknown")
        print_test(
            "Order Gateway Health",
            order_gateway_healthy,
            f"Status: {response.status_code}, Redis: {redis_status}",
        )
    except Exception as e:
        print_test("Order Gateway Health", False, f"Error: {e}")
        return False

    # Test Market Data Service
    try:
        response = requests.get(f"{MARKET_DATA_URL}/health", timeout=5)
        market_data_healthy = response.status_code in [200, 503]
        redis_status = response.json().get("redis", "unknown")
        print_test(
            "Market Data Service Health",
            market_data_healthy,
            f"Status: {response.status_code}, Redis: {redis_status}",
        )
    except Exception as e:
        print_test("Market Data Service Health", False, f"Error: {e}")
        return False

    return order_gateway_healthy and market_data_healthy


def test_order_submission():
    """Test 2: Order submission"""
    print_header("Test 2: Order Submission")

    test_orders = [
        {
            "name": "Market Buy Order",
            "payload": {
                "symbol": "BTC-USDT",
                "order_type": "market",
                "side": "buy",
                "quantity": "0.1",
            },
        },
        {
            "name": "Limit Sell Order",
            "payload": {
                "symbol": "BTC-USDT",
                "order_type": "limit",
                "side": "sell",
                "price": "60000.00",
                "quantity": "0.5",
            },
        },
        {
            "name": "Limit Buy Order",
            "payload": {
                "symbol": "BTC-USDT",
                "order_type": "limit",
                "side": "buy",
                "price": "59900.00",
                "quantity": "1.0",
            },
        },
        {
            "name": "IOC Order",
            "payload": {
                "symbol": "BTC-USDT",
                "order_type": "ioc",
                "side": "buy",
                "price": "60000.00",
                "quantity": "0.3",
            },
        },
        {
            "name": "FOK Order",
            "payload": {
                "symbol": "BTC-USDT",
                "order_type": "fok",
                "side": "sell",
                "price": "59900.00",
                "quantity": "0.2",
            },
        },
    ]

    successful_orders = []

    for test_order in test_orders:
        try:
            response = requests.post(
                f"{ORDER_GATEWAY_URL}/v1/orders",
                json=test_order["payload"],
                headers={"Content-Type": "application/json"},
                timeout=5,
            )

            if response.status_code == 201:
                order_id = response.json().get("order_id")
                successful_orders.append(order_id)
                print_test(test_order["name"], True, f"Order ID: {order_id[:8]}...")
            else:
                print_test(
                    test_order["name"],
                    False,
                    f"HTTP {response.status_code}: {response.text[:50]}",
                )
        except Exception as e:
            print_test(test_order["name"], False, f"Error: {e}")

    print()
    print(
        f"  {BLUE}Successfully submitted: {len(successful_orders)}/{len(test_orders)} orders{RESET}"
    )

    return len(successful_orders) > 0


def test_validation():
    """Test 3: Input validation"""
    print_header("Test 3: Input Validation")

    invalid_orders = [
        {
            "name": "Missing price (Limit order)",
            "payload": {
                "symbol": "BTC-USDT",
                "order_type": "limit",
                "side": "buy",
                "quantity": "1.0",
            },
            "expected_status": 422,
        },
        {
            "name": "Invalid side",
            "payload": {
                "symbol": "BTC-USDT",
                "order_type": "market",
                "side": "invalid",
                "quantity": "1.0",
            },
            "expected_status": 422,
        },
        {
            "name": "Negative quantity",
            "payload": {
                "symbol": "BTC-USDT",
                "order_type": "market",
                "side": "buy",
                "quantity": "-1.0",
            },
            "expected_status": 422,
        },
        {
            "name": "Market order with price",
            "payload": {
                "symbol": "BTC-USDT",
                "order_type": "market",
                "side": "buy",
                "quantity": "1.0",
                "price": "60000.00",
            },
            "expected_status": 422,
        },
    ]

    passed = 0
    for test in invalid_orders:
        try:
            response = requests.post(
                f"{ORDER_GATEWAY_URL}/v1/orders",
                json=test["payload"],
                headers={"Content-Type": "application/json"},
                timeout=5,
            )

            validation_passed = response.status_code == test["expected_status"]
            if validation_passed:
                passed += 1

            print_test(
                test["name"],
                validation_passed,
                f"Expected {test['expected_status']}, Got {response.status_code}",
            )
        except Exception as e:
            print_test(test["name"], False, f"Error: {e}")

    print()
    print(f"  {BLUE}Validation tests passed: {passed}/{len(invalid_orders)}{RESET}")

    return passed == len(invalid_orders)


def test_performance():
    """Test 4: Basic performance test"""
    print_header("Test 4: Basic Performance Test")

    num_orders = 100
    print(f"  Submitting {num_orders} orders...")

    successful = 0
    failed = 0
    latencies = []

    start_time = time.time()

    for i in range(num_orders):
        order = {
            "symbol": "BTC-USDT",
            "order_type": "limit",
            "side": "buy" if i % 2 == 0 else "sell",
            "price": f"{60000 + (i % 100)}",
            "quantity": "0.1",
        }

        order_start = time.time()
        try:
            response = requests.post(
                f"{ORDER_GATEWAY_URL}/v1/orders", json=order, timeout=5
            )
            order_end = time.time()

            latency_ms = (order_end - order_start) * 1000
            latencies.append(latency_ms)

            if response.status_code == 201:
                successful += 1
            else:
                failed += 1
        except Exception as e:
            failed += 1
            order_end = time.time()
            latencies.append((order_end - order_start) * 1000)

    end_time = time.time()
    total_time = end_time - start_time
    throughput = num_orders / total_time

    print()
    print(f"  {CYAN}Results:{RESET}")
    print(f"    Total Orders:    {num_orders}")
    print(f"    Successful:      {successful}")
    print(f"    Failed:          {failed}")
    print(f"    Total Time:      {total_time:.2f}s")
    print(f"    Throughput:      {throughput:.2f} orders/sec")

    if latencies:
        avg_latency = sum(latencies) / len(latencies)
        min_latency = min(latencies)
        max_latency = max(latencies)
        print(f"    Avg Latency:     {avg_latency:.2f}ms")
        print(f"    Min Latency:     {min_latency:.2f}ms")
        print(f"    Max Latency:     {max_latency:.2f}ms")

    print()

    success_rate = (successful / num_orders) * 100
    print_test(
        "Performance Test", success_rate >= 95, f"Success rate: {success_rate:.1f}%"
    )

    return success_rate >= 95


def test_api_documentation():
    """Test 5: API documentation availability"""
    print_header("Test 5: API Documentation")

    try:
        response = requests.get(f"{ORDER_GATEWAY_URL}/v1/docs", timeout=5)
        docs_available = response.status_code == 200
        print_test(
            "API Documentation (Swagger UI)",
            docs_available,
            f"URL: {ORDER_GATEWAY_URL}/v1/docs",
        )
    except Exception as e:
        print_test("API Documentation", False, f"Error: {e}")
        return False

    return docs_available


def main():
    """Run all tests"""
    print()
    print("=" * 70)
    print(f"{BLUE}  GoQuant Trading System - End-to-End Test Suite{RESET}")
    print("=" * 70)
    print()
    print(f"  Testing against:")
    print(f"    Order Gateway:  {ORDER_GATEWAY_URL}")
    print(f"    Market Data:    {MARKET_DATA_URL}")
    print()

    # Run all tests
    results = {}

    try:
        results["health"] = test_health_checks()
        results["orders"] = test_order_submission()
        results["validation"] = test_validation()
        results["performance"] = test_performance()
        results["documentation"] = test_api_documentation()
    except KeyboardInterrupt:
        print()
        print(f"{YELLOW}Tests interrupted by user{RESET}")
        return 1

    # Summary
    print_header("Test Summary")

    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)

    test_names = {
        "health": "Health Checks",
        "orders": "Order Submission",
        "validation": "Input Validation",
        "performance": "Performance Test",
        "documentation": "API Documentation",
    }

    for key, value in results.items():
        status = f"{GREEN}PASS{RESET}" if value else f"{RED}FAIL{RESET}"
        print(f"  [{status}] {test_names[key]}")

    print()
    print("=" * 70)

    if passed_tests == total_tests:
        print(f"{GREEN}  ✓ ALL TESTS PASSED ({passed_tests}/{total_tests}){RESET}")
        print("=" * 70)
        print()
        print(f"{BLUE}System is functioning correctly!{RESET}")
        return_code = 0
    else:
        print(
            f"{YELLOW}  ⚠ SOME TESTS FAILED ({passed_tests}/{total_tests} passed){RESET}"
        )
        print("=" * 70)
        print()
        print(f"{YELLOW}System has issues that need attention{RESET}")
        return_code = 1

    print()
    return return_code


if __name__ == "__main__":
    sys.exit(main())
