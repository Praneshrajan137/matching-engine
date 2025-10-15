#pragma once

#include "order.hpp"
#include <map>
#include <list>
#include <unordered_map>
#include <optional>
#include <memory>

/**
 * @brief Price level containing orders at the same price (FIFO queue)
 * 
 * Implements time-priority within each price level (FR-1.1)
 */
struct LimitLevel {
    std::list<Order> orders;  // FIFO queue for time priority
    Quantity total_quantity;   // Cached sum for fast BBO calculation
    
    LimitLevel() : total_quantity(0.0) {}
};

/**
 * @brief Order book implementing price-time priority matching
 * 
 * Data structure implements:
 * - FR-1.1: Price-time priority matching
 * - FR-1.2: Prevent trade-throughs
 * - FR-1.3: Real-time BBO calculation
 * - FR-1.4: Instantaneous BBO updates
 * 
 * Time complexity targets:
 * - Add order (new price): O(log M) where M = number of price levels
 * - Add order (existing price): O(1)
 * - Cancel order: O(1)
 * - Get BBO: O(1)
 */
class OrderBook {
public:
    OrderBook();
    ~OrderBook() = default;
    
    // Core operations (to be implemented via TDD)
    
    /**
     * @brief Add order to the book
     * @param order Order to add
     * 
     * TODO: Implement via TDD (test-expert will write tests first)
     */
    void add_order(const Order& order);
    
    /**
     * @brief Cancel order by ID
     * @param order_id ID of order to cancel
     * @return true if order was found and cancelled, false otherwise
     * 
     * TODO: Implement via TDD
     */
    bool cancel_order(const OrderID& order_id);
    
    /**
     * @brief Get best bid price
     * @return Best bid price, or nullopt if no bids
     * 
     * TODO: Implement via TDD
     */
    std::optional<Price> get_best_bid() const;
    
    /**
     * @brief Get best ask price
     * @return Best ask price, or nullopt if no asks
     * 
     * TODO: Implement via TDD
     */
    std::optional<Price> get_best_ask() const;
    
    /**
     * @brief Get total quantity at a specific price level
     * @param side BUY or SELL
     * @param price Price level to query
     * @return Total quantity, or 0.0 if price level doesn't exist
     * 
     * TODO: Implement via TDD
     */
    Quantity get_total_quantity(Side side, Price price) const;
    
    /**
     * @brief Get number of price levels on given side
     * @param side BUY or SELL
     * @return Number of active price levels
     * 
     * TODO: Implement via TDD
     */
    size_t price_level_count(Side side) const;
    
    /**
     * @brief Get reference to orders at specific price level (for matching)
     * @param side BUY or SELL
     * @param price Price level to query
     * @return Pointer to list of orders at that price, or nullptr if level doesn't exist
     */
    const std::list<Order>* get_orders_at_price(Side side, Price price) const;
    std::list<Order>* get_orders_at_price(Side side, Price price);

private:
    // Bid side: Sorted in descending order (best bid = highest price)
    // Uses std::greater for max-heap behavior
    std::map<Price, LimitLevel, std::greater<Price>> bids_;
    
    // Ask side: Sorted in ascending order (best ask = lowest price)
    // Uses default std::less for min-heap behavior
    std::map<Price, LimitLevel> asks_;
    
    // Index for O(1) order cancellation
    // Maps OrderID -> iterator into the order list
    std::unordered_map<OrderID, std::list<Order>::iterator> order_index_;
};

