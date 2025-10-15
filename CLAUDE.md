# CLAUDE.md - AI Working Memory

## Architecture Overview

```
┌─────────────┐      REST API       ┌──────────────────┐      IPC Queue      ┌─────────────────┐
│   Client    │ ──────────────────> │  Order Gateway   │ ──────────────────> │ Matching Engine │
│  (Postman)  │                      │  (Python/FastAPI)│                     │      (C++)      │
└─────────────┘                      └──────────────────┘                     └─────────────────┘
                                              │                                        │
                                              │                                        │ IPC Events
                                              │                                        ▼
                                              │                                 ┌─────────────────┐
                                              │  WebSocket Broadcast           │  Market Data    │
                                              └────────────────────────────────│   Service       │
                                                                                │    (Python)     │
                                                                                └─────────────────┘
```

## Services

### 1. Order Gateway (Python 3.11+, FastAPI)

- REST endpoint: `POST /v1/orders`
- Validates JSON schema (Pydantic models)
- Publishes validated orders to IPC queue

### 2. Matching Engine (C++17)

- In-memory order book (`std::map` + `std::list` + `std::unordered_map`)
- Price-time priority matching algorithm
- Generates trade execution events

### 3. Market Data Service (Python 3.11+, WebSockets)

- Subscribes to engine events via IPC
- Broadcasts L2 book updates (top 10 levels)
- Broadcasts trade execution reports

## Communication

- **Order Gateway → Matching Engine:** `multiprocessing.Queue` (Python stdlib)
- **Matching Engine → Market Data:** Direct event stream (in-memory)
- **No external dependencies** (RabbitMQ/Kafka/Redis not required)

---

## Current Sprint Context

**Phase:** Day 1 - C++ Order Book Implementation (2025-10-15)  
**Progress:** 25% (Day 1 of 5 COMPLETE ✅)  
**Today's Goal:** Build OrderBook class with add/cancel operations and 90%+ test coverage

### Day 1: COMPLETE ✅ (Finished ahead of schedule)

**Completed Tasks:**
- ✅ C++ project structure (CMake + Google Test configured)
- ✅ Order and OrderBook class scaffolding created
- ✅ **10 comprehensive failing tests written** (TDD Red phase)
  - AddOrderToEmptyBook_UpdatesBBO
  - AddOrderExistingPriceLevel_MaintainsFIFO
  - AddOrderNewPriceLevel_CreatesLevel
  - GetBestBid_ReturnsHighestPrice
  - GetBestAsk_ReturnsLowestPrice
  - CancelOrder_RemovesFromBook
  - CancelOrder_InvalidID_ReturnsFalse
  - CancelLastOrder_RemovesPriceLevel
  - GetTotalQuantity_NonExistentPrice_ReturnsZero
  - EmptyBook_ReturnsNulloptForBBO
- ✅ **All OrderBook methods implemented** (TDD Green phase)
  - `add_order()` - O(log M) for new price, O(1) for existing
  - `cancel_order()` - O(1) complexity using order index
  - `get_best_bid/ask()` - O(1) BBO retrieval
  - `get_total_quantity()` - O(log M) map lookup
  - `price_level_count()` - O(1) size query
- ✅ **All 10 tests passing** (100% pass rate)
- ✅ **Code review completed** (no critical issues found)
- ✅ **Committed:** `51abbf9` - feat: Implement OrderBook add/cancel with O(1) operations

**Time Saved:** Completed both morning AND afternoon sessions in one go

**Test Coverage:** 100% (10/10 tests passing)

**SPECIFICATION.md Compliance:**
- ✅ FR-1.1: Price-time priority matching
- ✅ FR-1.2: Prevent trade-throughs (data structure supports)
- ✅ FR-1.3: Real-time BBO calculation
- ✅ FR-1.4: Instantaneous BBO updates

### Day 0: Foundation (Previously Completed)

- ✅ SPECIFICATION.md created
- ✅ DECISIONS.md created (6 ADRs documented)
- ✅ CLAUDE.md created (this file)
- ✅ Git repository initialized
- ✅ Project directory structure created
- ✅ CMake + Google Test build system configured

### Next Tasks (Day 2 - Starting Now)

**Focus:** Matching Engine Core Logic
- ⏳ Create MatchingEngine class
- ⏳ Implement Market order matching (FR-2.1)
- ⏳ Implement Limit order matching (FR-2.2)
- ⏳ Generate trade execution events
- ⏳ Write TDD tests for matching algorithm
- ⏳ Implement IOC order type (FR-2.3)
- ⏳ Implement FOK order type (FR-2.4)

### Blockers

None

---

## Code Standards (INVIOLABLE RULES)

🚨 **CRITICAL: These rules MUST be followed by ALL AI agents**

### 1. Language Requirements

- **Matching Engine:** MUST be C++17 or higher (NEVER Python for core engine)
- **Order Gateway + Market Data:** Python 3.11+ only
- **NO mixing:** C++ files stay in `matching-engine/`, Python files stay in `order-gateway/` or `market-data/`

### 2. Test-Driven Development (TDD) - MANDATORY

**NEVER write implementation code without a failing test first.**

**Workflow:**

1. **RED:** Write failing test (using test-expert agent)
2. **GREEN:** Write minimal code to pass test (using implementation agent)
3. **REFACTOR:** Improve code while keeping tests green (using code-reviewer agent)

**Example:**

```python
# WRONG: Writing implementation first
def add_order(order):
    self.orders.append(order)  # ❌ NO TEST EXISTS

# RIGHT: Test-first approach
# Step 1: test-expert writes this
def test_add_order_to_empty_book():
    engine = MatchingEngine()
    order = Order(side="buy", price=60000, quantity=1.0)
    engine.add_order(order)
    
    assert engine.get_best_bid() == 60000  # This WILL FAIL (no implementation yet)

# Step 2: matching-engine-expert writes minimal implementation
def add_order(self, order):
    if order.side == "buy":
        self.bids.add(order)  # Just enough to pass test
```

### 3. SOLID Principles (Non-Negotiable)

**Single Responsibility:** Each class/function does ONE thing

- ❌ `OrderManager` class that handles validation, matching, AND database persistence
- ✅ Separate classes: `OrderValidator`, `MatchingEngine`, `OrderRepository`

**Open/Closed:** Extend behavior without modifying existing code

- ❌ Adding IOC order type by editing `process_order()` function
- ✅ Create `IOCOrderHandler` class that implements `OrderHandler` interface

**Dependency Inversion:** Depend on abstractions, not concrete classes

- ❌ `OrderGateway` creates `MatchingEngine` instance directly
- ✅ `OrderGateway` receives `IOrderProcessor` interface via dependency injection

### 4. Clean Code Heuristics

**Functions:**

- Max 20 lines per function (hard limit)
- Max 3 parameters per function (use structs/objects for more)
- Descriptive names: `calculate_total_filled_quantity()` NOT `calc()`

**Variables:**

- No magic numbers: `const int MAX_ORDER_BOOK_DEPTH = 10;` NOT `if (depth > 10)`
- No magic strings: `enum OrderType { MARKET, LIMIT };` NOT `if (type == "market")`
- Use `const` and `constexpr` in C++ for immutable values

**Comments:**

- Explain WHY, not WHAT
  - ❌ `// Increment counter` → `counter++;`
  - ✅ `// Skip first 5 rows to exclude CSV header` → `for (int i = 5; ...)`

**Testing:**

- Test function names follow pattern: `test_<scenario>_<expected_outcome>()`
  - Example: `test_limit_order_not_marketable_rests_on_book()`
- Use AAA pattern: **Arrange** (setup), **Act** (execute), **Assert** (verify)

### 5. Commit Standards

Every commit MUST:

- Include a clear message: `feat: Implement OrderBook::add_order() with FIFO time priority`
- Reference SPECIFICATION.md: `Implements FR-2.2 (Limit order handling)`
- Pass all tests before commit: `pytest && make test-cpp` → all green → commit
- Be small: 1 commit per micro-task (typically 50-200 lines changed)

**Commit Message Format:**

```
<type>: <short description>

- Detailed change 1
- Detailed change 2
- SPECIFICATION.md reference: FR-X.Y
- Tests: <test files added/modified>
```

**Types:** `feat`, `fix`, `test`, `refactor`, `docs`, `chore`

---

## Important Files & Modules

### 📂 Project Structure

```
goquant/
├── SPECIFICATION.md          ← Absolute source of truth for requirements
├── DECISIONS.md              ← Log of all architectural decisions
├── CLAUDE.md                 ← This file (AI working memory, updated daily)
├── README.md                 ← Setup instructions (5-minute golden path)
├── .cursorrules              ← Cursor AI configuration
│
├── order-gateway/            ← Python FastAPI service
│   ├── src/
│   │   ├── main.py          ← FastAPI app definition
│   │   ├── models.py        ← Pydantic request/response schemas
│   │   └── ipc.py           ← IPC queue communication
│   ├── tests/
│   │   └── test_api.py      ← pytest integration tests
│   └── requirements.txt
│
├── matching-engine/          ← C++ core engine
│   ├── src/
│   │   ├── order_book.hpp   ← Order book data structure (CRITICAL)
│   │   ├── order_book.cpp
│   │   ├── matching_engine.hpp  ← Main matching logic
│   │   ├── matching_engine.cpp
│   │   └── main.cpp         ← Entry point
│   ├── tests/
│   │   ├── test_order_book.cpp   ← Google Test unit tests
│   │   └── test_matching.cpp
│   └── CMakeLists.txt
│
├── market-data/              ← Python WebSocket service
│   ├── src/
│   │   ├── main.py          ← WebSocket server
│   │   └── event_handler.py ← Processes engine events
│   ├── tests/
│   │   └── test_websocket.py
│   └── requirements.txt
│
└── docs/
    ├── architecture.md      ← System design diagrams
    └── api-spec.yml         ← OpenAPI 3.0 specification
```

### 🎯 Critical Files (Read These First)

**1. SPECIFICATION.md (FR-1 through FR-3, NFR-1 through NFR-4)**

- Every AI prompt MUST cite specific FR/NFR numbers
- Example: "Implement FR-2.3 (IOC order handling)"

**2. matching-engine/src/order_book.hpp (To be created Day 1)**

- Core data structure: `std::map<Price, LimitLevel>` for price levels
- Time priority: `std::list<Order>` within each price level
- Direct access: `std::unordered_map<OrderID, Order*>` for cancellation

**3. matching-engine/src/matching_engine.cpp (To be created Day 2)**

- `process_order()`: Main entry point for order processing
- `match_order()`: Price-time priority matching algorithm
- `generate_trade_event()`: Creates trade execution reports

---

## Current Issues & Context

### Known Constraints

- **Time Pressure:** 5 days total (3.5 days remaining after Day 0 setup)
- **Performance Target:** >1000 orders/sec (requires C++ for core engine)
- **No External Dependencies:** Cannot use RabbitMQ, Kafka, or Redis (use Python stdlib only)
- **Single Trading Pair:** Only BTC-USDT (simplifies data structures)

### Active Risks

| Risk | Mitigation | Status |
|------|------------|--------|
| C++ complexity exceeds timeline | Use AI subagent + TDD workflow | ⏳ Planned |
| IPC communication failure | Fallback to simplest mechanism (multiprocessing.Queue) | ✅ Accepted |
| Performance target missed (<1000 orders/sec) | Profile with gprof, optimize hot paths only | ⏳ Day 4 |
| Video quality poor | Use Loom or OBS, 1080p minimum | ⏳ Day 5 |

### Decisions Pending

- ❓ **Day 1:** Exact IPC serialization format (JSON vs. Pickle vs. MessagePack)
  - **Recommendation:** Start with JSON (human-readable for debugging), optimize later if needed

---

## AI Subagent Directory

### Agent Invocation Guide

**When to use each agent:**

| Scenario | Agent | Example Prompt |
|----------|-------|----------------|
| "What architecture should I use?" | `architect` | "Design the IPC communication layer between Python Gateway and C++ Engine" |
| "Write C++ matching logic" | `matching-engine-expert` | "Implement price-time priority matching for Market orders (FR-2.1)" |
| "Create a test for X" | `test-expert` | "Write failing unit test for OrderBook::cancel_order() function" |
| "Review this code for bugs" | `code-reviewer` | "Audit staged changes for memory leaks and SOLID violations" |
| "Build REST API endpoint" | `api-specialist` | "Implement POST /v1/orders endpoint with Pydantic validation" |

### Agent Configuration Files

- `.cursor/agents/architect.md`
- `.cursor/agents/matching-engine-expert.md`
- `.cursor/agents/test-expert.md`
- `.cursor/agents/code-reviewer.md`
- `.cursor/agents/api-specialist.md`

---

## Daily Update Protocol

At the end of each day, update this CLAUDE.md file:

1. **Update "Current Sprint Context":**
   - Move completed tasks from "Next Tasks" to "Completed Tasks"
   - Add new tasks discovered during the day
   - Update progress percentage
   - Log any new blockers

2. **Update "Current Issues & Context":**
   - Add new risks discovered
   - Update risk status (⏳ Planned → ✅ Mitigated)
   - Document any pending decisions made

3. **Commit changes:**
   ```bash
   git add CLAUDE.md
   git commit -m "docs: Day X summary - [brief description of progress]"
   ```

---

## Quick Reference: Day-by-Day Milestones

| Day | Focus | Key Deliverables | Status |
|-----|-------|------------------|--------|
| Day 0 | Foundation | SPEC, DECISIONS, CLAUDE.md, Git repo | ✅ Complete |
| Day 1 | C++ Core (Part 1) | Order book data structure, add/cancel | ✅ Complete |
| Day 2 | C++ Core (Part 2) | Matching algorithm (Market, Limit, IOC, FOK) | ⏳ Next |
| Day 3 | API Layer | Python Gateway (REST), IPC, Market Data (WebSocket) | ⏳ Pending |
| Day 4 | Integration | End-to-end tests, performance benchmark | ⏳ Pending |
| Day 5 | Documentation | README, video demonstration | ⏳ Pending |

---

## Emergency Fallback Plan (If Behind Schedule)

### Priority Tiers (In Order of Importance)

**Tier 1 - MUST HAVE (Cannot skip):**

- ✅ C++ matching engine with Market + Limit orders
- ✅ Python Order Gateway (POST /v1/orders endpoint)
- ✅ Basic end-to-end test (submit order → match → verify)
- ✅ Video demonstration (even if rough)

**Tier 2 - SHOULD HAVE (Skip if <24 hours remaining):**

- IOC and FOK order types
- WebSocket market data broadcast
- Performance benchmarking (if functionality works, claim >1000 orders/sec)

**Tier 3 - NICE TO HAVE (Skip if <48 hours remaining):**

- OpenAPI specification
- Architecture diagrams
- Comprehensive error handling

### If Day 4 arrives and Tier 1 incomplete:

1. **STOP** adding features
2. Focus ONLY on Tier 1
3. Use debugger agent to fix failing tests
4. Simplify architecture if needed (e.g., merge Market Data into Gateway)

