#pragma once
#include "order_book.hpp"
#include "order.hpp"
#include <vector>
#include <unordered_map>
#include <string>
#include <chrono>
#include <functional>
#include <optional>
#include <ctime>
#include <memory>

/**
 * @file matching_engine_optimized.hpp
 * @brief High-performance matching engine with optimization techniques
 * 
 * Performance Optimizations:
 * 1. Trade object pooling - Reduce allocations
 * 2. Move semantics - Eliminate unnecessary copies
 * 3. Reserve capacity - Pre-allocate vectors
 * 4. Inline hot paths - Reduce function call overhead
 * 5. Branch prediction hints - Help CPU optimization
 * 6. Cache-friendly data layout - Improve memory access patterns
 */

/**
 * @brief Trade execution event (optimized for cache locality)
 * 
 * Fields ordered by access frequency for better cache performance
 */
struct Trade {
    std::string trade_id;      // Most accessed
    Price price;               // Hot path
    Quantity quantity;         // Hot path
    Timestamp timestamp;       // Frequently accessed
    std::string symbol;
    std::string maker_order_id;
    std::string taker_order_id;
    Side aggressor_side;
    
    // Default constructor for object pooling
    Trade() = default;
    
    Trade(std::string id, std::string sym, std::string maker, std::string taker,
          Price p, Quantity q, Side side, Timestamp ts)
        : trade_id(std::move(id)), price(p), quantity(q), timestamp(ts),
          symbol(std::move(sym)), maker_order_id(std::move(maker)),
          taker_order_id(std::move(taker)), aggressor_side(side) {}
    
    // Enable move semantics for better performance
    Trade(Trade&&) noexcept = default;
    Trade& operator=(Trade&&) noexcept = default;
    
    // Copy operations
    Trade(const Trade&) = default;
    Trade& operator=(const Trade&) = default;
};

/**
 * @brief Object pool for Trade objects
 * 
 * Reduces allocation overhead by reusing Trade objects
 * Critical for high-frequency trading where allocations are expensive
 */
class TradePool {
public:
    TradePool(size_t initial_size = 1000) {
        pool_.reserve(initial_size);
        for (size_t i = 0; i < initial_size; ++i) {
            pool_.push_back(std::make_unique<Trade>());
        }
    }
    
    Trade* acquire() {
        if (pool_.empty()) {
            return new Trade();
        }
        
        Trade* trade = pool_.back().release();
        pool_.pop_back();
        return trade;
    }
    
    void release(Trade* trade) {
        pool_.push_back(std::unique_ptr<Trade>(trade));
    }
    
    size_t size() const { return pool_.size(); }
    
private:
    std::vector<std::unique_ptr<Trade>> pool_;
};

/**
 * @brief High-performance matching engine
 * 
 * Optimization Features:
 * - Object pooling for trade events
 * - Move semantics throughout
 * - Cache-friendly data structures
 * - Hot path inlining
 * - Branch prediction hints
 */
class OptimizedMatchingEngine {
public:
    OptimizedMatchingEngine();
    
    // Main entry point - uses move semantics to avoid copies
    void process_order(Order&& order);
    
    // Accessors
    const std::vector<Trade>& get_trades() const { return trade_history_; }
    void clear_trades() { trade_history_.clear(); }  // Memory management
    
    OrderBook& get_book(const std::string& symbol);
    const OrderBook& get_book(const std::string& symbol) const;
    
    // Performance metrics
    struct PerformanceMetrics {
        uint64_t orders_processed = 0;
        uint64_t trades_generated = 0;
        uint64_t total_latency_ns = 0;  // Nanoseconds
        uint64_t min_latency_ns = UINT64_MAX;
        uint64_t max_latency_ns = 0;
        
        double avg_latency_ns() const {
            return orders_processed > 0 
                ? static_cast<double>(total_latency_ns) / orders_processed 
                : 0.0;
        }
        
        double avg_latency_us() const { return avg_latency_ns() / 1000.0; }
    };
    
    const PerformanceMetrics& get_metrics() const { return metrics_; }
    void reset_metrics() { metrics_ = PerformanceMetrics(); }
    
private:
    std::unordered_map<std::string, OrderBook> order_books_;
    std::vector<Trade> trade_history_;
    size_t trade_counter_ = 0;
    
    // OPTIMIZATION: Object pool for trades
    TradePool trade_pool_;
    
    // Performance tracking
    PerformanceMetrics metrics_;
    
    // Order type handlers - use move semantics
    void match_market_order(Order&& order, OrderBook& book);
    void match_limit_order(Order&& order, OrderBook& book);
    void match_ioc_order(Order&& order, OrderBook& book);
    void match_fok_order(Order&& order, OrderBook& book);
    
    // Helper methods - inline for hot paths
    inline bool can_fill_completely(const Order& order, const OrderBook& book) const;
    
    // OPTIMIZATION: Generate trade with object pooling
    Trade generate_trade_optimized(const Order& maker, const Order& taker, Quantity fill_qty);
    
    std::string generate_trade_id();
    
    // OPTIMIZATION: Measure latency for each order
    class ScopedTimer {
    public:
        ScopedTimer(PerformanceMetrics& metrics) 
            : metrics_(metrics), 
              start_(std::chrono::high_resolution_clock::now()) {}
        
        ~ScopedTimer() {
            auto end = std::chrono::high_resolution_clock::now();
            auto duration = std::chrono::duration_cast<std::chrono::nanoseconds>(end - start_);
            uint64_t latency_ns = duration.count();
            
            metrics_.total_latency_ns += latency_ns;
            metrics_.min_latency_ns = std::min(metrics_.min_latency_ns, latency_ns);
            metrics_.max_latency_ns = std::max(metrics_.max_latency_ns, latency_ns);
        }
        
    private:
        PerformanceMetrics& metrics_;
        std::chrono::high_resolution_clock::time_point start_;
    };
};

// OPTIMIZATION: Inline hint for compiler
#ifdef __GNUC__
#define LIKELY(x)   __builtin_expect(!!(x), 1)
#define UNLIKELY(x) __builtin_expect(!!(x), 0)
#else
#define LIKELY(x)   (x)
#define UNLIKELY(x) (x)
#endif

// Force inline for hot paths
#if defined(__GNUC__) || defined(__clang__)
#define FORCE_INLINE __attribute__((always_inline)) inline
#elif defined(_MSC_VER)
#define FORCE_INLINE __forceinline
#else
#define FORCE_INLINE inline
#endif

