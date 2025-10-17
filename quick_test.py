"""
Quick Component Test Script
Tests each component independently to verify functionality
"""

import subprocess
import time
import sys
import os
import json
from pathlib import Path

# Color codes for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def print_header(title):
    """Print section header"""
    print()
    print("=" * 70)
    print(f"  {title}")
    print("=" * 70)
    print()


def test_result(test_name, passed, details=""):
    """Print test result"""
    status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
    print(f"{status} {test_name}")
    if details:
        print(f"       {details}")


def test_redis():
    """Test Redis connectivity"""
    print_header("Test 1: Redis Connection")

    try:
        result = subprocess.run(
            ["docker", "exec", "redis", "redis-cli", "ping"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode == 0 and "PONG" in result.stdout:
            test_result("Redis is running", True, "Response: PONG")

            # Test basic operations
            subprocess.run(
                ["docker", "exec", "redis", "redis-cli", "FLUSHALL"],
                capture_output=True,
            )

            # Test queue operations
            subprocess.run(
                [
                    "docker",
                    "exec",
                    "redis",
                    "redis-cli",
                    "RPUSH",
                    "test_queue",
                    "test_message",
                ],
                capture_output=True,
            )

            result = subprocess.run(
                ["docker", "exec", "redis", "redis-cli", "LLEN", "test_queue"],
                capture_output=True,
                text=True,
            )

            queue_length = result.stdout.strip()
            test_result(
                "Redis queue operations",
                queue_length == "1",
                f"Queue length: {queue_length}",
            )

            return True
        else:
            test_result("Redis is running", False, "Not responding to PING")
            return False

    except subprocess.TimeoutExpired:
        test_result("Redis is running", False, "Connection timeout")
        return False
    except FileNotFoundError:
        test_result("Redis is running", False, "Docker not found")
        return False
    except Exception as e:
        test_result("Redis is running", False, f"Error: {e}")
        return False


def test_cpp_tests():
    """Test C++ unit tests"""
    print_header("Test 2: C++ Unit Tests")

    project_root = Path(__file__).parent

    # Test OrderBook
    order_book_test = (
        project_root
        / "matching-engine"
        / "build"
        / "tests"
        / "Debug"
        / "order_book_tests.exe"
    )

    if order_book_test.exists():
        try:
            result = subprocess.run(
                [str(order_book_test)], capture_output=True, text=True, timeout=10
            )

            passed = "PASSED" in result.stdout and result.returncode == 0

            # Extract test count
            if "[  PASSED  ]" in result.stdout:
                for line in result.stdout.split("\n"):
                    if "[  PASSED  ]" in line and "tests" in line:
                        test_result("OrderBook tests", passed, line.strip())
                        break
            else:
                test_result("OrderBook tests", passed)

        except Exception as e:
            test_result("OrderBook tests", False, f"Error: {e}")
    else:
        test_result(
            "OrderBook tests", False, f"Executable not found at {order_book_test}"
        )

    # Test MatchingEngine
    matching_engine_test = (
        project_root
        / "matching-engine"
        / "build"
        / "tests"
        / "Debug"
        / "matching_engine_tests.exe"
    )

    if matching_engine_test.exists():
        try:
            result = subprocess.run(
                [str(matching_engine_test)], capture_output=True, text=True, timeout=10
            )

            passed = "PASSED" in result.stdout and result.returncode == 0

            # Extract test count
            if "[  PASSED  ]" in result.stdout:
                for line in result.stdout.split("\n"):
                    if "[  PASSED  ]" in line and "tests" in line:
                        test_result("MatchingEngine tests", passed, line.strip())
                        break
            else:
                test_result("MatchingEngine tests", passed)

        except Exception as e:
            test_result("MatchingEngine tests", False, f"Error: {e}")
    else:
        test_result(
            "MatchingEngine tests",
            False,
            f"Executable not found at {matching_engine_test}",
        )


def test_python_imports():
    """Test Python dependencies"""
    print_header("Test 3: Python Dependencies")

    dependencies = [
        ("FastAPI", "fastapi"),
        ("Uvicorn", "uvicorn"),
        ("Redis client", "redis"),
        ("Pydantic", "pydantic"),
        ("WebSockets", "websockets"),
        ("Requests", "requests"),
    ]

    all_passed = True

    for name, module in dependencies:
        try:
            __import__(module)
            test_result(f"{name} installed", True)
        except ImportError:
            test_result(f"{name} installed", False, f"Module '{module}' not found")
            all_passed = False

    return all_passed


def test_python_services():
    """Test Python services can be imported"""
    print_header("Test 4: Python Service Code")

    project_root = Path(__file__).parent

    # Test Order Gateway
    order_gateway_path = project_root / "order-gateway"
    sys.path.insert(0, str(order_gateway_path))

    try:
        os.chdir(order_gateway_path / "src")
        from main import app as order_app

        test_result("Order Gateway imports", True, "FastAPI app loaded")
        order_gateway_ok = True
    except SyntaxError as e:
        test_result("Order Gateway imports", False, f"Syntax error: {e}")
        order_gateway_ok = False
    except Exception as e:
        test_result("Order Gateway imports", False, f"Import error: {e}")
        order_gateway_ok = False

    # Test Market Data
    market_data_path = project_root / "market-data"
    sys.path.insert(0, str(market_data_path))

    try:
        os.chdir(market_data_path / "src")
        from main import app as market_app

        test_result("Market Data imports", True, "FastAPI app loaded")
        market_data_ok = True
    except SyntaxError as e:
        test_result("Market Data imports", False, f"Syntax error: {e}")
        market_data_ok = False
    except Exception as e:
        test_result("Market Data imports", False, f"Import error: {e}")
        market_data_ok = False

    os.chdir(project_root)
    return order_gateway_ok and market_data_ok


def test_cpp_engine():
    """Test C++ engine executable"""
    print_header("Test 5: C++ Matching Engine Executable")

    project_root = Path(__file__).parent
    engine_exe = (
        project_root
        / "matching-engine"
        / "build"
        / "src"
        / "Debug"
        / "engine_runner.exe"
    )

    if engine_exe.exists():
        test_result("Engine executable exists", True, str(engine_exe))

        # Check file size
        size_kb = engine_exe.stat().st_size / 1024
        test_result("Engine size", True, f"{size_kb:.1f} KB")

        # Try to run briefly (will fail without Redis connection but shows it starts)
        try:
            # Start engine and immediately kill it
            proc = subprocess.Popen(
                [str(engine_exe)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Give it a moment to start
            time.sleep(0.5)

            # Check if it's still running
            if proc.poll() is None:
                # Still running, kill it
                proc.terminate()
                test_result("Engine starts", True, "Process started successfully")
                return True
            else:
                # Exited - check why
                stdout, stderr = proc.communicate()
                if "Redis" in stdout or "Redis" in stderr:
                    test_result(
                        "Engine starts", True, "Exits waiting for Redis (expected)"
                    )
                    return True
                else:
                    test_result("Engine starts", False, "Exited unexpectedly")
                    return False

        except Exception as e:
            test_result("Engine starts", False, f"Error: {e}")
            return False
    else:
        test_result("Engine executable exists", False, f"Not found at {engine_exe}")
        return False


def test_simple_api_server():
    """Test if we can start a simple FastAPI server"""
    print_header("Test 6: Simple API Server Test")

    test_code = """
import uvicorn
from fastapi import FastAPI

app = FastAPI()

@app.get("/test")
def test():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=9999)
"""

    # Write test file
    test_file = Path("test_server.py")
    test_file.write_text(test_code)

    try:
        # Start server
        proc = subprocess.Popen(
            [sys.executable, "test_server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Wait for startup
        time.sleep(3)

        # Test connection
        try:
            import requests

            response = requests.get("http://127.0.0.1:9999/test", timeout=2)
            if response.status_code == 200:
                test_result("Simple FastAPI server", True, "Server responds correctly")
                result = True
            else:
                test_result(
                    "Simple FastAPI server", False, f"HTTP {response.status_code}"
                )
                result = False
        except Exception as e:
            test_result("Simple FastAPI server", False, f"Connection failed: {e}")
            result = False

        # Clean up
        proc.terminate()
        test_file.unlink()
        return result

    except Exception as e:
        test_result("Simple FastAPI server", False, f"Error: {e}")
        test_file.unlink()
        return False


def main():
    """Run all component tests"""
    print()
    print("=" * 70)
    print(f"{BLUE}  GoQuant Component Test Suite{RESET}")
    print("=" * 70)
    print()
    print("Testing individual components to identify issues...")

    results = {}

    # Test each component
    results["redis"] = test_redis()
    results["cpp_tests"] = test_cpp_tests()
    results["python_deps"] = test_python_imports()
    results["python_services"] = test_python_services()
    results["cpp_engine"] = test_cpp_engine()
    results["simple_api"] = test_simple_api_server()

    # Summary
    print_header("Test Summary")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    print(f"Component Status:")
    print(
        f"  {'✓' if results.get('redis') else '✗'} Redis: {'Running' if results.get('redis') else 'Not running'}"
    )
    print(
        f"  {'✓' if results.get('cpp_tests') else '✗'} C++ Tests: {'Passing' if results.get('cpp_tests') else 'Failed/Missing'}"
    )
    print(
        f"  {'✓' if results.get('python_deps') else '✗'} Python Dependencies: {'Installed' if results.get('python_deps') else 'Missing'}"
    )
    print(
        f"  {'✓' if results.get('python_services') else '✗'} Python Services: {'Valid' if results.get('python_services') else 'Syntax errors'}"
    )
    print(
        f"  {'✓' if results.get('cpp_engine') else '✗'} C++ Engine: {'Built' if results.get('cpp_engine') else 'Not built'}"
    )
    print(
        f"  {'✓' if results.get('simple_api') else '✗'} FastAPI: {'Working' if results.get('simple_api') else 'Not working'}"
    )

    print()
    print("=" * 70)

    if passed == total:
        print(f"{GREEN}  ✓ ALL COMPONENTS WORKING ({passed}/{total}){RESET}")
        print("=" * 70)
        print()
        print("All components are functional. System should work end-to-end.")
    else:
        print(f"{YELLOW}  ⚠ SOME COMPONENTS FAILING ({passed}/{total}){RESET}")
        print("=" * 70)
        print()

        if not results.get("redis"):
            print("Action needed: Start Redis with 'docker start redis'")
        if not results.get("cpp_tests"):
            print("Action needed: Build C++ tests in matching-engine/build")
        if not results.get("python_deps"):
            print("Action needed: Install Python dependencies")
        if not results.get("python_services"):
            print("Action needed: Fix syntax errors in Python services")
        if not results.get("cpp_engine"):
            print("Action needed: Build C++ engine")
        if not results.get("simple_api"):
            print("Action needed: Check Python/FastAPI installation")

    print()
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
