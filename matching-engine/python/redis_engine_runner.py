"""
Redis Engine Runner - Python Wrapper for Matching Engine
Integrates with Order Gateway and Market Data services via Redis

Architecture:
1. BLPOP orders from "order_queue" (blocking read)
2. Process through MatchingEngine
3. PUBLISH trades to "trade_events" channel
"""

import redis
import json
import sys
import signal
import time
from decimal import Decimal
from typing import Optional
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from matching_engine import MatchingEngine, Order, Side, OrderType


# Configuration
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0
ORDER_QUEUE = "order_queue"
TRADE_EVENTS_CHANNEL = "trade_events"

# Global flag for graceful shutdown
running = True


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    global running
    print("\n🛑 Shutdown signal received")
    running = False


def parse_order_json(order_json: str) -> Order:
    """Parse JSON string to Order object"""
    data = json.loads(order_json)
    
    # Parse side
    side = Side.BUY if data["side"] == "buy" else Side.SELL
    
    # Parse order type
    order_type_map = {
        "market": OrderType.MARKET,
        "limit": OrderType.LIMIT,
        "ioc": OrderType.IOC,
        "fok": OrderType.FOK
    }
    order_type = order_type_map[data["order_type"]]
    
    # Parse price (optional for market orders)
    price = Decimal(data["price"]) if data.get("price") else None
    
    return Order(
        id=data["id"],
        symbol=data["symbol"],
        side=side,
        order_type=order_type,
        quantity=Decimal(data["quantity"]),
        price=price,
        timestamp=data.get("timestamp", int(time.time()))
    )


def main():
    """Main event loop"""
    global running
    
    print("🚀 GoQuant Python Matching Engine Runner")
    print("=" * 50)
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Connect to Redis
    try:
        redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        
        # Test connection
        redis_client.ping()
        print(f"✅ Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
        
    except redis.ConnectionError as e:
        print(f"❌ Failed to connect to Redis: {e}")
        print(f"   Make sure Redis is running: docker run -d -p 6379:6379 redis")
        return 1
    
    # Initialize matching engine
    engine = MatchingEngine()
    print("✅ Matching Engine initialized")
    print(f"📥 Listening for orders on '{ORDER_QUEUE}'...")
    print("   Press Ctrl+C to stop")
    print()
    
    # Main event loop
    order_count = 0
    trade_count = 0
    
    while running:
        try:
            # 1. BLPOP order from queue (blocking, 1 second timeout)
            result = redis_client.blpop(ORDER_QUEUE, timeout=1)
            
            if result is None:
                # Timeout - no orders in queue
                continue
            
            queue_name, order_json = result
            order_count += 1
            
            print(f"📨 Order #{order_count} received: {order_json[:100]}...")
            
            # 2. Parse JSON to Order object
            try:
                order = parse_order_json(order_json)
                
                print(f"🔍 Processing {order.side.value.upper()} {order.order_type.value.upper()} "
                      f"{order.quantity} {order.symbol} (ID: {order.id})")
                
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                print(f"❌ Invalid order JSON: {e}")
                continue
            
            # 3. Process order through matching engine
            trades = engine.process_order(order)
            
            # 4. Publish trades to Redis
            if trades:
                print(f"   ✅ Generated {len(trades)} trade(s)")
                
                for trade in trades:
                    trade_json = json.dumps(trade.to_dict())
                    redis_client.publish(TRADE_EVENTS_CHANNEL, trade_json)
                    trade_count += 1
                    
                    print(f"      Trade {trade.trade_id}: "
                          f"{trade.quantity} @ {trade.price}")
            else:
                print(f"   ℹ️  No trades generated (order rested or cancelled)")
            
            print()
            
        except redis.ConnectionError as e:
            print(f"❌ Redis connection error: {e}")
            print("   Attempting to reconnect...")
            time.sleep(1)
            
        except Exception as e:
            print(f"❌ Error processing order: {e}")
            import traceback
            traceback.print_exc()
            # Continue processing next order
    
    print()
    print("👋 Shutting down gracefully...")
    print(f"📊 Statistics:")
    print(f"   Orders processed: {order_count}")
    print(f"   Trades generated: {trade_count}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

