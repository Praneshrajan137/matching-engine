#pragma once

#include <string>
#include <cstdint>

// Forward declarations
using Price = double;
using Quantity = double;
using OrderID = std::string;
using Timestamp = uint64_t;

/**
 * @brief Side of the order (buy or sell)
 */
enum class Side {
    BUY,
    SELL
};

/**
 * @brief Type of order
 */
enum class OrderType {
    MARKET,
    LIMIT,
    IOC,  // Immediate-Or-Cancel
    FOK   // Fill-Or-Kill
};

/**
 * @brief Represents a single order in the matching engine
 * 
 * Implements FR-2.1 through FR-2.4 (order type support)
 */
struct Order {
    OrderID id;
    Side side;
    OrderType type;
    Price price;  // Only used for LIMIT orders
    Quantity quantity;
    Quantity remaining_quantity;
    Timestamp timestamp;
    
    Order() = default;
    
    Order(OrderID id_, Side side_, OrderType type_, Price price_, 
          Quantity quantity_, Timestamp timestamp_)
        : id(id_)
        , side(side_)
        , type(type_)
        , price(price_)
        , quantity(quantity_)
        , remaining_quantity(quantity_)
        , timestamp(timestamp_)
    {}
};

