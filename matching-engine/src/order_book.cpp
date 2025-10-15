#include "order_book.hpp"

OrderBook::OrderBook() {
    // Constructor - currently empty
    // Data structures initialized via member initialization
}

void OrderBook::add_order(const Order& order) {
    if (order.side == Side::BUY) {
        // 1. Find or create price level in bids - O(log M) for new price
        auto& level = bids_[order.price];
        
        // 2. Append to FIFO list - O(1)
        level.orders.push_back(order);
        
        // 3. Store iterator for O(1) cancellation
        auto it = std::prev(level.orders.end());
        order_index_[order.id] = it;
        
        // 4. Update cached quantity (use remaining_quantity for partially filled orders)
        level.total_quantity += order.remaining_quantity;
    } else {
        // Same logic for asks
        auto& level = asks_[order.price];
        level.orders.push_back(order);
        auto it = std::prev(level.orders.end());
        order_index_[order.id] = it;
        level.total_quantity += order.remaining_quantity;
    }
}

bool OrderBook::cancel_order(const OrderID& order_id) {
    // 1. Find order in index - O(1) hash lookup
    auto index_it = order_index_.find(order_id);
    if (index_it == order_index_.end()) {
        return false;  // Order not found
    }
    
    // 2. Get iterator to order in list
    auto order_it = index_it->second;
    const Order& order = *order_it;
    
    // 3. Find and update price level based on side
    if (order.side == Side::BUY) {
        auto level_it = bids_.find(order.price);
        level_it->second.total_quantity -= order.remaining_quantity;
        level_it->second.orders.erase(order_it);
        
        // Remove price level if empty
        if (level_it->second.orders.empty()) {
            bids_.erase(level_it);
        }
    } else {
        auto level_it = asks_.find(order.price);
        level_it->second.total_quantity -= order.remaining_quantity;
        level_it->second.orders.erase(order_it);
        
        // Remove price level if empty
        if (level_it->second.orders.empty()) {
            asks_.erase(level_it);
        }
    }
    
    // 4. Remove from index
    order_index_.erase(index_it);
    
    return true;
}

std::optional<Price> OrderBook::get_best_bid() const {
    // O(1) - first element in descending map is highest price
    if (bids_.empty()) {
        return std::nullopt;
    }
    return bids_.begin()->first;
}

std::optional<Price> OrderBook::get_best_ask() const {
    // O(1) - first element in ascending map is lowest price
    if (asks_.empty()) {
        return std::nullopt;
    }
    return asks_.begin()->first;
}

Quantity OrderBook::get_total_quantity(Side side, Price price) const {
    // O(log M) - binary search in map
    if (side == Side::BUY) {
        auto it = bids_.find(price);
        if (it == bids_.end()) {
            return 0.0;  // Price level doesn't exist
        }
        return it->second.total_quantity;
    } else {
        auto it = asks_.find(price);
        if (it == asks_.end()) {
            return 0.0;  // Price level doesn't exist
        }
        return it->second.total_quantity;
    }
}

size_t OrderBook::price_level_count(Side side) const {
    // O(1) - map maintains size
    return (side == Side::BUY) ? bids_.size() : asks_.size();
}

const std::list<Order>* OrderBook::get_orders_at_price(Side side, Price price) const {
    // O(log M) - binary search in map
    if (side == Side::BUY) {
        auto it = bids_.find(price);
        if (it == bids_.end()) return nullptr;
        return &(it->second.orders);
    } else {
        auto it = asks_.find(price);
        if (it == asks_.end()) return nullptr;
        return &(it->second.orders);
    }
}

std::list<Order>* OrderBook::get_orders_at_price(Side side, Price price) {
    // O(log M) - binary search in map
    if (side == Side::BUY) {
        auto it = bids_.find(price);
        if (it == bids_.end()) return nullptr;
        return &(it->second.orders);
    } else {
        auto it = asks_.find(price);
        if (it == asks_.end()) return nullptr;
        return &(it->second.orders);
    }
}

Quantity OrderBook::get_available_liquidity(Side side, Price limit_price) const {
    // Calculate total liquidity available within price limit
    Quantity total = 0.0;
    
    if (side == Side::SELL) {
        // For sell orders, check asks (counter-side)
        // Iterate through ask levels from best (lowest) up to limit price
        for (const auto& [price, level] : asks_) {
            if (price <= limit_price) {
                total += level.total_quantity;
            } else {
                break;  // Asks are sorted ascending, so we can stop here
            }
        }
    } else {
        // For buy orders, check bids (counter-side)
        // Iterate through bid levels from best (highest) down to limit price
        for (const auto& [price, level] : bids_) {
            if (price >= limit_price) {
                total += level.total_quantity;
            } else {
                break;  // Bids are sorted descending, so we can stop here
            }
        }
    }
    
    return total;
}

