#!/usr/bin/env python3
"""
Quick Redis Integration Test
Verifies Redis connectivity and basic order flow
"""

import redis
import json
import time
import sys

# Color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

def print_status(message, status="info"):
    """Print colored status message"""
    color = {"success": GREEN, "error": RED, "warning": YELLOW, "info": BLUE}.get(status, RESET)
    symbol = {"success": "✓", "error": "✗", "warning": "⚠", "info": "ℹ"}.get(status, "•")
    print(f"{color}[{symbol}]{RESET} {message}")


def main():
    print()
    print("=" * 70)
    print(f"  {BLUE}GoQuant Redis Integration Test{RESET}")
    print("=" * 70)
    print()

    # Test 1: Redis Connection
    print_status("Testing Redis connection...", "info")
    try:
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        result = r.ping()
        if result:
            print_status("Redis is connected and responding", "success")
        else:
            print_status("Redis connection failed", "error")
            return 1
    except Exception as e:
        print_status(f"Redis connection error: {e}", "error")
        return 1

    # Test 2: Redis Queue Operations
    print()
    print_status("Testing Redis queue operations...", "info")
    try:
        # Clear test queue
        r.delete("test_order_queue")
        
        # Push test order
        test_order = {
            "id": "TEST-001",
            "symbol": "BTC-USDT",
            "order_type": "limit",
            "side": "buy",
            "quantity": "1.0",
            "price": "60000.00",
            "timestamp": int(time.time())
        }
        
        r.rpush("test_order_queue", json.dumps(test_order))
        print_status("Order pushed to Redis queue", "success")
        
        # Pop order
        order_json = r.lpop("test_order_queue")
        if order_json:
            retrieved_order = json.loads(order_json)
            if retrieved_order["id"] == "TEST-001":
                print_status("Order retrieved from Redis queue correctly", "success")
            else:
                print_status("Order data mismatch", "error")
                return 1
        else:
            print_status("Failed to retrieve order from queue", "error")
            return 1
            
    except Exception as e:
        print_status(f"Queue operation error: {e}", "error")
        return 1

    # Test 3: Redis Pub/Sub
    print()
    print_status("Testing Redis Pub/Sub...", "info")
    try:
        # Test publish
        test_trade = {
            "trade_id": "T0001",
            "symbol": "BTC-USDT",
            "price": "60000.00",
            "quantity": "0.5"
        }
        
        subscribers = r.publish("test_trade_events", json.dumps(test_trade))
        print_status(f"Published to channel (subscribers: {subscribers})", "success")
        
    except Exception as e:
        print_status(f"Pub/Sub error: {e}", "error")
        return 1

    # Test 4: Check actual order queue status
    print()
    print_status("Checking GoQuant order queue status...", "info")
    try:
        queue_length = r.llen("order_queue")
        print_status(f"Current order queue length: {queue_length}", "info")
        
        if queue_length > 0:
            print_status(f"There are {queue_length} pending orders in the queue", "warning")
        else:
            print_status("Order queue is empty (ready for testing)", "success")
            
    except Exception as e:
        print_status(f"Queue check error: {e}", "error")

    # Test 5: Check Redis memory usage
    print()
    print_status("Redis server info...", "info")
    try:
        info = r.info("memory")
        used_memory_mb = info.get("used_memory", 0) / (1024 * 1024)
        print(f"  Memory used: {used_memory_mb:.2f} MB")
        
        info = r.info("stats")
        total_commands = info.get("total_commands_processed", 0)
        print(f"  Total commands processed: {total_commands}")
        
    except Exception as e:
        print_status(f"Info retrieval error: {e}", "warning")

    print()
    print("=" * 70)
    print_status("All Redis integration tests passed!", "success")
    print("=" * 70)
    print()
    print(f"{BLUE}Next steps:{RESET}")
    print(f"  1. Start the system: python start_system.py")
    print(f"  2. Run integration tests: python test_integration.py")
    print(f"  3. Test API: http://localhost:8000/v1/docs")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
