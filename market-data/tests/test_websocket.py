"""
Market Data WebSocket Tests
Tests for FR-3.2 and FR-3.3: Real-time market data and trade execution feeds

Test Strategy:
- Use FastAPI TestClient for WebSocket testing
- Mock Redis pub/sub to avoid external dependencies
- Follow AAA pattern: Arrange, Act, Assert
"""

import pytest
import json
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient

# Import after sys.path modification if needed
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Change working directory to src for imports to work
import os
os.chdir(Path(__file__).parent.parent / "src")

from main import app, manager


# Test client fixture
@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


# Test 1: WebSocket connection and disconnect lifecycle
def test_websocket_connect_disconnect(client):
    """
    Test Case 1: Basic WebSocket connection lifecycle
    
    Given: Market Data service is running
    When: Client connects and disconnects
    Then: Connection is accepted and cleanup happens
    """
    # Arrange & Act
    with client.websocket_connect("/ws/market-data") as websocket:
        # Assert - connection established
        assert websocket is not None
        
        # Verify we can receive the welcome message
        data = websocket.receive_json()
        assert data["type"] == "connected"
        assert "message" in data
        
    # After context exit, connection is closed
    # Verify cleanup (connection manager should have 0 active connections)
    assert len(manager.active_connections) == 0


# Test 2: WebSocket receives welcome message on connection
def test_websocket_receives_welcome_message(client):
    """
    Test Case 2: Initial welcome message
    
    Given: Market Data service is running
    When: Client connects
    Then: Receives welcome message with subscription info
    """
    # Arrange & Act
    with client.websocket_connect("/ws/market-data") as websocket:
        # Act - receive first message
        welcome_msg = websocket.receive_json()
        
        # Assert
        assert welcome_msg["type"] == "connected"
        assert "Connected to GoQuant Market Data Feed" in welcome_msg["message"]
        assert "subscriptions" in welcome_msg
        assert "trades" in welcome_msg["subscriptions"]


# Test 3: Multiple clients all receive broadcast
def test_multiple_clients_all_receive_broadcast(client):
    """
    Test Case 3: Fan-out broadcasting to multiple clients
    
    Given: Two WebSocket clients connected
    When: Trade event is broadcast
    Then: Both clients receive the same message
    """
    # Arrange - connect two clients
    with client.websocket_connect("/ws/market-data") as ws1:
        with client.websocket_connect("/ws/market-data") as ws2:
            # Clear welcome messages
            ws1.receive_json()
            ws2.receive_json()
            
            # Verify both clients are connected
            assert len(manager.active_connections) == 2
            
            # Act - manually broadcast a test message
            test_trade = {
                "type": "trade",
                "data": {
                    "trade_id": "T0001",
                    "symbol": "BTC-USDT",
                    "price": "60000.00",
                    "quantity": "1.5"
                }
            }
            
            # Use asyncio to run the async broadcast
            import asyncio
            asyncio.run(manager.broadcast(test_trade))
            
            # Assert - both clients received the message
            msg1 = ws1.receive_json()
            msg2 = ws2.receive_json()
            
            assert msg1 == test_trade
            assert msg2 == test_trade
            assert msg1["data"]["trade_id"] == "T0001"


# Test 4: Disconnected client removed from active connections
def test_disconnected_client_not_in_active_connections(client):
    """
    Test Case 4: Cleanup verification
    
    Given: Client is connected
    When: Client disconnects
    Then: Connection manager removes it from active connections
    """
    # Arrange
    initial_count = len(manager.active_connections)
    
    # Act - connect and then disconnect
    with client.websocket_connect("/ws/market-data") as websocket:
        # Clear welcome message
        websocket.receive_json()
        
        # Verify connection added
        assert len(manager.active_connections) == initial_count + 1
    
    # Assert - after context exit, connection is removed
    assert len(manager.active_connections) == initial_count


# Test 5: Client can send messages and receive acknowledgment
def test_websocket_client_message_acknowledged(client):
    """
    Test Case 5: Client-to-server message handling
    
    Given: Client is connected
    When: Client sends a message
    Then: Server acknowledges the message
    """
    # Arrange
    with client.websocket_connect("/ws/market-data") as websocket:
        # Clear welcome message
        websocket.receive_json()
        
        # Act - send a test message
        test_msg = {"action": "subscribe", "channel": "trades"}
        websocket.send_json(test_msg)
        
        # Assert - receive acknowledgment
        response = websocket.receive_json()
        assert response["type"] == "ack"
        assert "Received" in response["message"]


# Test 6: Health check endpoint
def test_health_check_endpoint(client):
    """
    Test: Health check returns service status
    
    Given: Market Data service is running
    When: GET /health
    Then: Returns status (may be 503 if Redis not connected)
    """
    # Act
    response = client.get("/health")
    
    # Assert - accept both 200 (healthy) and 503 (unhealthy due to Redis)
    assert response.status_code in [200, 503]
    data = response.json()
    assert data["service"] == "market-data"
    assert "active_connections" in data
    
    # If Redis is connected, should be healthy
    if response.status_code == 200:
        assert data["status"] == "healthy"
        assert data["redis"] == "connected"
    else:
        # Redis disconnected in test environment is acceptable
        assert data["status"] == "unhealthy"
        assert data["redis"] == "disconnected"


# Test 7: Stats endpoint
def test_stats_endpoint(client):
    """
    Test: Stats endpoint returns service metrics
    
    Given: Market Data service is running
    When: GET /stats
    Then: Returns connection count and service info
    """
    # Act
    response = client.get("/stats")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "active_websocket_connections" in data
    assert data["service"] == "market-data"
    assert data["version"] == "1.0.0"

