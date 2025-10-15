#include <gtest/gtest.h>
#include "order_book.hpp"

// Test 1: Add order to empty book should update BBO
TEST(OrderBookTest, AddOrderToEmptyBook_UpdatesBBO) {
    // Arrange
    OrderBook book;
    Order buy_order("order1", Side::BUY, OrderType::LIMIT, 60000.0, 1.5, 1000);
    
    // Act
    book.add_order(buy_order);
    
    // Assert
    ASSERT_TRUE(book.get_best_bid().has_value());
    EXPECT_EQ(book.get_best_bid().value(), 60000.0);
    EXPECT_EQ(book.get_total_quantity(Side::BUY, 60000.0), 1.5);
    EXPECT_EQ(book.price_level_count(Side::BUY), 1);
}

// Test 2: Adding multiple orders at same price maintains FIFO
TEST(OrderBookTest, AddOrderExistingPriceLevel_MaintainsFIFO) {
    // Arrange
    OrderBook book;
    Order order1("order1", Side::BUY, OrderType::LIMIT, 60000.0, 1.0, 1000);
    Order order2("order2", Side::BUY, OrderType::LIMIT, 60000.0, 2.0, 1001);
    Order order3("order3", Side::BUY, OrderType::LIMIT, 60000.0, 0.5, 1002);
    
    // Act
    book.add_order(order1);
    book.add_order(order2);
    book.add_order(order3);
    
    // Assert - all orders at same price level
    EXPECT_EQ(book.price_level_count(Side::BUY), 1);
    EXPECT_EQ(book.get_total_quantity(Side::BUY, 60000.0), 3.5);  // 1.0 + 2.0 + 0.5
}

// Test 3: Adding orders at different prices creates multiple levels
TEST(OrderBookTest, AddOrderNewPriceLevel_CreatesLevel) {
    // Arrange
    OrderBook book;
    Order order1("order1", Side::BUY, OrderType::LIMIT, 60000.0, 1.0, 1000);
    Order order2("order2", Side::BUY, OrderType::LIMIT, 59999.0, 2.0, 1001);
    Order order3("order3", Side::BUY, OrderType::LIMIT, 59998.0, 0.5, 1002);
    
    // Act
    book.add_order(order1);
    book.add_order(order2);
    book.add_order(order3);
    
    // Assert - three distinct price levels
    EXPECT_EQ(book.price_level_count(Side::BUY), 3);
    EXPECT_EQ(book.get_total_quantity(Side::BUY, 60000.0), 1.0);
    EXPECT_EQ(book.get_total_quantity(Side::BUY, 59999.0), 2.0);
    EXPECT_EQ(book.get_total_quantity(Side::BUY, 59998.0), 0.5);
}

// Test 4: Get best bid returns highest price (FR-1.3)
TEST(OrderBookTest, GetBestBid_ReturnsHighestPrice) {
    // Arrange
    OrderBook book;
    Order order1("order1", Side::BUY, OrderType::LIMIT, 59998.0, 1.0, 1000);
    Order order2("order2", Side::BUY, OrderType::LIMIT, 60000.0, 2.0, 1001);
    Order order3("order3", Side::BUY, OrderType::LIMIT, 59999.0, 0.5, 1002);
    
    // Act
    book.add_order(order1);
    book.add_order(order2);
    book.add_order(order3);
    
    // Assert - best bid is highest price
    ASSERT_TRUE(book.get_best_bid().has_value());
    EXPECT_EQ(book.get_best_bid().value(), 60000.0);
}

// Test 5: Get best ask returns lowest price (FR-1.3)
TEST(OrderBookTest, GetBestAsk_ReturnsLowestPrice) {
    // Arrange
    OrderBook book;
    Order order1("order1", Side::SELL, OrderType::LIMIT, 60002.0, 1.0, 1000);
    Order order2("order2", Side::SELL, OrderType::LIMIT, 60000.0, 2.0, 1001);
    Order order3("order3", Side::SELL, OrderType::LIMIT, 60001.0, 0.5, 1002);
    
    // Act
    book.add_order(order1);
    book.add_order(order2);
    book.add_order(order3);
    
    // Assert - best ask is lowest price
    ASSERT_TRUE(book.get_best_ask().has_value());
    EXPECT_EQ(book.get_best_ask().value(), 60000.0);
}

// Test 6: Cancel order removes from book and updates quantities
TEST(OrderBookTest, CancelOrder_RemovesFromBook) {
    // Arrange
    OrderBook book;
    Order order1("order1", Side::BUY, OrderType::LIMIT, 60000.0, 1.0, 1000);
    Order order2("order2", Side::BUY, OrderType::LIMIT, 60000.0, 2.0, 1001);
    book.add_order(order1);
    book.add_order(order2);
    
    // Act
    bool cancelled = book.cancel_order("order1");
    
    // Assert
    EXPECT_TRUE(cancelled);
    EXPECT_EQ(book.get_total_quantity(Side::BUY, 60000.0), 2.0);  // Only order2 remains
    EXPECT_EQ(book.price_level_count(Side::BUY), 1);  // Price level still exists
}

// Test 7: Cancel non-existent order returns false
TEST(OrderBookTest, CancelOrder_InvalidID_ReturnsFalse) {
    // Arrange
    OrderBook book;
    Order order1("order1", Side::BUY, OrderType::LIMIT, 60000.0, 1.0, 1000);
    book.add_order(order1);
    
    // Act
    bool cancelled = book.cancel_order("non_existent_order");
    
    // Assert
    EXPECT_FALSE(cancelled);
    EXPECT_EQ(book.get_total_quantity(Side::BUY, 60000.0), 1.0);  // Original order unchanged
}

// Test 8: Cancel last order at price level removes the level
TEST(OrderBookTest, CancelLastOrder_RemovesPriceLevel) {
    // Arrange
    OrderBook book;
    Order order1("order1", Side::BUY, OrderType::LIMIT, 60000.0, 1.0, 1000);
    Order order2("order2", Side::BUY, OrderType::LIMIT, 59999.0, 2.0, 1001);
    book.add_order(order1);
    book.add_order(order2);
    
    // Act
    book.cancel_order("order1");
    
    // Assert
    EXPECT_EQ(book.price_level_count(Side::BUY), 1);  // Only one level remains
    EXPECT_EQ(book.get_total_quantity(Side::BUY, 60000.0), 0.0);  // Price level removed
    EXPECT_EQ(book.get_best_bid().value(), 59999.0);  // Best bid updated
}

// Test 9: Get total quantity for non-existent price returns 0
TEST(OrderBookTest, GetTotalQuantity_NonExistentPrice_ReturnsZero) {
    // Arrange
    OrderBook book;
    Order order1("order1", Side::BUY, OrderType::LIMIT, 60000.0, 1.0, 1000);
    book.add_order(order1);
    
    // Act & Assert
    EXPECT_EQ(book.get_total_quantity(Side::BUY, 99999.0), 0.0);
    EXPECT_EQ(book.get_total_quantity(Side::SELL, 60000.0), 0.0);
}

// Test 10: Empty book returns nullopt for BBO
TEST(OrderBookTest, EmptyBook_ReturnsNulloptForBBO) {
    // Arrange
    OrderBook book;
    
    // Act & Assert
    EXPECT_FALSE(book.get_best_bid().has_value());
    EXPECT_FALSE(book.get_best_ask().has_value());
    EXPECT_EQ(book.price_level_count(Side::BUY), 0);
    EXPECT_EQ(book.price_level_count(Side::SELL), 0);
}

