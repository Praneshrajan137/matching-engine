"""
Order Gateway API Tests
Implements TDD RED phase for FR-3.1 (POST /v1/orders)

Test Strategy:
- Use FastAPI TestClient for HTTP testing
- Mock Redis to avoid external dependencies
- Follow AAA pattern: Arrange, Act, Assert
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from decimal import Decimal

# Import after sys.path modification if needed
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Change working directory to src for imports to work
import os
os.chdir(Path(__file__).parent.parent / "src")

from main import app
from redis_client import RedisConnectionError


# Test client fixture
@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


# Mock Redis fixture
@pytest.fixture
def mock_redis():
    """Mock Redis client to avoid external dependencies"""
    with patch('main.get_redis_client') as mock:
        redis_mock = Mock()
        redis_mock.rpush = Mock(return_value=1)  # RPUSH returns queue length (FIFO ordering)
        redis_mock.ping = Mock(return_value=True)
        mock.return_value = redis_mock
        yield redis_mock


# Test 1: Valid market order submission
def test_submit_valid_market_order(client, mock_redis):
    """
    Test Case 1: Submit valid market order
    
    Given: Valid market order request (no price)
    When: POST /v1/orders
    Then: Return 201 Created with order_id
    """
    # Arrange
    order_data = {
        "symbol": "BTC-USDT",
        "order_type": "market",
        "side": "buy",
        "quantity": "1.5"
    }
    
    # Act
    response = client.post("/v1/orders", json=order_data)
    
    # Assert
    assert response.status_code == 201
    response_json = response.json()
    assert "order_id" in response_json
    assert response_json["status"] == "accepted"
    assert "timestamp" in response_json
    
    # Verify Redis was called (RPUSH for FIFO ordering)
    mock_redis.rpush.assert_called_once()
    call_args = mock_redis.rpush.call_args
    assert call_args[0][0] == "order_queue"  # Queue name
    
    # Verify order payload structure
    order_payload = json.loads(call_args[0][1])
    assert order_payload["symbol"] == "BTC-USDT"
    assert order_payload["order_type"] == "market"
    assert order_payload["side"] == "buy"
    assert order_payload["quantity"] == "1.5"
    assert order_payload["price"] is None


# Test 2: Valid limit order submission
def test_submit_valid_limit_order(client, mock_redis):
    """
    Test Case 2: Submit valid limit order
    
    Given: Valid limit order request (with price)
    When: POST /v1/orders
    Then: Return 201 Created
    """
    # Arrange
    order_data = {
        "symbol": "BTC-USDT",
        "order_type": "limit",
        "side": "sell",
        "quantity": "2.0",
        "price": "60000.00"
    }
    
    # Act
    response = client.post("/v1/orders", json=order_data)
    
    # Assert
    assert response.status_code == 201
    response_json = response.json()
    assert "order_id" in response_json
    
    # Verify order payload
    call_args = mock_redis.rpush.call_args
    order_payload = json.loads(call_args[0][1])
    assert order_payload["price"] == "60000.00"  # Price included for limit


# Test 3: Limit order missing price should fail validation
def test_submit_limit_order_missing_price(client, mock_redis):
    """
    Test Case 3: Limit order without price
    
    Given: Limit order request WITHOUT price
    When: POST /v1/orders
    Then: Return 422 Unprocessable Entity
    """
    # Arrange
    order_data = {
        "symbol": "BTC-USDT",
        "order_type": "limit",
        "side": "buy",
        "quantity": "1.0"
        # Missing price field
    }
    
    # Act
    response = client.post("/v1/orders", json=order_data)
    
    # Assert
    assert response.status_code == 422
    response_json = response.json()
    assert "detail" in response_json
    
    # Verify Redis was NOT called (validation failed before processing)
    mock_redis.rpush.assert_not_called()


# Test 4: Market order with price should fail validation
def test_submit_market_order_with_price(client, mock_redis):
    """
    Test Case 4: Market order with price (invalid)
    
    Given: Market order request WITH price
    When: POST /v1/orders
    Then: Return 422 Unprocessable Entity
    """
    # Arrange
    order_data = {
        "symbol": "BTC-USDT",
        "order_type": "market",
        "side": "buy",
        "quantity": "1.0",
        "price": "60000.00"  # Invalid for market order
    }
    
    # Act
    response = client.post("/v1/orders", json=order_data)
    
    # Assert
    assert response.status_code == 422
    response_json = response.json()
    assert "detail" in response_json
    # Verify error message mentions price issue
    error_detail = str(response_json["detail"])
    assert "price" in error_detail.lower() or "market" in error_detail.lower()
    
    # Verify Redis was NOT called
    mock_redis.rpush.assert_not_called()


# Test 5: Invalid quantity should fail validation
def test_submit_order_invalid_quantity(client, mock_redis):
    """
    Test Case 5: Order with invalid quantity
    
    Given: Order with quantity <= 0
    When: POST /v1/orders
    Then: Return 422 Unprocessable Entity
    """
    # Arrange
    test_cases = [
        {"quantity": "0"},      # Zero
        {"quantity": "-1.5"},   # Negative
    ]
    
    for test_data in test_cases:
        order_data = {
            "symbol": "BTC-USDT",
            "order_type": "market",
            "side": "buy",
            **test_data
        }
        
        # Act
        response = client.post("/v1/orders", json=order_data)
        
        # Assert
        assert response.status_code == 422, f"Failed for quantity: {test_data['quantity']}"
        
    # Verify Redis was never called
    mock_redis.rpush.assert_not_called()


# Test 6: Invalid side should fail validation
def test_submit_order_invalid_side(client, mock_redis):
    """
    Test Case 6: Order with invalid side
    
    Given: Order with side not 'buy' or 'sell'
    When: POST /v1/orders
    Then: Return 422 Unprocessable Entity
    """
    # Arrange
    order_data = {
        "symbol": "BTC-USDT",
        "order_type": "market",
        "side": "invalid_side",  # Invalid
        "quantity": "1.0"
    }
    
    # Act
    response = client.post("/v1/orders", json=order_data)
    
    # Assert
    assert response.status_code == 422
    
    # Verify Redis was NOT called
    mock_redis.rpush.assert_not_called()


# Test 7: Redis connection failure should return 500
def test_redis_connection_failure(client):
    """
    Test Case 7: Redis connection failure
    
    Given: Redis is unavailable
    When: POST /v1/orders
    Then: Return 500 Internal Server Error
    """
    # Arrange
    order_data = {
        "symbol": "BTC-USDT",
        "order_type": "market",
        "side": "buy",
        "quantity": "1.0"
    }
    
    # Mock Redis to raise connection error
    with patch('main.get_redis_client') as mock_get_redis:
        mock_get_redis.side_effect = RedisConnectionError("Connection refused")
        
        # Act
        response = client.post("/v1/orders", json=order_data)
        
        # Assert
        assert response.status_code == 500
        response_json = response.json()
        assert "detail" in response_json
        # Should NOT expose internal error details to client
        assert "refused" not in response_json["detail"].lower()


# Test 8: Health check endpoint
def test_health_check_redis_connected(client, mock_redis):
    """
    Test: Health check when Redis is connected
    
    Given: Redis is available
    When: GET /health
    Then: Return 200 with status healthy
    """
    # Act
    response = client.get("/health")
    
    # Assert
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["status"] == "healthy"
    assert response_json["redis"] == "connected"


def test_health_check_redis_disconnected(client):
    """
    Test: Health check when Redis is disconnected
    
    Given: Redis is unavailable
    When: GET /health
    Then: Return 503 Service Unavailable
    """
    # Arrange - Mock Redis connection failure
    with patch('main.get_redis_client') as mock_get_redis:
        mock_get_redis.side_effect = RedisConnectionError("Connection failed")
        
        # Act
        response = client.get("/health")
        
        # Assert
        assert response.status_code == 503
        response_json = response.json()
        assert response_json["status"] == "unhealthy"
        assert response_json["redis"] == "disconnected"

