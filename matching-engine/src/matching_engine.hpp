#pragma once
#include "order_book.hpp"
#include "order.hpp"
#include <vector>
#include <unordered_map>  // FIXED: Added missing include
#include <string>          // FIXED: Added missing include
#include <chrono>          // FIXED: Added missing include
#include <functional>
#include <optional>
#include <ctime>

/**
 * @brief Trade execution event
 * Generated when orders match
 * Implements FR-2.1 through FR-2.4 trade reporting
 */
struct Trade {
    std::string trade_id;      // Format: T0001, T0002, etc. (deterministic for tests)
    std::string symbol;
    std::string maker_order_id;
    std::string taker_order_id;
    Price price;
    Quantity quantity;
    Side aggressor_side;
    Timestamp timestamp;
    
    Trade(std::string id, std::string sym, std::string maker, std::string taker,
          Price p, Quantity q, Side side, Timestamp ts)
        : trade_id(id), symbol(sym), maker_order_id(maker), taker_order_id(taker),
          price(p), quantity(q), aggressor_side(side), timestamp(ts) {}
};

/**
 * @brief Matching engine implementing price-time priority
 * Implements FR-2.1 through FR-2.4 (all order types)
 * 
 * Supports:
 * - Market orders: Immediate execution at best available prices
 * - Limit orders: Execute at specified price or better, rest if not marketable
 * - IOC orders: Fill immediately, cancel remainder
 * - FOK orders: Fill completely or cancel all
 */
class MatchingEngine {
public:
    MatchingEngine();
    
    // Main entry point - processes any order type
    void process_order(Order order);  // FIXED: Pass by value, not const&
    
    // Accessors
    const std::vector<Trade>& get_trades() const { return trade_history_; }
    OrderBook& get_book(const std::string& symbol);
    const OrderBook& get_book(const std::string& symbol) const;
    
private:
    std::unordered_map<std::string, OrderBook> order_books_;
    std::vector<Trade> trade_history_;
    size_t trade_counter_ = 0;  // FIXED: For deterministic trade IDs
    
    // Order type handlers (FIXED: Pass by value to allow mutation)
    void match_market_order(Order order, OrderBook& book);
    void match_limit_order(Order order, OrderBook& book);
    void match_ioc_order(Order order, OrderBook& book);
    void match_fok_order(Order order, OrderBook& book);
    
    // Helper methods
    bool can_fill_completely(const Order& order, const OrderBook& book) const;  // FIXED: Added for FOK
    Trade generate_trade(const Order& maker, Order& taker, Quantity fill_qty);
    std::string generate_trade_id();  // FIXED: Deterministic ID generation
};

