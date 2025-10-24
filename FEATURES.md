# Features & Technical Specifications

## 1. Core Matching Engine

### Price-Time Priority Matching

**Implementation:**
- Strict price-time priority matching algorithm (REG NMS-inspired)
- Internal trade-through prevention (no order skipping at better prices)
- Real-time Best Bid and Offer (BBO) calculation
- Instantaneous BBO updates on order add/cancel/match

**Guarantees:**
- Orders at better prices always execute first
- Orders at same price execute in FIFO order (time priority)
- BBO calculation completes in <1ms

**Example:**
```
Given order book with asks at [60000, 60001, 60002]
When: New buy order at 60001
Then: System fills at 60000 first (best price priority)
```

---

### Order Types

#### 1. Market Order

**Behavior:**
- Executes immediately at best available price(s)
- Never rests on order book
- Continues filling at progressively worse prices until quantity satisfied

**Example:**
```
Order book: Asks [60000: 0.5 BTC, 60001: 1.0 BTC]
Market buy: 1.2 BTC
Result:
  - Fill 0.5 BTC @ 60000
  - Fill 0.7 BTC @ 60001
  - 2 trade events generated
```

#### 2. Limit Order

**Behavior:**
- Executes at specified price or better
- Rests on book if not immediately marketable
- Partial fills allowed

**Example:**
```
Order book: Best ask = 60000
Limit buy: 1.0 BTC @ 59900
Result:
  - Order rests on bid side at 59900
  - BBO updates: best_bid = 59900
```

#### 3. Immediate-Or-Cancel (IOC)

**Behavior:**
- Executes immediately fillable portion
- Cancels unfilled remainder instantly
- Never rests on book

**Example:**
```
Order book: Asks [60000: 0.3 BTC]
IOC buy: 1.0 BTC @ 60000
Result:
  - Fill 0.3 BTC @ 60000
  - Cancel 0.7 BTC
```

#### 4. Fill-Or-Kill (FOK)

**Behavior:**
- Pre-checks if entire order can be filled immediately
- If yes: executes all trades atomically
- If no: cancels entire order (no partial fills)
- Never rests on book

**Example:**
```
Order book: Asks [60000: 0.5 BTC, 60001: 0.3 BTC]
FOK buy: 1.0 BTC @ 60001
Result:
  - Available: 0.8 BTC < 1.0 BTC required
  - Cancel entire order (no trades)
```

---

### FR-3: API Endpoints

#### FR-3.1: Order Submission API (REST)

- [ ] Endpoint: `POST /v1/orders`
- [ ] Protocol: HTTP/REST
- [ ] Authentication: None (assignment scope)
- [ ] Rate Limiting: None (assignment scope)

**Request Schema:**
```json
{
  "symbol": "string (e.g., 'BTC-USDT')",
  "order_type": "enum ['market', 'limit', 'ioc', 'fok']",
  "side": "enum ['buy', 'sell']",
  "quantity": "decimal string (e.g., '1.5')",
  "price": "decimal string (required for 'limit', ignored otherwise)"
}
```

**Success Response (201 Created):**
```json
{
  "order_id": "uuid-v4-string",
  "status": "accepted",
  "timestamp": "ISO8601-string"
}
```

**Error Responses:**

- `400 Bad Request`: Invalid JSON, missing fields, invalid order_type
- `500 Internal Server Error`: Unexpected server failure

#### FR-3.2: Market Data API (WebSocket)

- [ ] Protocol: WebSocket
- [ ] Subscription: Client connects, receives all updates
- [ ] Data Types: L2 order book depth (top 10 levels)

**L2 Order Book Update Payload:**
```json
{
  "timestamp": "2025-10-14T10:00:00.123456Z",
  "symbol": "BTC-USDT",
  "bids": [
    ["60000.00", "1.5"],
    ["59999.50", "2.0"]
  ],
  "asks": [
    ["60001.00", "0.8"],
    ["60002.00", "1.2"]
  ]
}
```

#### FR-3.3: Trade Execution Feed (WebSocket)

- [ ] Real-time broadcast of every trade
- [ ] Includes maker/taker order IDs

**Trade Execution Report Payload:**
```json
{
  "timestamp": "2025-10-14T10:00:01.543210Z",
  "symbol": "BTC-USDT",
  "trade_id": "uuid-v4-string",
  "price": "60000.00",
  "quantity": "0.5",
  "aggressor_side": "sell",
  "maker_order_id": "uuid-maker",
  "taker_order_id": "uuid-taker"
}
```

---

## 2. Performance Characteristics

### Achieved Performance

- **Throughput**: 2,325 orders/second sustained
- **Latency**: <10ms (p99), <5ms (p50)
- **BBO Update**: <1ms calculation and broadcast
- **Memory**: <300MB for 10K active orders
- **Matching Speed**: <10μs per order (C++ core)

### Technology Stack

- **Matching Engine**: C++17
  - Chosen for sub-microsecond matching latency
  - Manual memory management (no GC pauses)
  - Compiled optimizations
  
- **Order Gateway**: Python 3.11+ with FastAPI
  - 5000+ requests/sec capability
  - Not on critical path (order validation)
  
- **Market Data Service**: Python 3.11+ with WebSockets
  - Async I/O for concurrent client connections
  - Real-time broadcast capability
  
- **Message Broker**: Redis
  - Lightweight IPC for single-machine deployment
  - 100K+ ops/sec throughput

### Testing & Quality

- **Unit Test Coverage**: 90%+ for matching engine core logic
- **Integration Tests**: End-to-end order submission → matching → broadcast flow
- **Test Frameworks**: pytest (Python), Google Test (C++)
- **Total Tests**: 39+ unit and integration tests

---

## 3. Current Scope

### Implemented Features

✅ Price-time priority matching  
✅ 4 order types (Market, Limit, IOC, FOK)  
✅ Real-time BBO calculation  
✅ WebSocket market data feeds  
✅ RESTful order submission API  
✅ Trade execution reporting  
✅ L2 order book depth (top 10 levels)  
✅ Comprehensive test coverage  
✅ Detailed technical documentation  

### Future Extensions

⏳ User authentication & authorization  
⏳ Account & risk management  
⏳ Database persistence (order book snapshots)  
⏳ Multi-symbol support  
⏳ Advanced order types (Stop-Loss, Iceberg, etc.)  
⏳ Monitoring & alerting infrastructure  
⏳ Circuit breakers & trading halts  

---

## 4. Data Structures

### Order Book Implementation

**Design Goal:** Optimal time complexity for all operations

| Operation | Complexity | Data Structure |
|-----------|------------|----------------|
| Add order (new price) | O(log M) | `std::map` (Red-Black tree) |
| Add order (existing price) | O(1) | `std::list` (doubly-linked) |
| Cancel order | O(1) | `std::unordered_map` + iterator |
| Match best order | O(1) | Direct tree root access |
| Get BBO | O(1) | Cached pointers |

**Where:**
- M = number of distinct price levels (typically <100)
- N = total number of orders

**Rationale:**
- `std::map` maintains sorted price levels (bids descending, asks ascending)
- `std::list` within each level provides FIFO time priority
- `std::unordered_map` enables O(1) order cancellation

See [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md) Section 4 for complete analysis.

---

## 5. Development & Roadmap

### v1.0.0 (Current)

- Core matching engine with 4 order types
- REST API and WebSocket feeds
- 2,300+ orders/second throughput
- Comprehensive documentation

### v1.1.0 (Planned)

- Order book persistence (Redis snapshots)
- Multi-symbol support (5+ trading pairs)
- Enhanced market data (full L2 depth)
- Performance optimization (Redis pipelining)

### v2.0.0 (Future)

- Authentication & authorization
- Risk management layer
- Advanced order types
- Distributed architecture
- Production monitoring & alerting

---

For implementation details, see:
- [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md) - Complete system design
- [DECISIONS.md](DECISIONS.md) - Architecture decision records
- [PERFORMANCE_REPORT.md](PERFORMANCE_REPORT.md) - Detailed benchmarks

