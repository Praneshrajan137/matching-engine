"""
Quick Performance Test - Simplified version
Tests a smaller batch to verify throughput quickly
"""

import time
import requests
import json

URL = "http://localhost:8000/v1/orders"
NUM_ORDERS = 1000  # Smaller test for quick results

def main():
    print("=" * 60)
    print("QUICK PERFORMANCE TEST")
    print("=" * 60)
    print(f"Submitting {NUM_ORDERS} orders...")
    print()
    
    # Check connection
    try:
        requests.get("http://localhost:8000/health", timeout=2)
        print("[OK] Order Gateway is running")
    except:
        print("[ERROR] Order Gateway not running on port 8000")
        return
    
    # Submit orders
    start_time = time.time()
    success = 0
    failed = 0
    
    for i in range(NUM_ORDERS):
        order = {
            "symbol": "BTC-USDT",
            "side": "buy" if i % 2 == 0 else "sell",
            "order_type": "limit",
            "price": f"{60000 + (i % 100 - 50):.2f}",
            "quantity": "0.1"
        }
        
        try:
            resp = requests.post(URL, json=order, timeout=5)
            if resp.status_code == 201:
                success += 1
            else:
                failed += 1
        except:
            failed += 1
        
        if (i + 1) % 100 == 0:
            print(f"  Progress: {i+1}/{NUM_ORDERS}")
    
    end_time = time.time()
    total_time = end_time - start_time
    throughput = NUM_ORDERS / total_time
    
    # Results
    print()
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Total Time:    {total_time:.2f} seconds")
    print(f"Throughput:    {throughput:.2f} orders/sec")
    print(f"Success Rate:  {success}/{NUM_ORDERS} ({success/NUM_ORDERS*100:.1f}%)")
    print()
    
    if throughput >= 1000:
        print(f"[PASS] {throughput:.0f} orders/sec >= 1000 orders/sec")
        print("Assignment requirement MET!")
    else:
        print(f"[FAIL] {throughput:.0f} orders/sec < 1000 orders/sec")
        print("Assignment requirement NOT MET")
    
    print("=" * 60)

if __name__ == "__main__":
    main()

