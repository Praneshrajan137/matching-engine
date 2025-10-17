"""
Python Wrapper for C++ Matching Engine
Connects Redis to the C++ matching logic

This is a TEMPORARY solution to demonstrate end-to-end functionality.
The proper solution is to integrate hiredis into engine_runner.cpp.
"""

import json
import redis
import sys
from pathlib import Path

# Add matching-engine Python bindings to path (if available)
# For now, we'll use a pure Python port of the matching logic
sys.path.append(str(Path(__file__).parent.parent / "matching-engine" / "src"))


class Order:
    """Order representation matching C++ Order struct"""
    def __init__(self, id, symbol, side, order_type, price, quantity, timestamp):
        self.id = id
        self.symbol = symbol
        self.side = side  # "buy" or "sell"
        self.order_type = order_type  # "market", "limit", "ioc", "fok"
        self.price = float(price) if price else 0.0
        self.quantity = float(quantity)
        self.remaining_quantity = float(quantity)
        self.timestamp = timestamp


class LimitLevel:
    """Price level with FIFO order queue"""
    def __init__(self):
        self.orders = []  # List maintains FIFO order
        self.total_quantity = 0.0


class OrderBook:
    """
    Order book implementing price-time priority
    Python port of C++ OrderBook class
    """
    def __init__(self):
        self.bids = {}  # price -> LimitLevel (sorted desc)
        self.asks = {}  # price -> LimitLevel (sorted asc)
        self.order_index = {}  # order_id -> (price, side)
    
    def add_order(self, order):
        """Add order to book"""
        book = self.bids if order.side == "buy" else self.asks
        
        if order.price not in book:
            book[order.price] = LimitLevel()
        
        level = book[order.price]
        level.orders.append(order)
        level.total_quantity += order.remaining_quantity
        self.order_index[order.id] = (order.price, order.side)
    
    def cancel_order(self, order_id):
        """Remove order from book"""
        if order_id not in self.order_index:
            return False
        
        price, side = self.order_index[order_id]
        book = self.bids if side == "buy" else self.asks
        
        if price not in book:
            return False
        
        level = book[price]
        for i, order in enumerate(level.orders):
            if order.id == order_id:
                level.total_quantity -= order.remaining_quantity
                del level.orders[i]
                
                if len(level.orders) == 0:
                    del book[price]
                
                del self.order_index[order_id]
                return True
        
        return False
    
    def get_best_bid(self):
        """Get highest bid price"""
        return max(self.bids.keys()) if self.bids else None
    
    def get_best_ask(self):
        """Get lowest ask price"""
        return min(self.asks.keys()) if self.asks else None
    
    def get_orders_at_price(self, side, price):
        """Get list of orders at given price"""
        book = self.bids if side == "buy" else self.asks
        return book.get(price, LimitLevel()).orders


class MatchingEngine:
    """
    Matching engine with price-time priority
    Python port of C++ MatchingEngine class
    """
    def __init__(self):
        self.order_books = {}  # symbol -> OrderBook
        self.trade_history = []
        self.trade_counter = 0
    
    def get_book(self, symbol):
        """Get or create order book for symbol"""
        if symbol not in self.order_books:
            self.order_books[symbol] = OrderBook()
        return self.order_books[symbol]
    
    def generate_trade_id(self):
        """Generate deterministic trade ID"""
        self.trade_counter += 1
        return f"T{self.trade_counter:04d}"
    
    def generate_trade(self, maker, taker, fill_qty):
        """Generate trade event"""
        return {
            "trade_id": self.generate_trade_id(),
            "symbol": maker.symbol,
            "maker_order_id": maker.id,
            "taker_order_id": taker.id,
            "price": str(maker.price),
            "quantity": str(fill_qty),
            "aggressor_side": taker.side,
            "timestamp": taker.timestamp
        }
    
    def process_order(self, order):
        """Main entry point - dispatches to order type handler"""
        book = self.get_book(order.symbol)
        
        if order.order_type == "market":
            self.match_market_order(order, book)
        elif order.order_type == "limit":
            self.match_limit_order(order, book)
        elif order.order_type == "ioc":
            self.match_ioc_order(order, book)
        elif order.order_type == "fok":
            self.match_fok_order(order, book)
    
    def match_market_order(self, order, book):
        """Market order - immediate execution, never rests"""
        counter_side = "sell" if order.side == "buy" else "buy"
        
        while order.remaining_quantity > 0:
            best_price = book.get_best_ask() if order.side == "buy" else book.get_best_bid()
            
            if best_price is None:
                break
            
            orders_at_price = book.get_orders_at_price(counter_side, best_price)
            if not orders_at_price:
                break
            
            resting_order = orders_at_price[0]
            fill_qty = min(order.remaining_quantity, resting_order.remaining_quantity)
            
            trade = self.generate_trade(resting_order, order, fill_qty)
            self.trade_history.append(trade)
            
            order.remaining_quantity -= fill_qty
            resting_order.remaining_quantity -= fill_qty
            
            if resting_order.remaining_quantity == 0:
                book.cancel_order(resting_order.id)
    
    def match_limit_order(self, order, book):
        """Limit order - match at price or better, rest if not marketable"""
        counter_side = "sell" if order.side == "buy" else "buy"
        
        while order.remaining_quantity > 0:
            best_price = book.get_best_ask() if order.side == "buy" else book.get_best_bid()
            
            if best_price is None:
                break
            
            # Check if limit order is marketable
            is_marketable = False
            if order.side == "buy":
                is_marketable = order.price >= best_price
            else:
                is_marketable = order.price <= best_price
            
            if not is_marketable:
                break
            
            orders_at_price = book.get_orders_at_price(counter_side, best_price)
            if not orders_at_price:
                break
            
            resting_order = orders_at_price[0]
            fill_qty = min(order.remaining_quantity, resting_order.remaining_quantity)
            
            trade = self.generate_trade(resting_order, order, fill_qty)
            self.trade_history.append(trade)
            
            order.remaining_quantity -= fill_qty
            resting_order.remaining_quantity -= fill_qty
            
            if resting_order.remaining_quantity == 0:
                book.cancel_order(resting_order.id)
        
        # Rest remaining quantity on book
        if order.remaining_quantity > 0:
            book.add_order(order)
    
    def match_ioc_order(self, order, book):
        """IOC order - immediate-or-cancel, partial fills allowed"""
        counter_side = "sell" if order.side == "buy" else "buy"
        
        while order.remaining_quantity > 0:
            best_price = book.get_best_ask() if order.side == "buy" else book.get_best_bid()
            
            if best_price is None:
                break
            
            # Check price limit
            is_marketable = False
            if order.side == "buy":
                is_marketable = order.price >= best_price
            else:
                is_marketable = order.price <= best_price
            
            if not is_marketable:
                break
            
            orders_at_price = book.get_orders_at_price(counter_side, best_price)
            if not orders_at_price:
                break
            
            resting_order = orders_at_price[0]
            fill_qty = min(order.remaining_quantity, resting_order.remaining_quantity)
            
            trade = self.generate_trade(resting_order, order, fill_qty)
            self.trade_history.append(trade)
            
            order.remaining_quantity -= fill_qty
            resting_order.remaining_quantity -= fill_qty
            
            if resting_order.remaining_quantity == 0:
                book.cancel_order(resting_order.id)
        
        # IOC never rests - remaining quantity is cancelled
    
    def match_fok_order(self, order, book):
        """FOK order - fill-or-kill, all-or-nothing"""
        counter_side = "sell" if order.side == "buy" else "buy"
        
        # Pre-check: Can we fill the entire order?
        available_qty = 0.0
        book_copy = self.bids if counter_side == "buy" else self.asks
        
        for price in sorted(book_copy.keys(), reverse=(counter_side == "buy")):
            # Check price limit
            is_acceptable = False
            if order.side == "buy":
                is_acceptable = order.price >= price
            else:
                is_acceptable = order.price <= price
            
            if not is_acceptable:
                break
            
            level = book_copy[price]
            available_qty += level.total_quantity
            
            if available_qty >= order.quantity:
                break
        
        if available_qty < order.quantity:
            # Cannot fill completely - cancel entire order
            return
        
        # Can fill - proceed with matching
        while order.remaining_quantity > 0:
            best_price = book.get_best_ask() if order.side == "buy" else book.get_best_bid()
            
            orders_at_price = book.get_orders_at_price(counter_side, best_price)
            if not orders_at_price:
                break
            
            resting_order = orders_at_price[0]
            fill_qty = min(order.remaining_quantity, resting_order.remaining_quantity)
            
            trade = self.generate_trade(resting_order, order, fill_qty)
            self.trade_history.append(trade)
            
            order.remaining_quantity -= fill_qty
            resting_order.remaining_quantity -= fill_qty
            
            if resting_order.remaining_quantity == 0:
                book.cancel_order(resting_order.id)
    
    def get_recent_trades(self):
        """Get trades since last call (and clear)"""
        trades = self.trade_history.copy()
        self.trade_history.clear()
        return trades


def main():
    """Main event loop"""
    print("🚀 GoQuant Python Engine Wrapper")
    print("=" * 50)
    print("Connecting to Redis...")
    
    # Connect to Redis
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    
    try:
        redis_client.ping()
        print("✅ Connected to Redis at localhost:6379")
    except redis.ConnectionError:
        print("❌ ERROR: Cannot connect to Redis")
        print("   Make sure Redis is running: docker ps")
        return
    
    # Initialize matching engine
    engine = MatchingEngine()
    print("✅ Matching Engine initialized")
    print("📥 Listening for orders on 'order_queue'...")
    print("   Press Ctrl+C to stop")
    print()
    
    # Main event loop
    while True:
        try:
            # BLPOP order from queue (blocking, 1 second timeout)
            result = redis_client.blpop("order_queue", timeout=1)
            
            if result is None:
                # Timeout - no orders
                continue
            
            _, order_json_str = result
            print(f"📨 Received order: {order_json_str[:100]}...")
            
            # Parse JSON
            order_data = json.loads(order_json_str)
            
            # Create Order object
            order = Order(
                id=order_data["id"],
                symbol=order_data["symbol"],
                side=order_data["side"],
                order_type=order_data["order_type"],
                price=order_data.get("price"),
                quantity=order_data["quantity"],
                timestamp=order_data["timestamp"]
            )
            
            print(f"🔍 Processing {order.side.upper()} {order.order_type.upper()} "
                  f"{order.quantity} {order.symbol} (ID: {order.id[:8]}...)")
            
            # Process order through matching engine
            engine.process_order(order)
            
            # Get generated trades
            trades = engine.get_recent_trades()
            
            if not trades:
                print("   📝 Order rested on book (no immediate match)")
            else:
                print(f"   ✅ Generated {len(trades)} trade(s)")
                
                # Publish each trade to Redis
                for trade in trades:
                    trade_json = json.dumps(trade)
                    redis_client.publish("trade_events", trade_json)
                    
                    print(f"      💰 Trade {trade['trade_id']}: "
                          f"{trade['quantity']} @ ${trade['price']}")
            
            print()
            
        except KeyboardInterrupt:
            print("\n👋 Shutting down gracefully...")
            break
        except Exception as e:
            print(f"❌ Error processing order: {e}")
            import traceback
            traceback.print_exc()
            # Continue processing next order


if __name__ == "__main__":
    main()

