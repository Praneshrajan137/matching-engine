"""
Order Gateway FastAPI Application
Implements FR-3.1: REST API for order submission
"""

import json
import logging
import uuid
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
import redis

try:
    from .models import OrderRequest, OrderResponse, ErrorResponse
    from .redis_client import get_redis_client, RedisConnectionError
    from .constants import ORDER_QUEUE, API_VERSION
except ImportError:
    # For direct execution and testing
    from models import OrderRequest, OrderResponse, ErrorResponse
    from redis_client import get_redis_client, RedisConnectionError
    from constants import ORDER_QUEUE, API_VERSION


# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s order-gateway %(message)s",
)
logger = logging.getLogger("order-gateway")

# FastAPI application
app = FastAPI(
    title="GoQuant Order Gateway",
    description="High-performance order submission gateway for cryptocurrency matching engine",
    version="1.0.0",
    docs_url=f"/{API_VERSION}/docs",
)


@app.get("/health")
async def health_check():
    """
    Health check endpoint

    Returns:
        dict: Service health status
    """
    try:
        redis_client = get_redis_client()
        redis_client.ping()
        logger.info(
            "health_check ok", extra={"service": "order-gateway", "redis": "connected"}
        )
        return {"status": "healthy", "service": "order-gateway", "redis": "connected"}
    except RedisConnectionError:
        logger.error("health_check failed: redis disconnected")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "service": "order-gateway",
                "redis": "disconnected",
            },
        )


@app.post(
    f"/{API_VERSION}/orders",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        422: {"model": ErrorResponse, "description": "Validation Error"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
async def submit_order(order: OrderRequest) -> OrderResponse:
    """
    Submit order to matching engine

    Implements FR-3.1: Order submission endpoint

    Process:
    1. Validate request (automatic via Pydantic)
    2. Generate unique order ID
    3. Serialize to JSON
    4. Push to Redis queue (LPUSH for FIFO processing)
    5. Return confirmation

    Time complexity: O(1) for Redis LPUSH

    Args:
        order: Validated order request

    Returns:
        OrderResponse: Order confirmation with ID and timestamp

    Raises:
        HTTPException 500: If Redis connection fails
    """
    try:
        # Generate unique order ID
        order_id = str(uuid.uuid4())

        # Prepare order payload for matching engine
        order_payload = {
            "id": order_id,
            "symbol": order.symbol,
            "order_type": order.order_type.value,
            "side": order.side.value,
            "quantity": str(order.quantity),  # Serialize Decimal as string
            "price": str(order.price) if order.price else None,
            "timestamp": int(uuid.uuid1().time),  # Microsecond timestamp
        }

        # Serialize to JSON
        order_json = json.dumps(order_payload)

        # Push to Redis queue (RPUSH for FIFO: producer pushes right, consumer pops left)
        redis_client = get_redis_client()
        redis_client.rpush(ORDER_QUEUE, order_json)
        # Audit log for order submission
        logger.info(
            "order_submitted",
            extra={
                "order_id": order_id,
                "symbol": order.symbol,
                "side": order.side.value,
                "type": order.order_type.value,
                "quantity": str(order.quantity),
                "price": str(order.price) if order.price else None,
            },
        )

        # Return confirmation
        return OrderResponse(order_id=order_id)

    except RedisConnectionError as e:
        # Redis connection failure - return 500
        logger.exception("redis_connection_error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Service temporarily unavailable",
        )
    except Exception as e:
        # Unexpected error - log and return generic 500
        logger.exception("internal_server_error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize Redis connection on startup"""
    try:
        redis_client = get_redis_client()
        print(
            f"Connected to Redis at {redis_client.connection_pool.connection_kwargs['host']}"
        )
    except RedisConnectionError as e:
        print(f"Warning: Could not connect to Redis: {e}")
        print("API will return 500 errors until Redis is available")
