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
    // TODO: Implement full limit order matching (marketable vs. resting)
    // For now, just rest the order on the book (non-marketable case)
    book.add_order(order);
}

void MatchingEngine::match_ioc_order(Order order, OrderBook& book) {
    (void)order;
    (void)book;
}

void MatchingEngine::match_fok_order(Order order, OrderBook& book) {
    (void)order;
    (void)book;
}

bool MatchingEngine::can_fill_completely(const Order& order, const OrderBook& book) const {
    (void)order;
    (void)book;
    return false;
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

