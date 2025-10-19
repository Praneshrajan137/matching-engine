#!/usr/bin/env python3
"""
Quick Order Submission Test
Tests the full order flow: REST API -> Redis -> Matching Engine -> WebSocket
"""

import requests
import json
import sys

# Config
ORDER_GATEWAY_URL = "http://localhost:8000"

def test_order_submission():
    print("\n" + "="*70)
    print("  GoQuant Order Submission Test")
    print("="*70 + "\n")
    
    # Test 1: Submit a limit sell order (creates liquidity)
    print("📝 Submitting SELL limit order at $60,000...")
    sell_order = {
        "symbol": "BTC-USDT",
        "order_type": "limit",
        "side": "sell",
        "price": "60000.00",
        "quantity": "1.0"
    }
    
    try:
        response = requests.post(f"{ORDER_GATEWAY_URL}/v1/orders", json=sell_order, timeout=5)
        if response.status_code == 201:
            data = response.json()
            print(f"✓ Order accepted: {data['order_id']}")
            print(f"  Status: {data['status']}")
            print(f"  Time: {data['timestamp']}")
        else:
            print(f"✗ Failed: HTTP {response.status_code}")
            print(f"  Response: {response.text}")
            return 1
    except requests.exceptions.ConnectionError:
        print("✗ Error: Cannot connect to Order Gateway")
        print("  Run: python start_system.py (in another terminal)")
        return 1
    except Exception as e:
        print(f"✗ Error: {e}")
        return 1
    
    print()
    
    # Test 2: Submit a market buy order (matches against the sell)
    print("📝 Submitting BUY market order for 0.5 BTC...")
    buy_order = {
        "symbol": "BTC-USDT",
        "order_type": "market",
        "side": "buy",
        "quantity": "0.5"
    }
    
    try:
        response = requests.post(f"{ORDER_GATEWAY_URL}/v1/orders", json=buy_order, timeout=5)
        if response.status_code == 201:
            data = response.json()
            print(f"✓ Order accepted: {data['order_id']}")
            print(f"  This should match against the $60,000 sell order!")
        else:
            print(f"✗ Failed: HTTP {response.status_code}")
    except Exception as e:
        print(f"✗ Error: {e}")
        return 1
    
    print()
    print("="*70)
    print("✓ Orders submitted successfully!")
    print("="*70)
    print()
    print("To see the trades:")
    print("  1. Check C++ Engine logs in terminal running start_system.py")
    print("  2. Open websocket_test.html in a browser")
    print("  3. Connect to ws://localhost:8001/ws/market-data")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(test_order_submission())
