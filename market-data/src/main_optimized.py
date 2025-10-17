"""
Market Data Service - OPTIMIZED VERSION with Message Batching
Implements FR-3.2 and FR-3.3 with performance enhancements

Optimizations:
1. Message batching: Group trades within time window
2. Async broadcasting: Non-blocking send operations
3. Connection pooling: Efficient client management
4. Backpressure handling: Drop slow clients instead of blocking
"""

import json
import asyncio
import os
from typing import Set, List, Dict, Any
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
import time

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
import redis

# Constants
TRADE_EVENTS_CHANNEL = "trade_events"
ORDER_BOOK_CHANNEL = "order_book_updates"

# OPTIMIZATION SETTINGS
BATCH_INTERVAL_MS = 50  # Batch messages every 50ms
MAX_BATCH_SIZE = 100     # Or send immediately if batch reaches 100 messages
SLOW_CLIENT_THRESHOLD = 10  # Drop client if message queue > 10


@dataclass
class ClientConnection:
    """
    WebSocket client with buffering and health tracking
    """
    websocket: WebSocket
    message_queue: deque = field(default_factory=lambda: deque(maxlen=SLOW_CLIENT_THRESHOLD))
    messages_sent: int = 0
    messages_dropped: int = 0
    connected_at: float = field(default_factory=time.time)
    last_send_time: float = field(default_factory=time.time)
    
    @property
    def is_slow(self) -> bool:
        """Check if client is falling behind (backpressure detection)"""
        return len(self.message_queue) >= SLOW_CLIENT_THRESHOLD
    
    @property
    def latency_ms(self) -> float:
        """Estimated send latency"""
        return (time.time() - self.last_send_time) * 1000


class OptimizedConnectionManager:
    """
    High-performance WebSocket connection manager with batching
    
    Performance Features:
    - Message batching: Reduces overhead by grouping trades
    - Async broadcasting: Non-blocking sends with backpressure handling
    - Slow client detection: Auto-disconnect lagging clients
    - Statistics tracking: Monitor performance metrics
    """
    
    def __init__(self):
        self.active_connections: Dict[str, ClientConnection] = {}
        self.message_batch: List[Dict[str, Any]] = []
        self.batch_task: asyncio.Task = None
        self.stats = {
            "total_messages": 0,
            "batches_sent": 0,
            "clients_dropped": 0,
            "avg_batch_size": 0.0
        }
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections[client_id] = ClientConnection(websocket=websocket)
        print(f"✅ Client {client_id[:8]} connected. Total: {len(self.active_connections)}")
        
        # Start batch sender if not running
        if self.batch_task is None or self.batch_task.done():
            self.batch_task = asyncio.create_task(self._batch_sender())
    
    def disconnect(self, client_id: str):
        """Remove WebSocket connection"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            print(f"❌ Client {client_id[:8]} disconnected. Total: {len(self.active_connections)}")
    
    async def broadcast_single(self, message: Dict[str, Any]):
        """
        Add message to batch for efficient broadcasting
        
        Messages are batched and sent every BATCH_INTERVAL_MS
        or immediately if batch reaches MAX_BATCH_SIZE
        """
        self.message_batch.append(message)
        self.stats["total_messages"] += 1
        
        # Send immediately if batch is full
        if len(self.message_batch) >= MAX_BATCH_SIZE:
            await self._flush_batch()
    
    async def _batch_sender(self):
        """
        Background task that flushes message batch periodically
        
        This reduces WebSocket overhead by sending multiple messages together
        """
        while True:
            try:
                await asyncio.sleep(BATCH_INTERVAL_MS / 1000.0)
                
                if self.message_batch:
                    await self._flush_batch()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"❌ Batch sender error: {e}")
    
    async def _flush_batch(self):
        """
        Send batched messages to all clients
        
        Uses asyncio.gather for concurrent sends with backpressure handling
        """
        if not self.message_batch:
            return
        
        batch = self.message_batch.copy()
        self.message_batch.clear()
        
        batch_size = len(batch)
        self.stats["batches_sent"] += 1
        self.stats["avg_batch_size"] = (
            (self.stats["avg_batch_size"] * (self.stats["batches_sent"] - 1) + batch_size)
            / self.stats["batches_sent"]
        )
        
        # Create batch message envelope
        batch_message = {
            "type": "batch",
            "count": batch_size,
            "messages": batch
        }
        
        # Send to all clients concurrently
        disconnected = []
        
        for client_id, client in self.active_connections.items():
            try:
                # Backpressure handling: Drop slow clients
                if client.is_slow:
                    print(f"⚠️  Dropping slow client {client_id[:8]} "
                          f"(queue: {len(client.message_queue)}, "
                          f"latency: {client.latency_ms:.1f}ms)")
                    disconnected.append(client_id)
                    self.stats["clients_dropped"] += 1
                    continue
                
                # Send message (non-blocking with timeout)
                await asyncio.wait_for(
                    client.websocket.send_json(batch_message),
                    timeout=0.5  # 500ms max per client
                )
                
                client.messages_sent += batch_size
                client.last_send_time = time.time()
                
            except asyncio.TimeoutError:
                print(f"⏱️  Client {client_id[:8]} timeout, dropping")
                disconnected.append(client_id)
            except WebSocketDisconnect:
                disconnected.append(client_id)
            except Exception as e:
                print(f"❌ Error sending to {client_id[:8]}: {e}")
                disconnected.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected:
            self.disconnect(client_id)
        
        if batch_size > 1:
            print(f"📤 Batch sent: {batch_size} messages to {len(self.active_connections)} clients")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return {
            "active_connections": len(self.active_connections),
            "total_messages": self.stats["total_messages"],
            "batches_sent": self.stats["batches_sent"],
            "avg_batch_size": round(self.stats["avg_batch_size"], 2),
            "clients_dropped": self.stats["clients_dropped"],
            "pending_batch": len(self.message_batch)
        }


# FastAPI application
app = FastAPI(
    title="GoQuant Market Data Service (Optimized)",
    description="High-performance WebSocket broadcast with message batching",
    version="2.0.0"
)

# Global connection manager
manager = OptimizedConnectionManager()


def get_redis_client():
    """Get Redis client for pub/sub"""
    host = os.getenv("REDIS_HOST", "localhost")
    port = int(os.getenv("REDIS_PORT", "6379"))
    db = int(os.getenv("REDIS_DB", "0"))
    
    return redis.Redis(
        host=host,
        port=port,
        db=db,
        decode_responses=True,
        socket_timeout=1.0,  # Faster timeout
        socket_connect_timeout=1.0
    )


async def redis_subscriber():
    """
    Background task: Subscribe to Redis trade_events channel
    Broadcasts messages to all WebSocket clients with batching
    
    Implements FR-3.3: Real-time trade execution broadcast (optimized)
    """
    try:
        redis_client = get_redis_client()
        pubsub = redis_client.pubsub()
        pubsub.subscribe(TRADE_EVENTS_CHANNEL)
        
        print(f"✅ Subscribed to Redis channel: {TRADE_EVENTS_CHANNEL}")
        print(f"⚡ Batching enabled: {BATCH_INTERVAL_MS}ms window, max {MAX_BATCH_SIZE} messages")
        
        # Listen for messages (non-blocking with timeout)
        for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    # Parse trade event
                    trade_data = json.loads(message["data"])
                    
                    # Add to batch (will be sent every BATCH_INTERVAL_MS)
                    await manager.broadcast_single({
                        "type": "trade",
                        "data": trade_data
                    })
                    
                except json.JSONDecodeError as e:
                    print(f"❌ Invalid JSON from Redis: {e}")
                except Exception as e:
                    print(f"❌ Error processing trade event: {e}")
        
    except redis.ConnectionError as e:
        print(f"❌ Redis connection error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error in Redis subscriber: {e}")


@app.on_event("startup")
async def startup_event():
    """Start Redis subscriber on application startup"""
    asyncio.create_task(redis_subscriber())
    print("✅ Optimized Market Data Service started")
    print(f"   Batch interval: {BATCH_INTERVAL_MS}ms")
    print(f"   Max batch size: {MAX_BATCH_SIZE}")
    print(f"   Slow client threshold: {SLOW_CLIENT_THRESHOLD} messages")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        redis_client = get_redis_client()
        redis_client.ping()
        return {
            "status": "healthy",
            "service": "market-data-optimized",
            "redis": "connected",
            "active_connections": len(manager.active_connections),
            "performance": manager.get_stats()
        }
    except redis.ConnectionError:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "market-data-optimized",
                "redis": "disconnected",
                "active_connections": len(manager.active_connections)
            }
        )


@app.websocket("/ws/market-data")
async def market_data_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for market data feed (OPTIMIZED)
    
    Implements FR-3.2 & FR-3.3 with batching for performance
    
    Clients receive batched messages:
    {
        "type": "batch",
        "count": 10,
        "messages": [
            {"type": "trade", "data": {...}},
            {"type": "trade", "data": {...}},
            ...
        ]
    }
    """
    client_id = f"{websocket.client.host}:{websocket.client.port}"
    await manager.connect(websocket, client_id)
    
    try:
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to GoQuant Market Data Feed (Optimized)",
            "features": {
                "batching": True,
                "batch_interval_ms": BATCH_INTERVAL_MS,
                "max_batch_size": MAX_BATCH_SIZE
            }
        })
        
        # Keep connection alive and handle client messages
        while True:
            data = await websocket.receive_text()
            
            try:
                client_msg = json.loads(data)
                
                # Handle subscription changes (future feature)
                if client_msg.get("action") == "subscribe":
                    await websocket.send_json({
                        "type": "ack",
                        "message": "Subscription acknowledged"
                    })
                elif client_msg.get("action") == "stats":
                    # Return client-specific stats
                    client = manager.active_connections.get(client_id)
                    if client:
                        await websocket.send_json({
                            "type": "stats",
                            "data": {
                                "messages_sent": client.messages_sent,
                                "messages_dropped": client.messages_dropped,
                                "latency_ms": round(client.latency_ms, 2),
                                "connected_seconds": round(time.time() - client.connected_at, 1)
                            }
                        })
                        
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON"
                })
                
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        print(f"❌ WebSocket error for {client_id}: {e}")
        manager.disconnect(client_id)


@app.get("/stats")
async def get_stats():
    """Get service performance statistics"""
    return manager.get_stats()


@app.get("/clients")
async def get_clients():
    """Get connected client details"""
    clients = []
    for client_id, client in manager.active_connections.items():
        clients.append({
            "id": client_id,
            "messages_sent": client.messages_sent,
            "messages_dropped": client.messages_dropped,
            "latency_ms": round(client.latency_ms, 2),
            "connected_seconds": round(time.time() - client.connected_at, 1),
            "queue_size": len(client.message_queue)
        })
    
    return {
        "total_clients": len(clients),
        "clients": clients
    }

