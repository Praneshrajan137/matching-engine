#include <gtest/gtest.h>
#include "matching_engine.hpp"

// Test 1: Market buy fills single ask
TEST(MatchingEngineTest, MarketBuy_FillsSingleAsk) {
    // Arrange
    MatchingEngine engine;
    Order ask("ask1", Side::SELL, OrderType::LIMIT, 60000.0, 1.0, 1000);
    engine.process_order(ask);  // Add liquidity
    
    Order market_buy("buy1", Side::BUY, OrderType::MARKET, 0, 1.0, 1001);
    
    // Act
    engine.process_order(market_buy);
    
    // Assert - FIXED: Use EXPECT_DOUBLE_EQ for floats
    ASSERT_EQ(engine.get_trades().size(), 1);
    const auto& trade = engine.get_trades()[0];
    EXPECT_DOUBLE_EQ(trade.price, 60000.0);
    EXPECT_DOUBLE_EQ(trade.quantity, 1.0);
    EXPECT_EQ(trade.maker_order_id, "ask1");
    EXPECT_EQ(trade.taker_order_id, "buy1");
}

// Test 2: Market order crosses multiple price levels
TEST(MatchingEngineTest, MarketBuy_CrossesMultipleLevels) {
    // Arrange
    MatchingEngine engine;
    engine.process_order(Order("ask1", Side::SELL, OrderType::LIMIT, 60000.0, 0.5, 1000));
    engine.process_order(Order("ask2", Side::SELL, OrderType::LIMIT, 60001.0, 1.0, 1001));
    
    Order market_buy("buy1", Side::BUY, OrderType::MARKET, 0, 1.2, 1002);
    
    // Act
    engine.process_order(market_buy);
    
    // Assert
    ASSERT_EQ(engine.get_trades().size(), 2);
    EXPECT_DOUBLE_EQ(engine.get_trades()[0].price, 60000.0);  // Best price first
    EXPECT_DOUBLE_EQ(engine.get_trades()[0].quantity, 0.5);
    EXPECT_DOUBLE_EQ(engine.get_trades()[1].price, 60001.0);  // Worse price second
    EXPECT_DOUBLE_EQ(engine.get_trades()[1].quantity, 0.7);
}

// Test 3: Market order on empty book generates no trades (FIXED: Edge case)
TEST(MatchingEngineTest, MarketOrder_EmptyBook_NoTrades) {
    // Arrange
    MatchingEngine engine;
    Order market_buy("buy1", Side::BUY, OrderType::MARKET, 0, 1.0, 1000);
    
    // Act
    engine.process_order(market_buy);
    
    // Assert
    EXPECT_EQ(engine.get_trades().size(), 0);
}

// Test 4: Market order never rests on book
TEST(MatchingEngineTest, MarketOrder_NeverRests) {
    // Arrange
    MatchingEngine engine;
    engine.process_order(Order("ask1", Side::SELL, OrderType::LIMIT, 60000.0, 0.5, 1000));
    
    Order market_buy("buy1", Side::BUY, OrderType::MARKET, 0, 1.0, 1001);
    
    // Act
    engine.process_order(market_buy);
    
    // Assert - book should have no buy orders
    auto& book = engine.get_book("BTC-USDT");
    EXPECT_EQ(book.price_level_count(Side::BUY), 0);
}

// Test 5: Market sell fills bid
TEST(MatchingEngineTest, MarketSell_FillsBid) {
    // Arrange
    MatchingEngine engine;
    engine.process_order(Order("bid1", Side::BUY, OrderType::LIMIT, 60000.0, 1.0, 1000));
    
    Order market_sell("sell1", Side::SELL, OrderType::MARKET, 0, 1.0, 1001);
    
    // Act
    engine.process_order(market_sell);
    
    // Assert
    ASSERT_EQ(engine.get_trades().size(), 1);
    EXPECT_DOUBLE_EQ(engine.get_trades()[0].price, 60000.0);
    EXPECT_EQ(engine.get_trades()[0].aggressor_side, Side::SELL);
}

