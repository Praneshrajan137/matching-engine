"""
Python Matching Engine - Port of C++ Implementation
Implements FR-2.1 through FR-2.4 (all order types)

This module mirrors the C++ matching engine logic for integration testing.
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from decimal import Decimal
from collections import defaultdict, deque
import time


class Side(Enum):
    """Order side enumeration"""
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    """Order type enumeration"""
    MARKET = "market"
    LIMIT = "limit"
    IOC = "ioc"  # Immediate-Or-Cancel
    FOK = "fok"  # Fill-Or-Kill


@dataclass
class Order:
    """Represents a single order"""
    id: str
    symbol: str
    side: Side
    order_type: OrderType
    quantity: Decimal
    price: Optional[Decimal] = None
    remaining_quantity: Optional[Decimal] = None
    timestamp: int = field(default_factory=lambda: int(time.time()))
    
    def __post_init__(self):
        if self.remaining_quantity is None:
            self.remaining_quantity = self.quantity


@dataclass
class Trade:
    """Trade execution event"""
    trade_id: str
    symbol: str
    maker_order_id: str
    taker_order_id: str
    price: Decimal
    quantity: Decimal
    aggressor_side: Side
    timestamp: int = field(default_factory=lambda: int(time.time()))
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "trade_id": self.trade_id,
            "symbol": self.symbol,
            "maker_order_id": self.maker_order_id,
            "taker_order_id": self.taker_order_id,
            "price": str(self.price),
            "quantity": str(self.quantity),
            "aggressor_side": self.aggressor_side.value,
            "timestamp": self.timestamp
        }


class OrderBook:
    """
    Order book implementing price-time priority matching
    
    Data structure:
    - Bids: Sorted descending (best bid = highest price)
    - Asks: Sorted ascending (best ask = lowest price)
    - Time priority: FIFO within each price level
    """
    
    def __init__(self):
        # Price levels: {price: deque of orders}
        self.bids: Dict[Decimal, deque] = {}
        self.asks: Dict[Decimal, deque] = {}
        
        # Order index for O(1) cancellation
        self.order_index: Dict[str, Tuple[Side, Decimal]] = {}
    
    def add_order(self, order: Order) -> None:
        """Add order to book (O(1) for existing price, O(log M) for new price)"""
        price_levels = self.bids if order.side == Side.BUY else self.asks
        
        if order.price not in price_levels:
            price_levels[order.price] = deque()
        
        price_levels[order.price].append(order)
        self.order_index[order.id] = (order.side, order.price)
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel order by ID (O(1) complexity)"""
        if order_id not in self.order_index:
            return False
        
        side, price = self.order_index[order_id]
        price_levels = self.bids if side == Side.BUY else self.asks
        
        if price not in price_levels:
            return False
        
        # Remove order from deque
        orders = price_levels[price]
        for i, order in enumerate(orders):
            if order.id == order_id:
                del orders[i]
                break
        
        # Remove price level if empty
        if len(orders) == 0:
            del price_levels[price]
        
        # Remove from index
        del self.order_index[order_id]
        return True
    
    def get_best_bid(self) -> Optional[Decimal]:
        """Get best bid price (O(n) where n = number of price levels)"""
        if not self.bids:
            return None
        return max(self.bids.keys())
    
    def get_best_ask(self) -> Optional[Decimal]:
        """Get best ask price (O(n) where n = number of price levels)"""
        if not self.asks:
            return None
        return min(self.asks.keys())
    
    def get_orders_at_price(self, side: Side, price: Decimal) -> Optional[deque]:
        """Get orders at specific price level"""
        price_levels = self.bids if side == Side.BUY else self.asks
        return price_levels.get(price)
    
    def get_available_liquidity(self, side: Side, limit_price: Decimal) -> Decimal:
        """Get total available liquidity up to price limit (for FOK pre-check)"""
        total = Decimal(0)
        price_levels = self.bids if side == Side.BUY else self.asks
        
        for price, orders in price_levels.items():
            if side == Side.BUY:
                # For buy orders, check bids >= limit_price
                if price >= limit_price:
                    total += sum(order.remaining_quantity for order in orders)
            else:
                # For sell orders, check asks <= limit_price
                if price <= limit_price:
                    total += sum(order.remaining_quantity for order in orders)
        
        return total


class MatchingEngine:
    """
    Matching engine implementing price-time priority
    Supports: Market, Limit, IOC, FOK order types
    """
    
    def __init__(self):
        self.order_books: Dict[str, OrderBook] = defaultdict(OrderBook)
        self.trade_history: List[Trade] = []
        self.trade_counter = 0
    
    def process_order(self, order: Order) -> List[Trade]:
        """Main entry point - processes any order type"""
        book = self.order_books[order.symbol]
        trades_before = len(self.trade_history)
        
        # Dispatch based on order type
        if order.order_type == OrderType.MARKET:
            self._match_market_order(order, book)
        elif order.order_type == OrderType.LIMIT:
            self._match_limit_order(order, book)
        elif order.order_type == OrderType.IOC:
            self._match_ioc_order(order, book)
        elif order.order_type == OrderType.FOK:
            self._match_fok_order(order, book)
        
        # Return trades generated for this order
        return self.trade_history[trades_before:]
    
    def _match_market_order(self, order: Order, book: OrderBook) -> None:
        """Match market order (FR-2.1)"""
        counter_side = Side.SELL if order.side == Side.BUY else Side.BUY
        
        while order.remaining_quantity > 0:
            best_price = book.get_best_ask() if counter_side == Side.SELL else book.get_best_bid()
            
            if best_price is None:
                break  # No more liquidity
            
            orders_at_price = book.get_orders_at_price(counter_side, best_price)
            if not orders_at_price or len(orders_at_price) == 0:
                break
            
            resting_order = orders_at_price[0]
            fill_qty = min(order.remaining_quantity, resting_order.remaining_quantity)
            
            # Generate trade
            trade = self._generate_trade(resting_order, order, fill_qty)
            self.trade_history.append(trade)
            
            # Update quantities
            order.remaining_quantity -= fill_qty
            resting_order.remaining_quantity -= fill_qty
            
            # Remove fully filled resting order
            if resting_order.remaining_quantity == 0:
                book.cancel_order(resting_order.id)
    
    def _match_limit_order(self, order: Order, book: OrderBook) -> None:
        """Match limit order (FR-2.2)"""
        counter_side = Side.SELL if order.side == Side.BUY else Side.BUY
        
        while order.remaining_quantity > 0:
            best_price = book.get_best_ask() if counter_side == Side.SELL else book.get_best_bid()
            
            if best_price is None:
                break
            
            # Check if marketable
            is_marketable = (
                (order.side == Side.BUY and order.price >= best_price) or
                (order.side == Side.SELL and order.price <= best_price)
            )
            
            if not is_marketable:
                break
            
            orders_at_price = book.get_orders_at_price(counter_side, best_price)
            if not orders_at_price or len(orders_at_price) == 0:
                break
            
            resting_order = orders_at_price[0]
            fill_qty = min(order.remaining_quantity, resting_order.remaining_quantity)
            
            trade = self._generate_trade(resting_order, order, fill_qty)
            self.trade_history.append(trade)
            
            order.remaining_quantity -= fill_qty
            resting_order.remaining_quantity -= fill_qty
            
            if resting_order.remaining_quantity == 0:
                book.cancel_order(resting_order.id)
        
        # Rest unfilled portion on book
        if order.remaining_quantity > 0:
            book.add_order(order)
    
    def _match_ioc_order(self, order: Order, book: OrderBook) -> None:
        """Match IOC order (FR-2.3) - never rests"""
        counter_side = Side.SELL if order.side == Side.BUY else Side.BUY
        
        while order.remaining_quantity > 0:
            best_price = book.get_best_ask() if counter_side == Side.SELL else book.get_best_bid()
            
            if best_price is None:
                break
            
            is_marketable = (
                (order.side == Side.BUY and order.price >= best_price) or
                (order.side == Side.SELL and order.price <= best_price)
            )
            
            if not is_marketable:
                break
            
            orders_at_price = book.get_orders_at_price(counter_side, best_price)
            if not orders_at_price or len(orders_at_price) == 0:
                break
            
            resting_order = orders_at_price[0]
            fill_qty = min(order.remaining_quantity, resting_order.remaining_quantity)
            
            trade = self._generate_trade(resting_order, order, fill_qty)
            self.trade_history.append(trade)
            
            order.remaining_quantity -= fill_qty
            resting_order.remaining_quantity -= fill_qty
            
            if resting_order.remaining_quantity == 0:
                book.cancel_order(resting_order.id)
        
        # IOC never rests - unfilled portion cancelled
    
    def _match_fok_order(self, order: Order, book: OrderBook) -> None:
        """Match FOK order (FR-2.4) - all or nothing"""
        counter_side = Side.SELL if order.side == Side.BUY else Side.BUY
        
        # Pre-check: Can we fill completely?
        available = book.get_available_liquidity(counter_side, order.price)
        if available < order.remaining_quantity:
            return  # Cannot fill completely, cancel entire order
        
        # Can fill completely, execute
        while order.remaining_quantity > 0:
            best_price = book.get_best_ask() if counter_side == Side.SELL else book.get_best_bid()
            
            if best_price is None:
                break
            
            is_marketable = (
                (order.side == Side.BUY and order.price >= best_price) or
                (order.side == Side.SELL and order.price <= best_price)
            )
            
            if not is_marketable:
                break
            
            orders_at_price = book.get_orders_at_price(counter_side, best_price)
            if not orders_at_price or len(orders_at_price) == 0:
                break
            
            resting_order = orders_at_price[0]
            fill_qty = min(order.remaining_quantity, resting_order.remaining_quantity)
            
            trade = self._generate_trade(resting_order, order, fill_qty)
            self.trade_history.append(trade)
            
            order.remaining_quantity -= fill_qty
            resting_order.remaining_quantity -= fill_qty
            
            if resting_order.remaining_quantity == 0:
                book.cancel_order(resting_order.id)
    
    def _generate_trade(self, maker: Order, taker: Order, fill_qty: Decimal) -> Trade:
        """Generate trade execution event"""
        self.trade_counter += 1
        trade_id = f"T{self.trade_counter:04d}"
        
        return Trade(
            trade_id=trade_id,
            symbol=maker.symbol,
            maker_order_id=maker.id,
            taker_order_id=taker.id,
            price=maker.price,  # Maker price (price-time priority)
            quantity=fill_qty,
            aggressor_side=taker.side
        )
    
    def get_trades(self) -> List[Trade]:
        """Get all trade history"""
        return self.trade_history
    
    def get_book(self, symbol: str) -> OrderBook:
        """Get order book for symbol"""
        return self.order_books[symbol]

