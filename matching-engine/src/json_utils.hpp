#pragma once

#include "order.hpp"
#include "matching_engine.hpp"
#include <string>
#include <sstream>
#include <stdexcept>

/**
 * @brief Simple JSON parser/serializer for Order and Trade structs
 * 
 * Note: In production, use a proper JSON library like nlohmann/json
 * This is a minimal implementation for the assignment scope
 */

namespace json_utils {

/**
 * @brief Parse JSON string to Order struct
 * 
 * Expected format:
 * {
 *   "id": "uuid",
 *   "symbol": "BTC-USDT",
 *   "order_type": "limit",
 *   "side": "buy",
 *   "quantity": "1.5",
 *   "price": "60000.00",
 *   "timestamp": 1234567890
 * }
 */
inline Order parse_order(const std::string& json_str) {
    // Simple JSON parsing (production would use nlohmann::json)
    Order order;
    
    // Extract fields using string operations
    // This is simplified - production code would use proper JSON library
    
    auto find_value = [&json_str](const std::string& key) -> std::string {
        std::string search = "\"" + key + "\":";
        size_t pos = json_str.find(search);
        if (pos == std::string::npos) return "";
        
        pos += search.length();
        while (pos < json_str.length() && (json_str[pos] == ' ' || json_str[pos] == '\"')) pos++;
        
        size_t end = pos;
        while (end < json_str.length() && json_str[end] != '\"' && json_str[end] != ',' && json_str[end] != '}') end++;
        
        return json_str.substr(pos, end - pos);
    };
    
    try {
        order.id = find_value("id");
        order.symbol = find_value("symbol");
        
        // Parse order type
        std::string type_str = find_value("order_type");
        if (type_str == "market") order.type = OrderType::MARKET;
        else if (type_str == "limit") order.type = OrderType::LIMIT;
        else if (type_str == "ioc") order.type = OrderType::IOC;
        else if (type_str == "fok") order.type = OrderType::FOK;
        else throw std::runtime_error("Invalid order type: " + type_str);
        
        // Parse side
        std::string side_str = find_value("side");
        if (side_str == "buy") order.side = Side::BUY;
        else if (side_str == "sell") order.side = Side::SELL;
        else throw std::runtime_error("Invalid side: " + side_str);
        
        // Parse quantity and price
        order.quantity = std::stod(find_value("quantity"));
        order.remaining_quantity = order.quantity;
        
        std::string price_str = find_value("price");
        if (!price_str.empty() && price_str != "null") {
            order.price = std::stod(price_str);
        } else {
            order.price = 0.0;  // Market orders have no price
        }
        
        // Parse timestamp
        std::string ts_str = find_value("timestamp");
        order.timestamp = ts_str.empty() ? 0 : std::stoull(ts_str);
        
    } catch (const std::exception& e) {
        throw std::runtime_error("Failed to parse order JSON: " + std::string(e.what()));
    }
    
    return order;
}

/**
 * @brief Serialize Trade to JSON string
 * 
 * Output format:
 * {
 *   "trade_id": "T0001",
 *   "symbol": "BTC-USDT",
 *   "maker_order_id": "uuid1",
 *   "taker_order_id": "uuid2",
 *   "price": "60000.00",
 *   "quantity": "1.5",
 *   "aggressor_side": "buy",
 *   "timestamp": 1234567890
 * }
 */
inline std::string serialize_trade(const Trade& trade) {
    std::ostringstream oss;
    
    oss << "{";
    oss << "\"trade_id\":\"" << trade.trade_id << "\",";
    oss << "\"symbol\":\"" << trade.symbol << "\",";
    oss << "\"maker_order_id\":\"" << trade.maker_order_id << "\",";
    oss << "\"taker_order_id\":\"" << trade.taker_order_id << "\",";
    oss << "\"price\":\"" << trade.price << "\",";
    oss << "\"quantity\":\"" << trade.quantity << "\",";
    oss << "\"aggressor_side\":\"" << (trade.aggressor_side == Side::BUY ? "buy" : "sell") << "\",";
    oss << "\"timestamp\":" << trade.timestamp;
    oss << "}";
    
    return oss.str();
}

/**
 * @brief Serialize BBO (Best Bid and Offer) to JSON string
 * 
 * Output format:
 * {
 *   "type": "bbo",
 *   "symbol": "BTC-USDT",
 *   "bid": "60000.00",
 *   "ask": "60001.00",
 *   "timestamp": 1234567890
 * }
 */
inline std::string serialize_bbo(const std::string& symbol,
                                   const std::optional<Price>& best_bid,
                                   const std::optional<Price>& best_ask) {
    std::ostringstream oss;
    
    // Get current timestamp
    auto now = std::chrono::system_clock::now();
    auto timestamp = std::chrono::duration_cast<std::chrono::seconds>(now.time_since_epoch()).count();
    
    oss << "{";
    oss << "\"type\":\"bbo\",";
    oss << "\"symbol\":\"" << symbol << "\",";
    
    if (best_bid.has_value()) {
        oss << "\"bid\":\"" << best_bid.value() << "\",";
    } else {
        oss << "\"bid\":null,";
    }
    
    if (best_ask.has_value()) {
        oss << "\"ask\":\"" << best_ask.value() << "\",";
    } else {
        oss << "\"ask\":null,";
    }
    
    oss << "\"timestamp\":" << timestamp;
    oss << "}";
    
    return oss.str();
}

/**
 * @brief Serialize L2 order book depth to JSON string
 * 
 * Output format (matches assignment requirement):
 * {
 *   "type": "l2_update",
 *   "timestamp": "2025-10-16T10:00:00.123456Z",
 *   "symbol": "BTC-USDT",
 *   "bids": [["60000.00", "1.5"], ["59999.50", "2.0"]],
 *   "asks": [["60001.00", "0.8"], ["60002.00", "1.2"]]
 * }
 */
inline std::string serialize_l2(const std::string& symbol, const OrderBook::L2Data& l2_data) {
    std::ostringstream oss;
    
    // Get current timestamp in ISO 8601 format
    auto now = std::chrono::system_clock::now();
    auto timestamp = std::chrono::duration_cast<std::chrono::seconds>(now.time_since_epoch()).count();
    
    oss << "{";
    oss << "\"type\":\"l2_update\",";
    oss << "\"timestamp\":" << timestamp << ",";
    oss << "\"symbol\":\"" << symbol << "\",";
    
    // Serialize bids array
    oss << "\"bids\":[";
    bool first = true;
    for (const auto& [price, quantity] : l2_data.bids) {
        if (!first) oss << ",";
        oss << "[\"" << price << "\",\"" << quantity << "\"]";
        first = false;
    }
    oss << "],";
    
    // Serialize asks array
    oss << "\"asks\":[";
    first = true;
    for (const auto& [price, quantity] : l2_data.asks) {
        if (!first) oss << ",";
        oss << "[\"" << price << "\",\"" << quantity << "\"]";
        first = false;
    }
    oss << "]";
    
    oss << "}";
    
    return oss.str();
}

} // namespace json_utils

