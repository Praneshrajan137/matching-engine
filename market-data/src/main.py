"""
Market Data Service - WebSocket Broadcast
Implements FR-3.2 and FR-3.3: Real-time market data and trade execution feeds
"""

import json
import logging
import asyncio
import os
from typing import Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
import redis


# Constants (centralized in order-gateway but duplicated here for independence)
TRADE_EVENTS_CHANNEL = "trade_events"
BBO_UPDATES_CHANNEL = "bbo_updates"
ORDER_BOOK_CHANNEL = "order_book_updates"


# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s market-data %(message)s",
)
logger = logging.getLogger("market-data")

# FastAPI application
app = FastAPI(
    title="GoQuant Market Data Service",
    description="Real-time WebSocket broadcast for trade executions and order book updates",
    version="1.0.0",
)


class ConnectionManager:
    """
    WebSocket connection manager
    Handles multiple client connections and broadcasting
    """

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections.add(websocket)
        print(f"Client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        self.active_connections.discard(websocket)
        print(f"Client disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """
        Broadcast message to all connected clients

        Removes disconnected clients automatically
        """
        disconnected = set()

        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except WebSocketDisconnect:
                disconnected.add(connection)
            except Exception as e:
                print(f"Error broadcasting to client: {e}")
                disconnected.add(connection)

        # Remove disconnected clients
        for conn in disconnected:
            self.disconnect(conn)


# Global connection manager
manager = ConnectionManager()


def get_redis_client():
    """Get Redis client for pub/sub"""
    host = os.getenv("REDIS_HOST", "localhost")
    port = int(os.getenv("REDIS_PORT", "6379"))
    db = int(os.getenv("REDIS_DB", "0"))

    return redis.Redis(host=host, port=port, db=db, decode_responses=True)


def blocking_redis_listener(redis_client, pubsub):
    """
    Blocking Redis listener (runs in thread pool)
    Returns messages from Redis pub/sub
    """
    for message in pubsub.listen():
        if message["type"] == "message":
            yield message["data"]


async def redis_subscriber():
    """
    Background task: Subscribe to Redis channels for market data
    Broadcasts messages to all WebSocket clients

    Implements:
    - FR-3.2: BBO and L2 order book updates
    - FR-3.3: Real-time trade execution broadcast
    """
    try:
        redis_client = get_redis_client()
        pubsub = redis_client.pubsub()

        # Subscribe to all market data channels
        pubsub.subscribe(TRADE_EVENTS_CHANNEL)
        pubsub.subscribe(BBO_UPDATES_CHANNEL)
        pubsub.subscribe(ORDER_BOOK_CHANNEL)

        logger.info(
            "subscribed_channels",
            extra={
                "channels": [
                    TRADE_EVENTS_CHANNEL,
                    BBO_UPDATES_CHANNEL,
                    ORDER_BOOK_CHANNEL,
                ]
            },
        )

        # Run blocking listener in thread pool to avoid blocking event loop
        loop = asyncio.get_event_loop()

        # Process messages asynchronously
        while True:
            try:
                # Get next message from Redis in thread pool
                message_data = await loop.run_in_executor(
                    None,  # Use default ThreadPoolExecutor
                    lambda: pubsub.get_message(timeout=1.0),
                )

                if message_data and message_data["type"] == "message":
                    try:
                        # Parse message data
                        data = json.loads(message_data["data"])

                        # Determine message type based on channel or data content
                        channel = message_data.get("channel", "")

                        # Broadcast to all WebSocket clients with appropriate type
                        if channel == TRADE_EVENTS_CHANNEL:
                            await manager.broadcast({"type": "trade", "data": data})
                            logger.info(
                                "broadcast_trade",
                                extra={
                                    "trade_id": data.get("trade_id"),
                                    "symbol": data.get("symbol"),
                                },
                            )

                        elif channel == BBO_UPDATES_CHANNEL:
                            await manager.broadcast({"type": "bbo", "data": data})
                            logger.debug(
                                "broadcast_bbo",
                                extra={"bid": data.get("bid"), "ask": data.get("ask")},
                            )

                        elif channel == ORDER_BOOK_CHANNEL:
                            await manager.broadcast({"type": "l2_update", "data": data})
                            bid_levels = len(data.get("bids", []))
                            ask_levels = len(data.get("asks", []))
                            logger.debug(
                                "broadcast_l2",
                                extra={
                                    "bid_levels": bid_levels,
                                    "ask_levels": ask_levels,
                                },
                            )

                    except json.JSONDecodeError as e:
                        print(f"Invalid JSON from Redis: {e}")
                    except Exception as e:
                        print(f"Error processing market data: {e}")

                # Small delay to prevent CPU spinning
                await asyncio.sleep(0.01)

            except Exception as e:
                logger.exception("message_loop_error")
                await asyncio.sleep(1)

    except redis.ConnectionError:
        logger.exception("redis_connection_error")
    except Exception:
        logger.exception("redis_subscriber_unexpected_error")


@app.on_event("startup")
async def startup_event():
    """Start Redis subscriber on application startup"""
    # Run Redis subscriber in background task
    asyncio.create_task(redis_subscriber())
    print("Market Data Service started")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        redis_client = get_redis_client()
        redis_client.ping()
        logger.info("health_check ok", extra={"redis": "connected"})
        return {
            "status": "healthy",
            "service": "market-data",
            "redis": "connected",
            "active_connections": len(manager.active_connections),
        }
    except redis.ConnectionError:
        logger.error("health_check failed: redis disconnected")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "market-data",
                "redis": "disconnected",
                "active_connections": len(manager.active_connections),
            },
        )


@app.websocket("/ws/market-data")
async def market_data_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for market data feed

    Implements FR-3.2: WebSocket market data API (BBO + L2 depth)
    Implements FR-3.3: Real-time trade execution feed

    Clients connect and receive three types of messages:

    1. Trade Execution Events:
    {
        "type": "trade",
        "data": {
            "trade_id": "T0001",
            "symbol": "BTC-USDT",
            "price": "60000.00",
            "quantity": "1.5",
            "aggressor_side": "buy",
            "maker_order_id": "uuid1",
            "taker_order_id": "uuid2",
            "timestamp": 1697380800
        }
    }

    2. BBO (Best Bid & Offer) Updates:
    {
        "type": "bbo",
        "data": {
            "type": "bbo",
            "symbol": "BTC-USDT",
            "bid": "60000.00",
            "ask": "60001.00",
            "timestamp": 1697380800
        }
    }

    3. L2 Order Book Depth (Top 10 Levels):
    {
        "type": "l2_update",
        "data": {
            "type": "l2_update",
            "timestamp": 1697380800,
            "symbol": "BTC-USDT",
            "bids": [["60000.00", "1.5"], ["59999.50", "2.0"]],
            "asks": [["60001.00", "0.8"], ["60002.00", "1.2"]]
        }
    }
    """
    await manager.connect(websocket)

    try:
        # Send welcome message
        await websocket.send_json(
            {
                "type": "connected",
                "message": "Connected to GoQuant Market Data Feed",
                "subscriptions": ["trades", "bbo", "l2_updates"],
            }
        )

        # Keep connection alive and handle client messages
        while True:
            # Wait for client messages (e.g., subscription changes)
            data = await websocket.receive_text()

            # For now, just acknowledge (future: handle subscribe/unsubscribe)
            try:
                client_msg = json.loads(data)
                await websocket.send_json(
                    {"type": "ack", "message": f"Received: {client_msg}"}
                )
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@app.get("/stats")
async def get_stats():
    """Get service statistics"""
    return {
        "active_websocket_connections": len(manager.active_connections),
        "service": "market-data",
        "version": "1.0.0",
    }
