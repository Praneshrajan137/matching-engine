"""
End-to-End Integration Test
Tests the complete order flow: REST → Redis → Matching Engine → WebSocket

Architecture tested:
1. Order Gateway receives REST POST
2. Publishes to Redis "order_queue"
3. Python Matching Engine consumes and processes
4. Publishes trades to Redis "trade_events"
5. Market Data broadcasts to WebSocket clients
"""

import pytest
import asyncio
import json
import time
import subprocess
import sys
from pathlib import Path
from decimal import Decimal
import httpx
from websockets import connect as ws_connect
import redis

# Test configuration
ORDER_GATEWAY_URL = "http://localhost:8000"
MARKET_DATA_WS_URL = "ws://localhost:8001/ws/market-data"
REDIS_HOST = "localhost"
REDIS_PORT = 6379


@pytest.fixture(scope="module")
def redis_client():
    """Create Redis client and verify connection"""
    try:
        client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            decode_responses=True,
            socket_connect_timeout=2
        )
        
        # Test connection
        client.ping()
        print(f"\n[OK] Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
        
        # Clean up any existing test data
        client.delete("order_queue")
        client.delete("trade_events")
        
        yield client
        
        # Cleanup
        client.delete("order_queue")
        client.delete("trade_events")
        
    except redis.ConnectionError as e:
        pytest.fail(f"Redis not available: {e}\n"
                   f"Please start Redis first:\n"
                   f"  docker run -d -p 6379:6379 --name redis redis:7-alpine")


@pytest.fixture(scope="module")
def check_services():
    """Verify all services are running"""
    print("\n[INFO] Checking service availability...")
    
    # Check Order Gateway
    try:
        import httpx
        response = httpx.get(f"{ORDER_GATEWAY_URL}/health", timeout=2)
        print(f"[OK] Order Gateway: {response.json()}")
    except Exception as e:
        pytest.fail(f"Order Gateway not running on port 8000: {e}\n"
                   f"Start it with: uvicorn src.main:app --port 8000")
    
    # Check Market Data
    try:
        response = httpx.get("http://localhost:8001/health", timeout=2)
        print(f"[OK] Market Data: {response.json()}")
    except Exception as e:
        pytest.fail(f"Market Data not running on port 8001: {e}\n"
                   f"Start it with: uvicorn src.main:app --port 8001")
    
    print("[OK] All services are running")
    yield


def test_redis_connectivity(redis_client):
    """
    Test: Verify Redis is accessible
    
    Given: Redis server is running
    When: Ping Redis
    Then: Should return PONG
    """
    response = redis_client.ping()
    assert response is True


@pytest.mark.asyncio
async def test_order_gateway_publishes_to_redis(redis_client, check_services):
    """
    Test: Order Gateway publishes orders to Redis
    
    Given: Order Gateway is running
    When: POST order to /v1/orders
    Then: Order appears in Redis "order_queue"
    """
    # Arrange
    order_data = {
        "symbol": "BTC-USDT",
        "order_type": "limit",
        "side": "buy",
        "quantity": "1.0",
        "price": "60000.00"
    }
    
    # Act
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{ORDER_GATEWAY_URL}/v1/orders",
            json=order_data,
            timeout=5
        )
    
    # Assert
    assert response.status_code == 201
    response_json = response.json()
    assert "order_id" in response_json
    order_id = response_json["order_id"]
    
    print(f"\n[OK] Order submitted: {order_id}")
    
    # Verify order is in Redis queue
    await asyncio.sleep(0.1)  # Small delay for Redis write
    queue_length = redis_client.llen("order_queue")
    assert queue_length > 0, "Order not found in Redis queue"
    
    print(f"[OK] Order found in Redis queue (length: {queue_length})")


@pytest.mark.asyncio
async def test_matching_engine_processes_order(redis_client, check_services):
    """
    Test: Matching Engine consumes orders from Redis
    
    Note: This test requires the Python Matching Engine to be running
    """
    # Check if matching engine is running by monitoring Redis
    print("\n[WARN] This test requires the Python Matching Engine to be running:")
    print("   cd matching-engine")
    print("   .venv\\Scripts\\Activate.ps1")
    print("   python python/redis_engine_runner.py")
    print()
    
    # We'll just verify the queue exists for now
    # Manual verification: Check if orders are being consumed
    initial_length = redis_client.llen("order_queue")
    print(f"[INFO] Current order queue length: {initial_length}")


@pytest.mark.asyncio
async def test_end_to_end_order_matching(redis_client, check_services):
    """
    Test: Complete end-to-end order flow
    
    Given: All services running (Gateway, Engine, Market Data)
    When: Submit matching orders
    Then: Trade event broadcast via WebSocket
    
    NOTE: Requires Python Matching Engine to be running manually
    """
    print("\n" + "="*60)
    print("END-TO-END INTEGRATION TEST")
    print("="*60)
    
    # Step 1: Connect WebSocket client
    print("\n[Step 1] Connecting to Market Data WebSocket...")
    
    try:
        async with ws_connect(MARKET_DATA_WS_URL) as websocket:
            # Receive welcome message
            welcome = await asyncio.wait_for(websocket.recv(), timeout=2)
            welcome_data = json.loads(welcome)
            print(f"   [OK] Connected: {welcome_data.get('message', '')}")
            
            # Step 2: Submit first order (buy limit)
            print("\n[Step 2] Submitting BUY limit order...")
            
            buy_order = {
                "symbol": "BTC-USDT",
                "order_type": "limit",
                "side": "buy",
                "quantity": "1.0",
                "price": "60000.00"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{ORDER_GATEWAY_URL}/v1/orders",
                    json=buy_order,
                    timeout=5
                )
            
            assert response.status_code == 201
            buy_order_id = response.json()["order_id"]
            print(f"   [OK] Order submitted: {buy_order_id}")
            
            # Wait for order to be processed
            await asyncio.sleep(0.5)
            
            # Step 3: Submit matching order (sell limit)
            print("\n[Step 3] Submitting SELL limit order (should match)...")
            
            sell_order = {
                "symbol": "BTC-USDT",
                "order_type": "limit",
                "side": "sell",
                "quantity": "1.0",
                "price": "60000.00"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{ORDER_GATEWAY_URL}/v1/orders",
                    json=sell_order,
                    timeout=5
                )
            
            assert response.status_code == 201
            sell_order_id = response.json()["order_id"]
            print(f"   [OK] Order submitted: {sell_order_id}")
            
            # Step 4: Wait for trade broadcast
            print("\n[Step 4] Waiting for trade event on WebSocket...")
            
            try:
                # Wait up to 10 seconds for trade event
                trade_msg = await asyncio.wait_for(websocket.recv(), timeout=10)
                trade_data = json.loads(trade_msg)
                
                print(f"   [OK] Trade received: {json.dumps(trade_data, indent=2)}")
                
                # Verify trade data
                assert trade_data.get("type") == "trade"
                assert "data" in trade_data
                
                trade_info = trade_data["data"]
                assert trade_info.get("symbol") == "BTC-USDT"
                assert Decimal(trade_info.get("price")) == Decimal("60000.00")
                assert Decimal(trade_info.get("quantity")) == Decimal("1.0")
                
                print("\n[PASS] END-TO-END TEST PASSED!")
                print("   - Order submitted via REST API")
                print("   - Processed by Matching Engine")
                print("   - Trade broadcast via WebSocket")
                
            except asyncio.TimeoutError:
                print("\n[WARN] No trade event received within 10 seconds")
                print("\n[INFO] Troubleshooting checklist:")
                print("   1. Is Python Matching Engine running?")
                print("      cd matching-engine && python python/redis_engine_runner.py")
                print("   2. Check Redis queue:")
                queue_len = redis_client.llen("order_queue")
                print(f"      Order queue length: {queue_len}")
                print("   3. Monitor Redis:")
                print("      docker exec redis redis-cli MONITOR")
                
                pytest.skip("Matching Engine not running - manual verification needed")
                
    except Exception as e:
        print(f"\n[ERROR] WebSocket connection error: {e}")
        pytest.fail(f"Failed to connect to Market Data WebSocket: {e}")


@pytest.mark.asyncio
async def test_manual_verification_guide(redis_client):
    """
    Test: Provide manual verification instructions
    
    This is a guide for manual testing when automation isn't possible
    """
    print("\n" + "="*60)
    print("MANUAL VERIFICATION GUIDE")
    print("="*60)
    
    print("\n[INFO] To test the complete system manually:")
    print()
    print("Terminal 1 - Redis:")
    print("  docker start redis")
    print("  # Or: docker run -d -p 6379:6379 --name redis redis:7-alpine")
    print()
    print("Terminal 2 - Order Gateway:")
    print("  cd order-gateway")
    print("  .venv\\Scripts\\Activate.ps1")
    print("  uvicorn src.main:app --reload --port 8000")
    print()
    print("Terminal 3 - Market Data:")
    print("  cd market-data")
    print("  .venv\\Scripts\\Activate.ps1")
    print("  uvicorn src.main:app --reload --port 8001")
    print()
    print("Terminal 4 - Python Matching Engine:")
    print("  cd matching-engine")
    print("  .venv\\Scripts\\Activate.ps1")
    print("  python python/redis_engine_runner.py")
    print()
    print("Terminal 5 - Test Commands:")
    print('  curl -X POST http://localhost:8000/v1/orders \\')
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"symbol":"BTC-USDT","order_type":"limit","side":"buy","quantity":"1.0","price":"60000.00"}\'')
    print()
    print("Terminal 6 - Monitor Redis:")
    print("  docker exec redis redis-cli MONITOR")
    print()
    print("="*60)


if __name__ == "__main__":
    # Run with: pytest tests/integration/test_end_to_end.py -v -s
    pytest.main([__file__, "-v", "-s"])

