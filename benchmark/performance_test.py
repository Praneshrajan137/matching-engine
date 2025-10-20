"""
Performance Benchmark: Test Order Processing Throughput
Goal: Demonstrate >1000 orders/sec as required by assignment
"""

import time
import requests
import json
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
import uuid

# Configuration
ORDER_GATEWAY_URL = "http://localhost:8000/v1/orders"
NUM_ORDERS = 1000  # Test with 1000 orders
NUM_THREADS = 12   # Concurrent threads (increased for higher throughput)
SYMBOL = "BTC-USDT"


def generate_random_order(order_num):
    """Generate a random test order"""
    side = "buy" if order_num % 2 == 0 else "sell"
    
    # Vary prices around 60000
    base_price = 60000
    price_variation = (order_num % 100) - 50  # ±50
    price = base_price + price_variation
    
    return {
        "symbol": SYMBOL,
        "side": side,
        "order_type": "limit",
        "price": f"{price:.2f}",
        "quantity": "0.1"
    }


def submit_single_order(order_num, session=None):
    """Submit a single order and measure latency
    
    Args:
        order_num: Order number for generation
        session: requests.Session for connection reuse (performance optimization)
    """
    order = generate_random_order(order_num)
    
    # Use provided session or create new request
    http_client = session if session else requests
    
    start_time = time.time()
    try:
        response = http_client.post(
            ORDER_GATEWAY_URL,
            json=order,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        end_time = time.time()
        
        latency_ms = (end_time - start_time) * 1000
        
        if response.status_code == 201:
            return {
                "success": True,
                "latency_ms": latency_ms,
                "order_id": response.json().get("order_id")
            }
        else:
            return {
                "success": False,
                "latency_ms": latency_ms,
                "error": f"HTTP {response.status_code}"
            }
    except Exception as e:
        end_time = time.time()
        return {
            "success": False,
            "latency_ms": (end_time - start_time) * 1000,
            "error": str(e)
        }


def run_benchmark():
    """Run the performance benchmark"""
    print("=" * 70)
    print("PERFORMANCE BENCHMARK: Order Processing Throughput")
    print("=" * 70)
    print()
    print(f"Configuration:")
    print(f"  Target:           >1000 orders/sec")
    print(f"  Test Orders:      {NUM_ORDERS}")
    print(f"  Concurrent Threads: {NUM_THREADS}")
    print(f"  Endpoint:         {ORDER_GATEWAY_URL}")
    print()
    
    # Check if Order Gateway is running
    try:
        health_response = requests.get("http://localhost:8000/health", timeout=2)
        if health_response.status_code == 200:
            print("[OK] Order Gateway is running")
        else:
            print("[ERROR] Order Gateway health check failed")
            return
    except Exception as e:
        print(f"[ERROR] Cannot connect to Order Gateway: {e}")
        print("   Make sure it's running on port 8000")
        return
    
    print()
    print("Starting benchmark...")
    print("-" * 70)
    
    # Submit orders using thread pool with session reuse
    start_time = time.time()
    results = []
    
    # Create a session per thread for connection reuse
    def submit_batch(order_nums):
        """Submit a batch of orders using a single session"""
        session = requests.Session()
        batch_results = []
        for order_num in order_nums:
            result = submit_single_order(order_num, session)
            batch_results.append(result)
        session.close()
        return batch_results
    
    # Split orders into batches (one per thread)
    orders_per_thread = NUM_ORDERS // NUM_THREADS
    batches = [
        range(i * orders_per_thread, (i + 1) * orders_per_thread) 
        for i in range(NUM_THREADS)
    ]
    # Handle remainder
    remainder = NUM_ORDERS % NUM_THREADS
    if remainder:
        batches[-1] = range((NUM_THREADS - 1) * orders_per_thread, NUM_ORDERS)
    
    with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        # Submit batches
        futures = [executor.submit(submit_batch, batch) for batch in batches]
        
        # Collect results with progress indicator
        completed = 0
        for future in as_completed(futures):
            batch_results = future.result()
            results.extend(batch_results)
            completed += len(batch_results)
            
            if completed % 100 == 0 or completed == NUM_ORDERS:
                print(f"  Progress: {completed}/{NUM_ORDERS} orders submitted...")
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Calculate statistics
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    latencies = [r["latency_ms"] for r in successful]
    
    throughput = NUM_ORDERS / total_time
    
    # Print results
    print("-" * 70)
    print()
    print("=" * 70)
    print("BENCHMARK RESULTS")
    print("=" * 70)
    print()
    
    # Throughput Results
    print("THROUGHPUT:")
    print(f"   Total Orders:     {NUM_ORDERS}")
    print(f"   Total Time:       {total_time:.2f} seconds")
    print(f"   Throughput:       {throughput:.2f} orders/sec")
    print()
    
    if throughput >= 1000:
        print(f"   [PASS] {throughput:.2f} orders/sec > 1000 orders/sec")
    else:
        print(f"   [FAIL] {throughput:.2f} orders/sec < 1000 orders/sec")
    print()
    
    # Success Rate
    success_rate = (len(successful) / NUM_ORDERS) * 100
    print("SUCCESS RATE:")
    print(f"   Successful:       {len(successful)}/{NUM_ORDERS} ({success_rate:.1f}%)")
    print(f"   Failed:           {len(failed)}/{NUM_ORDERS}")
    print()
    
    # Latency Statistics
    if latencies:
        print("LATENCY STATISTICS:")
        print(f"   Mean:             {statistics.mean(latencies):.2f} ms")
        print(f"   Median:           {statistics.median(latencies):.2f} ms")
        print(f"   Min:              {min(latencies):.2f} ms")
        print(f"   Max:              {max(latencies):.2f} ms")
        print(f"   StdDev:           {statistics.stdev(latencies):.2f} ms")
        print()
        
        # Percentiles
        sorted_latencies = sorted(latencies)
        p50 = sorted_latencies[int(len(sorted_latencies) * 0.50)]
        p95 = sorted_latencies[int(len(sorted_latencies) * 0.95)]
        p99 = sorted_latencies[int(len(sorted_latencies) * 0.99)]
        
        print("   Percentiles:")
        print(f"     P50:            {p50:.2f} ms")
        print(f"     P95:            {p95:.2f} ms")
        print(f"     P99:            {p99:.2f} ms")
    
    print()
    print("=" * 70)
    print()
    
    # Errors (if any)
    if failed:
        print("[ERRORS]:")
        error_types = {}
        for r in failed:
            error = r.get("error", "Unknown")
            error_types[error] = error_types.get(error, 0) + 1
        
        for error, count in error_types.items():
            print(f"   {error}: {count} occurrences")
        print()
    
    # Final verdict
    print("=" * 70)
    print("FINAL VERDICT:")
    print("=" * 70)
    
    if throughput >= 1000 and success_rate >= 99:
        print("[BENCHMARK PASSED]")
        print(f"   System achieved {throughput:.0f} orders/sec with {success_rate:.1f}% success rate")
        print("   Assignment requirement (>1000 orders/sec) is MET")
    elif throughput >= 1000:
        print("[BENCHMARK PARTIAL PASS]")
        print(f"   Throughput requirement met ({throughput:.0f} orders/sec)")
        print(f"   But success rate is low ({success_rate:.1f}%)")
    else:
        print("[BENCHMARK FAILED]")
        print(f"   System only achieved {throughput:.0f} orders/sec")
        print("   Does not meet assignment requirement (>1000 orders/sec)")
    
    print("=" * 70)
    print()
    
    return {
        "throughput": throughput,
        "success_rate": success_rate,
        "passed": throughput >= 1000 and success_rate >= 99
    }


if __name__ == "__main__":
    try:
        result = run_benchmark()
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Benchmark interrupted by user")
    except Exception as e:
        print(f"\n\n[ERROR] Benchmark failed with error: {e}")
        import traceback
        traceback.print_exc()

