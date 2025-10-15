# SPECIFICATION.md

## 1. FUNCTIONAL REQUIREMENTS (MUST-HAVES)

### FR-1: Core Matching Logic

- [ ] FR-1.1 Implement strict price-time priority matching algorithm
- [ ] FR-1.2 Prevent internal trade-throughs (no order skipping at better prices)
- [ ] FR-1.3 Maintain real-time Best Bid and Offer (BBO) calculation
- [ ] FR-1.4 Update BBO instantaneously on order add/cancel/match

**Acceptance Criteria FR-1:**

- Given orders at prices [60000, 60001, 60002] and new buy order at 60001, system MUST fill at 60000 first
- Given two orders at same price (e.g., 60000), FIFO order (earliest timestamp) MUST execute first
- BBO calculation MUST complete within 1ms of order book state change

---

### FR-2: Order Type Support

#### FR-2.1: Market Order

- [ ] Executes immediately at best available price(s)
- [ ] Never rests on order book
- [ ] Continues filling at progressively worse prices until quantity satisfied

**Test Case:**
```python
# Given: Order book with asks [60000:0.5, 60001:1.0]
# When: Market buy order for 1.2 BTC submitted
# Then: 
#   - Fill 0.5 BTC @ 60000
#   - Fill 0.7 BTC @ 60001
#   - Generate 2 trade execution events
#   - Market order does NOT appear in order book
```

#### FR-2.2: Limit Order

- [ ] Executes at specified price or better
- [ ] Rests on book if not immediately marketable
- [ ] Partial fills allowed

**Test Case:**
```python
# Given: Order book with best ask = 60000
# When: Limit buy order at 59900 for 1.0 BTC submitted
# Then:
#   - Order does NOT execute immediately
#   - Order appears in bids at 59900 with quantity 1.0
#   - BBO updates: best_bid = 59900
```

#### FR-2.3: Immediate-Or-Cancel (IOC)

- [ ] Executes immediately fillable portion
- [ ] Cancels unfilled remainder instantly
- [ ] Never rests on book

**Test Case:**
```python
# Given: Order book with asks [60000:0.3]
# When: IOC buy order at 60000 for 1.0 BTC submitted
# Then:
#   - Fill 0.3 BTC @ 60000
#   - Cancel 0.7 BTC
#   - Generate 1 trade + 1 cancel event
```

#### FR-2.4: Fill-Or-Kill (FOK)

- [ ] Checks if entire order can be filled immediately
- [ ] If yes: executes all trades atomically
- [ ] If no: cancels entire order without any partial fills
- [ ] Never rests on book

**Test Case:**
```python
# Given: Order book with asks [60000:0.5, 60001:0.3]
# When: FOK buy order at 60001 for 1.0 BTC submitted
# Then:
#   - Check total available = 0.8 BTC < 1.0 BTC required
#   - Cancel entire order
#   - NO trade executions
#   - Generate 1 cancel event
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

## 2. NON-FUNCTIONAL REQUIREMENTS (MUST-HAVES)

### NFR-1: Performance

- [ ] **Throughput**: System MUST process >1000 orders/second
- [ ] **Latency**: Order matching MUST complete within 10ms (p99)
- [ ] **BBO Update**: MUST calculate and broadcast BBO within 1ms of state change

**Verification Method:**

- Load test with 1500 orders/sec for 60 seconds
- Measure p50, p95, p99 latency using Locust or k6

---

### NFR-2: Technology Stack

- [ ] **Matching Engine**: C++ (MANDATORY for performance)
- [ ] **Order Gateway**: Python 3.11+ with FastAPI
- [ ] **Market Data Service**: Python 3.11+ with WebSockets
- [ ] **Communication**: Lightweight IPC (e.g., ZeroMQ, multiprocessing.Queue)

**Justification (from DECISIONS.md):**

- C++ chosen for matching engine to achieve <10μs matching latency
- Python chosen for API services for rapid development (not on critical path)

---

### NFR-3: Testing & Quality

- [ ] **Unit Test Coverage**: >90% for matching engine core logic
- [ ] **Integration Tests**: End-to-end order submission → matching → broadcast flow
- [ ] **Test Framework**: pytest (Python), Google Test (C++)

---

### NFR-4: Documentation

- [ ] README.md with setup instructions (5-minute golden path)
- [ ] Architecture diagrams (sequence diagram for order lifecycle)
- [ ] API specifications (OpenAPI 3.0 format preferred)
- [ ] Video demonstration (10-15 minutes)

---

## 3. OUT OF SCOPE (EXPLICITLY EXCLUDED)

❌ User authentication/authorization  
❌ Account & risk management  
❌ Database persistence (order book is in-memory only)  
❌ Production deployment infrastructure (Docker sufficient)  
❌ Advanced order types (Stop-Loss, Iceberg, etc.)  
❌ Multiple trading pairs (single pair: BTC-USDT)

---

## 4. DATA STRUCTURES (DESIGN CONSTRAINTS)

### Order Book Structure (C++)

**Requirement:** Optimal time complexity for core operations

| Operation | Target Complexity | Data Structure |
|-----------|-------------------|----------------|
| Add order (new price) | O(log M) | `std::map` (Red-Black tree) |
| Add order (existing price) | O(1) | `std::list` (doubly-linked) |
| Cancel order | O(1) | `std::unordered_map` + pointer |
| Match best order | O(1) | Direct access via best bid/ask pointers |
| Get BBO | O(1) | Cached pointers to tree nodes |

**Justification:**

- M = number of distinct price levels (typically <100 in crypto)
- O(log M) for price-level insertion is acceptable
- O(1) for time priority (FIFO) is critical for high throughput

---

## 5. ACCEPTANCE CRITERIA SUMMARY

### ✅ Project passes if:

1. All FR-1 through FR-3 checkboxes are marked complete
2. Performance benchmark shows >1000 orders/sec sustained
3. End-to-end test demonstrates: Order submission → Matching → Trade broadcast
4. Video demonstration explains:
   - Code walkthrough of C++ matching logic
   - Live demo of system handling 100+ orders
   - Explanation of architectural decisions (why C++, why microservices)
5. Code compiles and runs on reviewer's machine within 5 minutes

### ❌ Project fails if:

1. Any trade-through occurs (violates FR-1.2)
2. Performance <1000 orders/sec
3. Missing video demonstration
4. Code does not compile/run

---

## 6. IMPLEMENTATION PRIORITY (FOR 5-DAY TIMELINE)

### Day 1-2: Core Engine (HIGHEST PRIORITY)

- C++ order book data structure
- Price-time priority matching algorithm
- Market + Limit order handling

### Day 3: API Layer

- Python Order Gateway (REST endpoint)
- IPC communication with C++ engine

### Day 4: Market Data + Testing

- WebSocket broadcast service
- Integration tests
- Performance benchmarking

### Day 5: Documentation + Video

- README, architecture diagrams
- Video recording and editing

---

## 7. RISK MITIGATION

| Risk | Mitigation |
|------|------------|
| C++ complexity exceeds 5-day timeline | Use AI subagent (matching-engine-expert) with TDD workflow |
| IPC between Python-C++ fails | Fallback to simplest mechanism (multiprocessing.Queue) |
| Performance target missed | Profile with gprof, optimize hot paths only |
| Video quality poor | Use Loom or OBS, 1080p minimum, clear audio |

---

## Sign-off

**This specification is the absolute source of truth for the goquant project.**

- All AI-generated code MUST cite specific FR/NFR numbers.
- All design decisions MUST be logged in DECISIONS.md with references to this spec.

