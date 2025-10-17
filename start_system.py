"""
GoQuant System Startup Script
Launches all services in the correct order with proper health checks
"""

import subprocess
import time
import sys
import os
import requests
from pathlib import Path

# Color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def print_status(message, status="info"):
    """Print colored status message"""
    color = {"success": GREEN, "error": RED, "warning": YELLOW, "info": BLUE}.get(
        status, RESET
    )
    print(f"{color}[{status.upper()}]{RESET} {message}")


def check_redis():
    """Check if Redis is running"""
    try:
        result = subprocess.run(
            ["docker", "exec", "redis", "redis-cli", "ping"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0 and "PONG" in result.stdout
    except Exception as e:
        return False


def start_redis():
    """Start Redis container"""
    print_status("Starting Redis...", "info")

    # Try to start existing container
    result = subprocess.run(
        ["docker", "start", "redis"], capture_output=True, text=True
    )

    if result.returncode != 0:
        # Container doesn't exist, create new one
        result = subprocess.run(
            [
                "docker",
                "run",
                "-d",
                "--name",
                "redis",
                "-p",
                "6379:6379",
                "redis:latest",
            ],
            capture_output=True,
            text=True,
        )

    time.sleep(2)

    if check_redis():
        print_status("Redis started successfully", "success")
        return True
    else:
        print_status("Failed to start Redis", "error")
        return False


def wait_for_service(url, service_name, max_attempts=30):
    """Wait for service to be healthy"""
    print_status(f"Waiting for {service_name}...", "info")

    for i in range(max_attempts):
        try:
            response = requests.get(url, timeout=2)
            if response.status_code in [
                200,
                503,
            ]:  # 503 is OK for services without Redis
                print_status(f"{service_name} is ready", "success")
                return True
        except requests.exceptions.RequestException:
            pass

        time.sleep(1)
        if (i + 1) % 5 == 0:
            print_status(
                f"Still waiting for {service_name}... ({i + 1}/{max_attempts})",
                "warning",
            )

    print_status(f"{service_name} failed to start", "error")
    return False


def main():
    """Main startup routine"""
    print()
    print("=" * 70)
    print("  GoQuant Trading System - Startup Script")
    print("=" * 70)
    print()

    # Get project root directory
    project_root = Path(__file__).parent

    # Step 1: Check/Start Redis
    print_status("Step 1: Checking Redis", "info")
    if not check_redis():
        if not start_redis():
            print_status("Cannot proceed without Redis. Exiting.", "error")
            return 1
    else:
        print_status("Redis is already running", "success")

    print()

    # Step 2: Start Order Gateway
    print_status("Step 2: Starting Order Gateway (Port 8000)", "info")
    order_gateway_dir = project_root / "order-gateway"

    try:
        order_gateway_process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "src.main:app",
                "--host",
                "0.0.0.0",
                "--port",
                "8000",
            ],
            cwd=str(order_gateway_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        if not wait_for_service("http://localhost:8000/health", "Order Gateway"):
            print_status("Failed to start Order Gateway", "error")
            order_gateway_process.kill()
            return 1

    except Exception as e:
        print_status(f"Error starting Order Gateway: {e}", "error")
        return 1

    print()

    # Step 3: Start Market Data Service
    print_status("Step 3: Starting Market Data Service (Port 8001)", "info")
    market_data_dir = project_root / "market-data"

    try:
        market_data_process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "src.main:app",
                "--host",
                "0.0.0.0",
                "--port",
                "8001",
            ],
            cwd=str(market_data_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        if not wait_for_service("http://localhost:8001/health", "Market Data Service"):
            print_status("Failed to start Market Data Service", "error")
            market_data_process.kill()
            order_gateway_process.kill()
            return 1

    except Exception as e:
        print_status(f"Error starting Market Data Service: {e}", "error")
        order_gateway_process.kill()
        return 1

    print()

    # Step 4: Start C++ Matching Engine
    print_status("Step 4: Starting C++ Matching Engine", "info")
    engine_exe = (
        project_root
        / "matching-engine"
        / "build"
        / "src"
        / "Debug"
        / "engine_runner.exe"
    )

    if not engine_exe.exists():
        print_status(f"Engine executable not found at {engine_exe}", "error")
        print_status("Please build the C++ engine first:", "warning")
        print_status("  cd matching-engine/build", "info")
        print_status("  cmake --build . --config Debug", "info")
        market_data_process.kill()
        order_gateway_process.kill()
        return 1

    try:
        engine_process = subprocess.Popen(
            [str(engine_exe)],
            cwd=str(engine_exe.parent),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        time.sleep(2)

        if engine_process.poll() is not None:
            print_status("C++ Engine exited unexpectedly", "error")
            stdout, stderr = engine_process.communicate()
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
            market_data_process.kill()
            order_gateway_process.kill()
            return 1

        print_status("C++ Matching Engine started", "success")

    except Exception as e:
        print_status(f"Error starting C++ Engine: {e}", "error")
        market_data_process.kill()
        order_gateway_process.kill()
        return 1

    print()
    print("=" * 70)
    print_status("ALL SERVICES RUNNING!", "success")
    print("=" * 70)
    print()
    print(f"{BLUE}Service URLs:{RESET}")
    print(f"  • Order Gateway:     http://localhost:8000")
    print(f"  • API Documentation: http://localhost:8000/v1/docs")
    print(f"  • Market Data:       http://localhost:8001")
    print(f"  • WebSocket:         ws://localhost:8001/ws/market-data")
    print(f"  • Health Checks:")
    print(f"    - Order Gateway:   http://localhost:8000/health")
    print(f"    - Market Data:     http://localhost:8001/health")
    print()
    print(f"{YELLOW}Press Ctrl+C to stop all services{RESET}")
    print()

    # Keep running and monitor processes
    try:
        while True:
            time.sleep(1)

            # Check if any process died
            if order_gateway_process.poll() is not None:
                print_status("Order Gateway died unexpectedly", "error")
                break
            if market_data_process.poll() is not None:
                print_status("Market Data Service died unexpectedly", "error")
                break
            if engine_process.poll() is not None:
                print_status("C++ Engine died unexpectedly", "error")
                break

    except KeyboardInterrupt:
        print()
        print_status("Shutting down all services...", "warning")

        # Graceful shutdown
        order_gateway_process.terminate()
        market_data_process.terminate()
        engine_process.terminate()

        # Wait for termination
        time.sleep(2)

        # Force kill if still running
        order_gateway_process.kill()
        market_data_process.kill()
        engine_process.kill()

        print_status("All services stopped", "success")

    return 0


if __name__ == "__main__":
    sys.exit(main())
