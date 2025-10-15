#include "order_book.hpp"

OrderBook::OrderBook() {
    // Constructor - currently empty
    // Data structures initialized via member initialization
}

void OrderBook::add_order(const Order& order) {
    // TODO: Implement via TDD
    // test-expert will write failing tests first
    // then matching-engine-expert will implement
}

bool OrderBook::cancel_order(const OrderID& order_id) {
    // TODO: Implement via TDD
    return false;
}

std::optional<Price> OrderBook::get_best_bid() const {
    // TODO: Implement via TDD
    return std::nullopt;
}

std::optional<Price> OrderBook::get_best_ask() const {
    // TODO: Implement via TDD
    return std::nullopt;
}

Quantity OrderBook::get_total_quantity(Side side, Price price) const {
    // TODO: Implement via TDD
    (void)side;   // Suppress unused parameter warning
    (void)price;
    return 0.0;
}

size_t OrderBook::price_level_count(Side side) const {
    // TODO: Implement via TDD
    (void)side;
    return 0;
}

