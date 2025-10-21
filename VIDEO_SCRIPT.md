# 🎥 Video Demonstration Script - GoQuant Matching Engine

**Target Length:** 15 minutes  
**Format:** Screen recording with voiceover  
**Tools:** OBS Studio, Loom, or Windows Game Bar (Win+G)

---

## 🎬 PRE-RECORDING CHECKLIST

### Before You Start Recording:

- [ ] Close unnecessary applications (Discord, Slack, etc.)
- [ ] Clear browser history/tabs
- [ ] Set screen resolution to 1920x1080 (if possible)
- [ ] Test microphone audio
- [ ] Have water nearby (for clear speaking)
- [ ] Open required applications:
  - Visual Studio Code (or your code editor)
  - PowerShell (2-3 windows)
  - Web browser (for API docs)
  - Postman or REST client

### Files/Windows to Prepare:

1. **PowerShell Window #1** - For starting system
2. **PowerShell Window #2** - For running tests
3. **VS Code** - Open these files in tabs:
   - `matching-engine/src/order_book.hpp`
   - `matching-engine/src/matching_engine.cpp`
   - `SYSTEM_ARCHITECTURE.md`
   - `PERFORMANCE_REPORT.md`
4. **Browser** - Open tabs:
   - `http://localhost:8000/v1/docs` (will open after startup)
   - `https://websocketking.com/` (for WebSocket demo)

---

## 📝 SCRIPT WITH TIMESTAMPS

---

### **[0:00 - 0:45] INTRODUCTION (45 seconds)**

**ON SCREEN:** Show title slide or desktop with project folder open

**SCRIPT:**
```
"Hello! I'm [Your Name], and this is my submission for the 
high-performance cryptocurrency matching engine assignment.

I've built a microservices-based trading system that implements 
REG NMS-inspired price-time priority matching, supporting four 
order types: Market, Limit, IOC, and FOK orders.

The system achieves 2,325 orders per second—more than double the 
required 1,000 orders per second target—with sub-10 millisecond 
latency.

The architecture uses C++ for the performance-critical matching 
engine, Python with FastAPI for the REST API gateway, and Redis 
for message passing between services.

Let me show you how it works."
```

**ACTIONS:**
- Show project folder structure briefly
- Highlight key directories (matching-engine, order-gateway, market-data)

---

### **[0:45 - 3:30] LIVE SYSTEM DEMONSTRATION (2 min 45 sec)**

#### **Part 1: Starting the System (1 min)**

**ON SCREEN:** PowerShell Window #1

**SCRIPT:**
```
"First, let me start all three services using the startup script.
This will launch the Order Gateway on port 8000, the Market Data 
service on port 8001, and the C++ matching engine."
```

**COMMANDS TO RUN:**
```powershell
# Show we're in the right directory
pwd

# Start the system
python start_system.py
```

**WAIT FOR OUTPUT:**
```
[SUCCESS] Redis is already running
[SUCCESS] Order Gateway is ready
[SUCCESS] Market Data Service is ready  
[SUCCESS] C++ Matching Engine started

ALL SERVICES RUNNING!
```

**SCRIPT (WHILE STARTING):**
```
"The startup script automatically:
- Verifies Redis is running
- Starts the Order Gateway with 4 uvicorn workers for parallel 
  request handling
- Starts the Market Data WebSocket service
- Launches the C++ matching engine which connects to Redis and 
  begins listening for orders

All three services are now running and ready to process orders."
```

---

#### **Part 2: Health Check (30 seconds)**

**ON SCREEN:** Browser - show health endpoints

**SCRIPT:**
```
"Let me verify all services are healthy."
```

**NAVIGATE TO:**
1. `http://localhost:8000/health`

**SHOW OUTPUT:**
```json
{
  "status": "healthy",
  "service": "order-gateway",
  "redis": "connected",
  "queue_length": 0
}
```

**SCRIPT:**
```
"The Order Gateway is healthy and connected to Redis with an 
empty queue."
```

2. `http://localhost:8001/health`

**SHOW OUTPUT:**
```json
{
  "status": "healthy",
  "service": "market-data",
  "redis": "connected",
  "active_connections": 0
}
```

**SCRIPT:**
```
"The Market Data service is also healthy with no active WebSocket 
connections yet."
```

---

#### **Part 3: Submitting Orders via REST API (1 min)**

**ON SCREEN:** Browser - Swagger UI at `http://localhost:8000/v1/docs`

**SCRIPT:**
```
"Now let me submit some orders through the REST API. I'm using 
the interactive Swagger documentation."
```

**ACTIONS:**
1. Navigate to `/v1/orders` endpoint
2. Click "Try it out"
3. Enter this order:

```json
{
  "symbol": "BTC-USDT",
  "order_type": "limit",
  "side": "buy",
  "quantity": "1.5",
  "price": "60000.00"
}
```

4. Click "Execute"

**SHOW RESPONSE:**
```json
{
  "order_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "accepted",
  "timestamp": "2025-10-21T12:56:28.123456Z"
}
```

**SCRIPT:**
```
"The order was accepted and assigned a unique UUID. It's now in 
the Redis queue being processed by the matching engine.

Let me submit a matching sell order."
```

**SUBMIT SECOND ORDER:**
```json
{
  "symbol": "BTC-USDT",
  "order_type": "limit",
  "side": "sell",
  "quantity": "1.0",
  "price": "60000.00"
}
```

**SCRIPT:**
```
"This sell order should match against our buy order because 
they're at the same price. The matching engine will execute a 
trade for 1.0 BTC."
```

---

#### **Part 4: WebSocket Live Trade Feed (30 seconds)**

**ON SCREEN:** Browser tab with WebSocketKing.com or similar

**SCRIPT:**
```
"Let me connect to the WebSocket feed to see the trade execution 
in real-time."
```

**ACTIONS:**
1. Go to https://websocketking.com/
2. Connect to: `ws://localhost:8001/ws/market-data`
3. Show connection message:

```json
{
  "type": "connected",
  "message": "Connected to GoQuant Market Data Feed",
  "subscriptions": ["trades", "bbo", "l2_updates"]
}
```

**SCRIPT:**
```
"We're now connected and subscribed to trade events. When I submit 
orders, we'll see the trades broadcast here in real-time.

Watch what happens when I submit another order..."
```

**SUBMIT ORDER** (via Swagger UI in another tab):
```json
{
  "symbol": "BTC-USDT",
  "order_type": "market",
  "side": "buy",
  "quantity": "0.5"
}
```

**SHOW WEBSOCKET RECEIVING:**
```json
{
  "type": "trade",
  "data": {
    "trade_id": "T0002",
    "symbol": "BTC-USDT",
    "price": "60000.00",
    "quantity": "0.5",
    "aggressor_side": "buy",
    "maker_order_id": "...",
    "taker_order_id": "...",
    "timestamp": 1697380800
  }
}
```

**SCRIPT:**
```
"There's the trade! Executed instantly and broadcast to all 
connected WebSocket clients. This demonstrates the complete 
order-to-trade lifecycle."
```

---

### **[3:30 - 10:00] CODE WALKTHROUGH (6 min 30 sec)**

#### **Part 5: Order Book Data Structure (2 min 30 sec)**

**ON SCREEN:** VS Code - open `matching-engine/src/order_book.hpp`

**SCRIPT:**
```
"Now let me walk you through the core code, starting with the 
order book data structure.

The order book is the heart of the matching engine. It maintains 
all active buy and sell orders and must support extremely fast 
operations."
```

**SHOW CODE:** Lines 37-142 (OrderBook class)

**SCRIPT:**
```
"I use a composite data structure that combines three STL 
containers for optimal performance:

First, std::map for price levels."
```

**HIGHLIGHT CODE:**
```cpp
std::map<Price, LimitLevel, std::greater<Price>> bids_;  // Descending
std::map<Price, LimitLevel> asks_;                        // Ascending
```

**SCRIPT:**
```
"The map is a Red-Black tree that keeps prices sorted. 
Bids are sorted in descending order—highest price first—
and asks are sorted ascending—lowest price first.

This gives us O(log M) insertion for new price levels, 
where M is typically less than 100, so that's about 7 
comparisons maximum.

Inside each price level, I use std::list for FIFO time priority."
```

**HIGHLIGHT CODE:**
```cpp
struct LimitLevel {
    std::list<Order> orders;        // FIFO queue
    Quantity total_quantity;         // Cached sum
};
```

**SCRIPT:**
```
"The doubly-linked list maintains time priority—first order 
in gets filled first. This is O(1) for both appending new 
orders and removing filled orders.

Finally, for instant order cancellation, I maintain a hash map."
```

**HIGHLIGHT CODE:**
```cpp
std::unordered_map<OrderID, std::list<Order>::iterator> order_index_;
```

**SCRIPT:**
```
"This maps order IDs to iterators pointing directly into the 
list, giving O(1) cancellation—critical for high-frequency 
trading.

The alternative would be scanning the entire book for each 
cancellation, which would be O(N) and far too slow."
```

**SHOW TABLE:**
```
Operation              | Complexity | Implementation
-----------------------|------------|------------------
Add order (new price)  | O(log M)   | std::map insert
Add order (existing)   | O(1)       | std::list append
Cancel order           | O(1)       | hash lookup + erase
Get best bid/ask       | O(1)       | map.begin()
Match order            | O(1)       | direct access
```

**SCRIPT:**
```
"This design achieves all target complexities and is proven to 
handle thousands of orders per second."
```

---

#### **Part 6: Matching Algorithm (2 min)**

**ON SCREEN:** VS Code - open `matching-engine/src/matching_engine.cpp`

**SCRIPT:**
```
"Now let me show you the matching algorithm that implements 
REG NMS-inspired price-time priority."
```

**SCROLL TO:** `match_limit_order()` function (lines 93-154)

**SCRIPT:**
```
"Here's the limit order matching function. Let me walk through 
the logic step by step."
```

**HIGHLIGHT CODE:** Lines 98-102
```cpp
while (order.remaining_quantity > 0) {
    auto best_price = (counter_side == Side::BUY) 
        ? book.get_best_bid() 
        : book.get_best_ask();
```

**SCRIPT:**
```
"First, we continuously check the best price on the opposite 
side of the book. For a buy order, we look at the best ask—
the lowest sell price."
```

**HIGHLIGHT CODE:** Lines 110-117
```cpp
bool is_marketable = false;
if (order.side == Side::BUY) {
    is_marketable = (order.price >= best_price.value());
} else {
    is_marketable = (order.price <= best_price.value());
}
```

**SCRIPT:**
```
"This is the trade-through prevention mechanism. A buy order 
is only marketable if it's willing to pay at least the asking 
price. If not, we stop matching and rest the order on the book.

This ensures we NEVER skip over better-priced orders—a key 
requirement of REG NMS."
```

**HIGHLIGHT CODE:** Lines 130-134
```cpp
Order& resting_order = orders_at_price->front();
Quantity fill_qty = std::min(order.remaining_quantity, 
                             resting_order.remaining_quantity);
```

**SCRIPT:**
```
"We always match against the FIRST order at each price level—
that's the FIFO time priority. The oldest order at each price 
gets filled first.

The fill quantity is the minimum of what's needed and what's 
available, allowing partial fills."
```

**HIGHLIGHT CODE:** Lines 136-147
```cpp
Trade trade = generate_trade(resting_order, order, fill_qty);
trade_history_.push_back(trade);

order.remaining_quantity -= fill_qty;
resting_order.remaining_quantity -= fill_qty;

if (resting_order.remaining_quantity == 0) {
    book.cancel_order(resting_order.id);
}
```

**SCRIPT:**
```
"We generate a trade event, update both orders' remaining 
quantities, and remove the resting order if it's fully filled.

The loop continues until the incoming order is fully filled 
or no more marketable orders exist."
```

**SCROLL TO:** Lines 151-153
```cpp
if (order.remaining_quantity > 0) {
    book.add_order(order);
}
```

**SCRIPT:**
```
"Finally, if there's remaining quantity, the order rests on 
the book at its limit price, waiting for future matches.

This implements complete limit order behavior as specified 
in the requirements."
```

---

#### **Part 7: Order Type Variants (1 min)**

**SCRIPT:**
```
"The other three order types use similar logic with slight 
variations."
```

**SHOW BRIEFLY:**

**Market Order** (`match_market_order()` - lines 46-91):
```
"Market orders have no price limit, so they match against 
all available liquidity until filled or the book is empty."
```

**IOC Order** (`match_ioc_order()` - lines 156-204):
```
"Immediate-Or-Cancel orders match like limit orders but never 
rest on the book—any unfilled quantity is cancelled."
```

**FOK Order** (`match_fok_order()` - lines 206-259):
```
"Fill-Or-Kill orders pre-check if the entire quantity can be 
filled. If yes, execute all trades atomically. If no, cancel 
the entire order with no partial fills."
```

**HIGHLIGHT:** `can_fill_completely()` function (lines 261-272)
```cpp
Quantity available = book.get_available_liquidity(counter_side, order.price);
return (available >= order.remaining_quantity);
```

**SCRIPT:**
```
"This helper walks the book to calculate total available 
liquidity within the price limit before executing."
```

---

#### **Part 8: Performance Characteristics (1 min)**

**ON SCREEN:** VS Code - open `PERFORMANCE_REPORT.md`

**SCROLL TO:** Section 2.2 (Throughput Breakdown)

**SCRIPT:**
```
"Let me show you the performance results."
```

**HIGHLIGHT TABLE:**
```
Configuration          | Orders/Sec | Notes
-----------------------|------------|------------------
Baseline (1 worker)    | 476        | Single-threaded
Optimized (4 workers)  | 2,325      | 4× improvement
Target                 | 1,000      | ✅ Exceeded by 2.3×
```

**SCRIPT:**
```
"Through optimizations like multi-worker deployment, connection 
pooling, and efficient data structures, the system achieves 
2,325 orders per second—more than double the target."
```

**SCROLL TO:** Section 3.1 (Latency Breakdown)

**HIGHLIGHT TABLE:**
```
Operation              | p50      | p99     | Target
-----------------------|----------|---------|--------
Order Validation       | <1ms     | <2ms    | <10ms ✅
Matching (C++)         | <0.01ms  | <0.05ms | <1ms ✅
End-to-End            | <5ms     | <10ms   | <50ms ✅
```

**SCRIPT:**
```
"The matching engine itself takes only 10 microseconds—
that's 0.01 milliseconds—per order. The bottleneck is 
actually network I/O with Redis, not the matching logic.

This validates our data structure choices."
```

---

### **[10:00 - 13:00] DESIGN DECISIONS (3 min)**

#### **Part 9: Architecture Choices (3 min)**

**ON SCREEN:** VS Code - open `SYSTEM_ARCHITECTURE.md`

**SCRIPT:**
```
"Now let me explain the key design decisions and why I made them."
```

---

**SCROLL TO:** Section 3.1 (Microservices Architecture)

**SHOW DIAGRAM:**
```
Users → Order Gateway (Python) → Redis → Matching Engine (C++) → Redis → Market Data (Python) → Users
```

**SCRIPT:**
```
"I chose a microservices architecture with three services for 
several reasons:

First, separation of concerns. Each service has a single 
responsibility:
- Order Gateway handles API requests and validation
- Matching Engine focuses purely on order matching
- Market Data broadcasts real-time updates

Second, performance isolation. The C++ matching engine runs 
at maximum speed without being slowed down by Python's I/O 
operations.

Third, independent scaling. I can scale the Order Gateway 
horizontally to handle more API requests without touching 
the matching engine."
```

---

**SCROLL TO:** Section 3.2 (Hybrid C++/Python Stack)

**SCRIPT:**
```
"The most important decision: why C++ for the matching engine?

Speed. The matching engine is on the critical path for every 
order. We need sub-microsecond latency.

C++ gives us:
- Manual memory management—no garbage collection pauses
- Compiled optimizations like loop unrolling and SIMD
- Direct control over data structures and memory layout

Python would be 100× slower here due to the Global Interpreter 
Lock and interpreted execution.

But Python is PERFECT for the API services because:
- They're not on the critical path—2ms of network latency 
  dwarfs any Python overhead
- FastAPI lets us build and iterate quickly
- The rich Python ecosystem has great tools for testing

This hybrid approach gives us the best of both worlds."
```

---

**SCROLL TO:** Section 4.1 (Order Book Data Structure)

**SHOW TABLE:**
```
Design             | Add    | Cancel | Get BBO | Why Rejected
-------------------|--------|--------|---------|------------------
Vector + Sort      | O(N²)  | O(N)   | O(1)    | Too slow
Heap Only          | O(logN)| O(N)   | O(1)    | Can't cancel fast
Hash Map Only      | O(1)   | O(1)   | O(N)    | Can't find best price
Our Design (map+   | O(logM)| O(1)   | O(1)    | ✅ Optimal
list+hash)         |        |        |         |
```

**SCRIPT:**
```
"I evaluated multiple data structures and chose this composite 
design because it's the only one that achieves O(1) or 
near-O(1) for ALL required operations.

A simple vector would be easy to implement but O(N²) for 
adding orders—unacceptable at scale.

A heap-only approach can't support O(1) cancellation.

A hash map can't efficiently find the best price.

The composite design using three STL containers achieves 
optimal complexity for every operation. It's more complex 
to implement, but the performance gains are essential for 
a production matching engine."
```

---

**SCROLL TO:** Section 7.4 (Custom Redis Client)

**SCRIPT:**
```
"One final design choice: I built a custom lightweight Redis 
client in C++ instead of using the hiredis library.

Why?

Zero dependencies. The hiredis library would require 
compilation and installation on Windows—a 3-hour setup 
process that could fail.

My custom client is 227 lines of C++ using Windows Sockets 
API. It implements only the four commands we need: BLPOP, 
PUBLISH, PING, and SELECT.

This simplifies deployment and demonstrates understanding 
of the Redis protocol at a low level."
```

---

### **[13:00 - 15:00] WRAP-UP & SUMMARY (2 min)**

#### **Part 10: Final Summary (2 min)**

**ON SCREEN:** Split screen showing running system + documentation

**SCRIPT:**
```
"Let me summarize what I've built and demonstrated:

CORE FUNCTIONALITY:
✅ Price-time priority matching with strict FIFO ordering
✅ Internal trade-through prevention—REG NMS compliant
✅ Four order types: Market, Limit, IOC, and FOK
✅ Real-time BBO calculation and dissemination
✅ Complete REST API for order submission
✅ WebSocket feed for live trade and market data

PERFORMANCE:
✅ 2,325 orders per second—232% of target
✅ Sub-10 millisecond p99 latency
✅ Under 300 MB memory usage
✅ 90%+ test coverage

ARCHITECTURE:
✅ Microservices with proper separation of concerns
✅ C++ for performance-critical matching logic
✅ Python for rapid API development
✅ Redis for lightweight message passing

The system demonstrates:
- Deep understanding of order book mechanics
- Strong software engineering practices
- Ability to make informed architectural trade-offs
- Performance optimization skills
- Clear technical communication

All code is documented with over 3,000 lines of technical 
documentation covering system architecture, data structures, 
matching algorithms, and performance analysis.

The complete source code, documentation, and this demonstration 
are available in my GitHub repository."
```

**SHOW ON SCREEN:**
- GitHub URL: https://github.com/Praneshrajan137/matching-engine
- Key documentation files:
  - SYSTEM_ARCHITECTURE.md
  - PERFORMANCE_REPORT.md
  - SUBMISSION_CHECKLIST.md

**SCRIPT:**
```
"Thank you for watching. I'm excited to discuss the 
implementation in more detail and answer any questions 
you may have."
```

**FADE OUT**

---

## 🎬 POST-RECORDING CHECKLIST

After recording:

- [ ] Watch the video to check:
  - Audio is clear (no background noise)
  - Screen is visible (text readable)
  - No personal information visible
  - All demonstrations worked correctly
- [ ] Edit out long pauses or mistakes (if needed)
- [ ] Add title slide at beginning (optional)
- [ ] Export as MP4 (H.264 codec, 1080p, 30fps)
- [ ] Upload to:
  - [ ] YouTube (unlisted)
  - [ ] Google Drive (shareable link)
  - [ ] Or include in submission ZIP

---

## 💡 PRESENTATION TIPS

### Do's:
✅ Speak clearly and at a moderate pace
✅ Pause briefly between topics
✅ Show confidence—you built something impressive!
✅ Use the mouse to highlight code as you explain
✅ Keep it professional but personable

### Don'ts:
❌ Don't read word-for-word from script
❌ Don't apologize for code choices—explain trade-offs instead
❌ Don't rush—15 minutes is plenty of time
❌ Don't worry about being perfect—authenticity matters

### If You Make a Mistake:
- Pause, take a breath, and continue
- Or stop recording, start from the last section
- Minor stumbles are okay—it shows authenticity

---

## 📊 TIMING BREAKDOWN SUMMARY

```
Section                    | Time    | % of Video
---------------------------|---------|------------
Introduction               | 0:45    | 5%
Live Demo                  | 2:45    | 18%
Code Walkthrough           | 6:30    | 43%
  - Order Book Structure   | 2:30    | 17%
  - Matching Algorithm     | 2:00    | 13%
  - Order Types            | 1:00    | 7%
  - Performance            | 1:00    | 7%
Design Decisions           | 3:00    | 20%
Summary & Wrap-up          | 2:00    | 13%
---------------------------|---------|------------
TOTAL                      | 15:00   | 100%
```

---

## ✅ READY TO RECORD!

You now have:
- ✅ Complete script with talking points
- ✅ Exact commands to run
- ✅ Timestamps for each section
- ✅ Screen layouts and file navigation
- ✅ Presentation tips

**Good luck with your recording! You've built an excellent system—now show it off! 🚀**

---

**Script Version:** 1.0  
**Created:** October 21, 2025  
**Video Length:** ~15 minutes
