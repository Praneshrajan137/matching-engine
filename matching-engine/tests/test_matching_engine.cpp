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

// ========== LIMIT ORDER TESTS (FR-2.2) ==========

// Test 6: Marketable limit buy matches immediately
TEST(MatchingEngineTest, LimitBuy_Marketable_Matches) {
    // Arrange
    MatchingEngine engine;
    engine.process_order(Order("ask1", Side::SELL, OrderType::LIMIT, 60000.0, 1.0, 1000));
    
    // Limit buy at 60000 is marketable (crosses ask at 60000)
    Order limit_buy("buy1", Side::BUY, OrderType::LIMIT, 60000.0, 1.0, 1001);
    
    // Act
    engine.process_order(limit_buy);
    
    // Assert
    ASSERT_EQ(engine.get_trades().size(), 1);
    EXPECT_DOUBLE_EQ(engine.get_trades()[0].price, 60000.0);
    EXPECT_DOUBLE_EQ(engine.get_trades()[0].quantity, 1.0);
}

// Test 7: Non-marketable limit order rests on book
TEST(MatchingEngineTest, LimitBuy_NonMarketable_Rests) {
    // Arrange
    MatchingEngine engine;
    engine.process_order(Order("ask1", Side::SELL, OrderType::LIMIT, 60001.0, 1.0, 1000));
    
    // Limit buy at 60000 is not marketable (below best ask)
    Order limit_buy("buy1", Side::BUY, OrderType::LIMIT, 60000.0, 1.0, 1001);
    
    // Act
    engine.process_order(limit_buy);
    
    // Assert - no trades, order rests on book
    EXPECT_EQ(engine.get_trades().size(), 0);
    auto& book = engine.get_book("BTC-USDT");
    EXPECT_EQ(book.price_level_count(Side::BUY), 1);
    EXPECT_DOUBLE_EQ(book.get_best_bid().value(), 60000.0);
}

// Test 8: Limit order partial fill, rest on book
TEST(MatchingEngineTest, LimitOrder_PartialFill_RestRests) {
    // Arrange
    MatchingEngine engine;
    engine.process_order(Order("ask1", Side::SELL, OrderType::LIMIT, 60000.0, 0.5, 1000));
    
    // Limit buy for 1.0 can only fill 0.5
    Order limit_buy("buy1", Side::BUY, OrderType::LIMIT, 60000.0, 1.0, 1001);
    
    // Act
    engine.process_order(limit_buy);
    
    // Assert - one trade, remainder rests
    ASSERT_EQ(engine.get_trades().size(), 1);
    EXPECT_DOUBLE_EQ(engine.get_trades()[0].quantity, 0.5);
    
    auto& book = engine.get_book("BTC-USDT");
    EXPECT_EQ(book.price_level_count(Side::BUY), 1);
    EXPECT_DOUBLE_EQ(book.get_total_quantity(Side::BUY, 60000.0), 0.5);  // 0.5 remaining
}

// Test 9: Limit buy crosses multiple price levels
TEST(MatchingEngineTest, LimitBuy_CrossesMultipleLevels) {
    // Arrange
    MatchingEngine engine;
    engine.process_order(Order("ask1", Side::SELL, OrderType::LIMIT, 59999.0, 0.5, 1000));
    engine.process_order(Order("ask2", Side::SELL, OrderType::LIMIT, 60000.0, 0.5, 1001));
    
    // Limit buy at 60000 matches both levels
    Order limit_buy("buy1", Side::BUY, OrderType::LIMIT, 60000.0, 1.0, 1002);
    
    // Act
    engine.process_order(limit_buy);
    
    // Assert - matches best prices first
    ASSERT_EQ(engine.get_trades().size(), 2);
    EXPECT_DOUBLE_EQ(engine.get_trades()[0].price, 59999.0);  // Best price first
    EXPECT_DOUBLE_EQ(engine.get_trades()[1].price, 60000.0);
}

// Test 10: Limit sell (marketable)
TEST(MatchingEngineTest, LimitSell_Marketable_Matches) {
    // Arrange
    MatchingEngine engine;
    engine.process_order(Order("bid1", Side::BUY, OrderType::LIMIT, 60000.0, 1.0, 1000));
    
    // Limit sell at 60000 is marketable
    Order limit_sell("sell1", Side::SELL, OrderType::LIMIT, 60000.0, 1.0, 1001);
    
    // Act
    engine.process_order(limit_sell);
    
    // Assert
    ASSERT_EQ(engine.get_trades().size(), 1);
    EXPECT_DOUBLE_EQ(engine.get_trades()[0].price, 60000.0);
}

// Test 11: Limit sell (non-marketable, rests)
TEST(MatchingEngineTest, LimitSell_NonMarketable_Rests) {
    // Arrange
    MatchingEngine engine;
    engine.process_order(Order("bid1", Side::BUY, OrderType::LIMIT, 59999.0, 1.0, 1000));
    
    // Limit sell at 60000 is not marketable (above best bid)
    Order limit_sell("sell1", Side::SELL, OrderType::LIMIT, 60000.0, 1.0, 1001);
    
    // Act
    engine.process_order(limit_sell);
    
    // Assert - no trades, rests on book
    EXPECT_EQ(engine.get_trades().size(), 0);
    auto& book = engine.get_book("BTC-USDT");
    EXPECT_EQ(book.price_level_count(Side::SELL), 1);
    EXPECT_DOUBLE_EQ(book.get_best_ask().value(), 60000.0);
}

// Test 12: Limit order gets price improvement
TEST(MatchingEngineTest, LimitOrder_PriceImprovement) {
    // Arrange
    MatchingEngine engine;
    engine.process_order(Order("ask1", Side::SELL, OrderType::LIMIT, 59990.0, 1.0, 1000));
    
    // Limit buy willing to pay up to 60000, gets filled at 59990
    Order limit_buy("buy1", Side::BUY, OrderType::LIMIT, 60000.0, 1.0, 1001);
    
    // Act
    engine.process_order(limit_buy);
    
    // Assert - filled at maker price (better than limit)
    ASSERT_EQ(engine.get_trades().size(), 1);
    EXPECT_DOUBLE_EQ(engine.get_trades()[0].price, 59990.0);  // Maker price, not taker's limit
}

// ========== IOC ORDER TESTS (FR-2.3) ==========

// Test 13: IOC order fills completely
TEST(MatchingEngineTest, IOC_FillsCompletely) {
    // Arrange
    MatchingEngine engine;
    engine.process_order(Order("ask1", Side::SELL, OrderType::LIMIT, 60000.0, 1.0, 1000));
    
    Order ioc_buy("buy1", Side::BUY, OrderType::IOC, 60000.0, 1.0, 1001);
    
    // Act
    engine.process_order(ioc_buy);
    
    // Assert
    ASSERT_EQ(engine.get_trades().size(), 1);
    EXPECT_DOUBLE_EQ(engine.get_trades()[0].quantity, 1.0);
}

// Test 14: IOC order partial fill, remainder cancelled
TEST(MatchingEngineTest, IOC_PartialFill_RemainderCancelled) {
    // Arrange
    MatchingEngine engine;
    engine.process_order(Order("ask1", Side::SELL, OrderType::LIMIT, 60000.0, 0.5, 1000));
    
    Order ioc_buy("buy1", Side::BUY, OrderType::IOC, 60000.0, 1.0, 1001);
    
    // Act
    engine.process_order(ioc_buy);
    
    // Assert - partial fill, remainder cancelled (not rested)
    ASSERT_EQ(engine.get_trades().size(), 1);
    EXPECT_DOUBLE_EQ(engine.get_trades()[0].quantity, 0.5);
    
    auto& book = engine.get_book("BTC-USDT");
    EXPECT_EQ(book.price_level_count(Side::BUY), 0);  // Not rested
}

// Test 15: IOC order no match, cancelled
TEST(MatchingEngineTest, IOC_NoMatch_Cancelled) {
    // Arrange
    MatchingEngine engine;
    engine.process_order(Order("ask1", Side::SELL, OrderType::LIMIT, 60001.0, 1.0, 1000));
    
    Order ioc_buy("buy1", Side::BUY, OrderType::IOC, 60000.0, 1.0, 1001);
    
    // Act
    engine.process_order(ioc_buy);
    
    // Assert - no trades, order cancelled
    EXPECT_EQ(engine.get_trades().size(), 0);
    auto& book = engine.get_book("BTC-USDT");
    EXPECT_EQ(book.price_level_count(Side::BUY), 0);
}

// Test 16: IOC crosses multiple levels
TEST(MatchingEngineTest, IOC_CrossesMultipleLevels) {
    // Arrange
    MatchingEngine engine;
    engine.process_order(Order("ask1", Side::SELL, OrderType::LIMIT, 60000.0, 0.3, 1000));
    engine.process_order(Order("ask2", Side::SELL, OrderType::LIMIT, 60001.0, 0.5, 1001));
    
    Order ioc_buy("buy1", Side::BUY, OrderType::IOC, 60001.0, 1.0, 1002);
    
    // Act
    engine.process_order(ioc_buy);
    
    // Assert - fills 0.8, cancels 0.2
    ASSERT_EQ(engine.get_trades().size(), 2);
    EXPECT_DOUBLE_EQ(engine.get_trades()[0].quantity, 0.3);
    EXPECT_DOUBLE_EQ(engine.get_trades()[1].quantity, 0.5);
}

// ========== FOK ORDER TESTS (FR-2.4) ==========

// Test 17: FOK fills completely
TEST(MatchingEngineTest, FOK_FillsCompletely) {
    // Arrange
    MatchingEngine engine;
    engine.process_order(Order("ask1", Side::SELL, OrderType::LIMIT, 60000.0, 1.0, 1000));
    
    Order fok_buy("buy1", Side::BUY, OrderType::FOK, 60000.0, 1.0, 1001);
    
    // Act
    engine.process_order(fok_buy);
    
    // Assert - fills completely
    ASSERT_EQ(engine.get_trades().size(), 1);
    EXPECT_DOUBLE_EQ(engine.get_trades()[0].quantity, 1.0);
}

// Test 18: FOK cannot fill completely, cancelled (no partial fills)
TEST(MatchingEngineTest, FOK_CannotFillCompletely_Cancelled) {
    // Arrange
    MatchingEngine engine;
    engine.process_order(Order("ask1", Side::SELL, OrderType::LIMIT, 60000.0, 0.5, 1000));
    
    Order fok_buy("buy1", Side::BUY, OrderType::FOK, 60000.0, 1.0, 1001);
    
    // Act
    engine.process_order(fok_buy);
    
    // Assert - no trades at all (all-or-nothing)
    EXPECT_EQ(engine.get_trades().size(), 0);
    
    // Resting order still on book (not touched)
    auto& book = engine.get_book("BTC-USDT");
    EXPECT_DOUBLE_EQ(book.get_total_quantity(Side::SELL, 60000.0), 0.5);
}

// Test 19: FOK fills across multiple levels
TEST(MatchingEngineTest, FOK_FillsAcrossMultipleLevels) {
    // Arrange
    MatchingEngine engine;
    engine.process_order(Order("ask1", Side::SELL, OrderType::LIMIT, 60000.0, 0.5, 1000));
    engine.process_order(Order("ask2", Side::SELL, OrderType::LIMIT, 60001.0, 0.5, 1001));
    
    Order fok_buy("buy1", Side::BUY, OrderType::FOK, 60001.0, 1.0, 1002);
    
    // Act
    engine.process_order(fok_buy);
    
    // Assert - fills all (can fill completely)
    ASSERT_EQ(engine.get_trades().size(), 2);
    EXPECT_DOUBLE_EQ(engine.get_trades()[0].quantity, 0.5);
    EXPECT_DOUBLE_EQ(engine.get_trades()[1].quantity, 0.5);
}

// Test 20: FOK price limit prevents fill, cancelled
TEST(MatchingEngineTest, FOK_PriceLimitPrevents_Cancelled) {
    // Arrange
    MatchingEngine engine;
    engine.process_order(Order("ask1", Side::SELL, OrderType::LIMIT, 60000.0, 0.3, 1000));
    engine.process_order(Order("ask2", Side::SELL, OrderType::LIMIT, 60001.0, 0.8, 1001));
    
    // FOK willing to pay up to 60000, but needs 1.0 total (only 0.3 available at that price)
    Order fok_buy("buy1", Side::BUY, OrderType::FOK, 60000.0, 1.0, 1002);
    
    // Act
    engine.process_order(fok_buy);
    
    // Assert - no trades (cannot fill completely at limit price)
    EXPECT_EQ(engine.get_trades().size(), 0);
}

