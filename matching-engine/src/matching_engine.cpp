#include "matching_engine.hpp"
#include <sstream>
#include <iomanip>

MatchingEngine::MatchingEngine() {
    // Initialize with default BTC-USDT order book
    order_books_["BTC-USDT"] = OrderBook();
}

void MatchingEngine::process_order(Order order) {
    // Get or create order book for symbol
    auto& book = order_books_[order.symbol];
    
    // Dispatch based on order type
    switch (order.type) {
        case OrderType::MARKET:
            match_market_order(order, book);
            break;
        case OrderType::LIMIT:
            match_limit_order(order, book);
            break;
        case OrderType::IOC:
            match_ioc_order(order, book);
            break;
        case OrderType::FOK:
            match_fok_order(order, book);
            break;
    }
}

OrderBook& MatchingEngine::get_book(const std::string& symbol) {
    return order_books_[symbol];
}

const OrderBook& MatchingEngine::get_book(const std::string& symbol) const {
    return order_books_.at(symbol);
}

std::string MatchingEngine::generate_trade_id() {
    std::ostringstream oss;
    oss << "T" << std::setw(4) << std::setfill('0') << ++trade_counter_;
    return oss.str();
}

// Market order matching (FR-2.1)
void MatchingEngine::match_market_order(Order order, OrderBook& book) {
    // Determine counter-side (buy orders match against asks, sell orders against bids)
    Side counter_side = (order.side == Side::BUY) ? Side::SELL : Side::BUY;
    
    // Match while order has remaining quantity AND counter-side has liquidity
    while (order.remaining_quantity > 0) {
        // Get best price on counter-side
        auto best_price = (counter_side == Side::BUY) 
            ? book.get_best_bid() 
            : book.get_best_ask();
        
        if (!best_price.has_value()) {
            // No more liquidity - market order consumed what was available
            break;
        }
        
        // Get orders at best price level (FIFO)
        auto* orders_at_price = book.get_orders_at_price(counter_side, best_price.value());
        if (!orders_at_price || orders_at_price->empty()) {
            // Price level disappeared (shouldn't happen but safety check)
            break;
        }
        
        // Match against first order in FIFO queue (time priority)
        Order& resting_order = orders_at_price->front();
        
        // Determine fill quantity (min of incoming and resting quantities)
        Quantity fill_qty = std::min(order.remaining_quantity, resting_order.remaining_quantity);
        
        // Generate trade event
        Trade trade = generate_trade(resting_order, order, fill_qty);
        trade_history_.push_back(trade);
        
        // Update remaining quantities
        order.remaining_quantity -= fill_qty;
        resting_order.remaining_quantity -= fill_qty;
        
        // If resting order fully filled, remove it from book
        if (resting_order.remaining_quantity == 0) {
            book.cancel_order(resting_order.id);
        }
    }
    
    // Market order never rests - consumed or unfilled
    // (remaining_quantity is discarded if book runs out of liquidity)
}

void MatchingEngine::match_limit_order(Order order, OrderBook& book) {
    // Determine counter-side
    Side counter_side = (order.side == Side::BUY) ? Side::SELL : Side::BUY;
    
    // Try to match while order has remaining quantity
    while (order.remaining_quantity > 0) {
        // Get best price on counter-side
        auto best_price = (counter_side == Side::BUY) 
            ? book.get_best_bid() 
            : book.get_best_ask();
        
        if (!best_price.has_value()) {
            // No counter-side liquidity, rest order on book
            break;
        }
        
        // Check if limit order is marketable
        bool is_marketable = false;
        if (order.side == Side::BUY) {
            // Buy limit is marketable if willing to pay >= best ask
            is_marketable = (order.price >= best_price.value());
        } else {
            // Sell limit is marketable if willing to accept <= best bid
            is_marketable = (order.price <= best_price.value());
        }
        
        if (!is_marketable) {
            // Price limit prevents matching, rest on book
            break;
        }
        
        // Get orders at best price level
        auto* orders_at_price = book.get_orders_at_price(counter_side, best_price.value());
        if (!orders_at_price || orders_at_price->empty()) {
            break;
        }
        
        // Match against first order in FIFO queue
        Order& resting_order = orders_at_price->front();
        
        // Determine fill quantity
        Quantity fill_qty = std::min(order.remaining_quantity, resting_order.remaining_quantity);
        
        // Generate trade event
        Trade trade = generate_trade(resting_order, order, fill_qty);
        trade_history_.push_back(trade);
        
        // Update remaining quantities
        order.remaining_quantity -= fill_qty;
        resting_order.remaining_quantity -= fill_qty;
        
        // If resting order fully filled, remove it
        if (resting_order.remaining_quantity == 0) {
            book.cancel_order(resting_order.id);
        }
    }
    
    // If order has remaining quantity, rest it on the book
    if (order.remaining_quantity > 0) {
        book.add_order(order);
    }
}

void MatchingEngine::match_ioc_order(Order order, OrderBook& book) {
    // IOC (Immediate-Or-Cancel) is like a limit order but never rests
    // Same matching logic as limit, but remainder is cancelled instead of rested
    
    Side counter_side = (order.side == Side::BUY) ? Side::SELL : Side::BUY;
    
    while (order.remaining_quantity > 0) {
        auto best_price = (counter_side == Side::BUY) 
            ? book.get_best_bid() 
            : book.get_best_ask();
        
        if (!best_price.has_value()) {
            break;  // No liquidity, cancel remainder
        }
        
        // Check if marketable
        bool is_marketable = false;
        if (order.side == Side::BUY) {
            is_marketable = (order.price >= best_price.value());
        } else {
            is_marketable = (order.price <= best_price.value());
        }
        
        if (!is_marketable) {
            break;  // Not marketable, cancel remainder
        }
        
        auto* orders_at_price = book.get_orders_at_price(counter_side, best_price.value());
        if (!orders_at_price || orders_at_price->empty()) {
            break;
        }
        
        Order& resting_order = orders_at_price->front();
        Quantity fill_qty = std::min(order.remaining_quantity, resting_order.remaining_quantity);
        
        Trade trade = generate_trade(resting_order, order, fill_qty);
        trade_history_.push_back(trade);
        
        order.remaining_quantity -= fill_qty;
        resting_order.remaining_quantity -= fill_qty;
        
        if (resting_order.remaining_quantity == 0) {
            book.cancel_order(resting_order.id);
        }
    }
    
    // IOC never rests - any unfilled quantity is cancelled
    // (order.remaining_quantity is simply discarded)
}

void MatchingEngine::match_fok_order(Order order, OrderBook& book) {
    // FOK (Fill-Or-Kill): Check if can fill completely, if yes execute, if no cancel
    
    // Pre-check: Can this order be completely filled?
    if (!can_fill_completely(order, book)) {
        // Cannot fill completely, cancel entire order (no partial fills)
        return;
    }
    
    // Can fill completely, execute like IOC
    Side counter_side = (order.side == Side::BUY) ? Side::SELL : Side::BUY;
    
    while (order.remaining_quantity > 0) {
        auto best_price = (counter_side == Side::BUY) 
            ? book.get_best_bid() 
            : book.get_best_ask();
        
        if (!best_price.has_value()) {
            break;
        }
        
        bool is_marketable = false;
        if (order.side == Side::BUY) {
            is_marketable = (order.price >= best_price.value());
        } else {
            is_marketable = (order.price <= best_price.value());
        }
        
        if (!is_marketable) {
            break;
        }
        
        auto* orders_at_price = book.get_orders_at_price(counter_side, best_price.value());
        if (!orders_at_price || orders_at_price->empty()) {
            break;
        }
        
        Order& resting_order = orders_at_price->front();
        Quantity fill_qty = std::min(order.remaining_quantity, resting_order.remaining_quantity);
        
        Trade trade = generate_trade(resting_order, order, fill_qty);
        trade_history_.push_back(trade);
        
        order.remaining_quantity -= fill_qty;
        resting_order.remaining_quantity -= fill_qty;
        
        if (resting_order.remaining_quantity == 0) {
            book.cancel_order(resting_order.id);
        }
    }
    
    // FOK should fill completely (we pre-checked), so remaining should be 0
    // If not, something went wrong with can_fill_completely check
}

bool MatchingEngine::can_fill_completely(const Order& order, const OrderBook& book) const {
    // Check if order can be completely filled without executing
    // Use helper method to get total available liquidity within price limit
    
    Side counter_side = (order.side == Side::BUY) ? Side::SELL : Side::BUY;
    
    // Get total liquidity available within our price limit
    Quantity available = book.get_available_liquidity(counter_side, order.price);
    
    // Can fill if available >= needed
    return (available >= order.remaining_quantity);
}

Trade MatchingEngine::generate_trade(const Order& maker, Order& taker, Quantity fill_qty) {
    return Trade(
        generate_trade_id(),
        maker.symbol,
        maker.id,
        taker.id,
        maker.price,  // Maker price (price-time priority)
        fill_qty,
        taker.side,   // Taker is aggressor
        static_cast<Timestamp>(std::time(nullptr))
    );
}

