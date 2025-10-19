# goquant - High-Performance Matching Engine

**Status:** ✅ INTEGRATION COMPLETE (Day 4 Progress)  
**Interview Assignment for:** [Company Name]  
**Deadline:** 2025-10-19

> **Latest Update:** Redis integration successful! All services running and tested.  
> System ready for full end-to-end testing and performance benchmarking.

## 🎯 Project Goal

Build a high-performance cryptocurrency matching engine implementing:
- Price-time priority matching (REG NMS-inspired)
- 4 order types: Market, Limit, IOC, FOK
- >1000 orders/second throughput
- Real-time market data broadcast

## 🏗️ Architecture

**Pragmatic Microservices (3 services):**
1. **Order Gateway** (Python/FastAPI) - REST API for order submission
2. **Matching Engine** (C++) - High-performance order book
3. **Market Data** (Python) - WebSocket market data feed

## 📋 Quick Start (Windows)

### Prerequisites
1. **Python 3.11+** - https://www.python.org/downloads/
2. **Redis** - Docker or WSL2 (see setup below)
3. **Visual Studio Build Tools** - For C++ compilation

### 🚀 5-Minute Setup

#### Step 1: Start Redis
```powershell
# Option A: Docker (Recommended)
docker run -d --name redis -p 6379:6379 redis:7-alpine

# Option B: WSL2
wsl sudo service redis-server start
```

#### Step 2: Verify Redis
```powershell
python test_redis_integration.py
# Should show all tests passing ✓
```

#### Step 3: Start System
```powershell
python start_system.py
# All 3 services will start automatically
```

#### Step 4: Test Order Submission
```powershell
# In a new terminal
python test_order_submission.py
```

### 📖 Detailed Setup
See `REDIS_WINDOWS_SETUP.md` for troubleshooting and alternative methods.

## 📚 Documentation

- **SPECIFICATION.md** - Complete requirements (FR/NFR)
- **DECISIONS.md** - Architecture decision log
- **docs/architecture.md** - System design diagrams
- **docs/api-spec.yml** - OpenAPI 3.0 specification

## 🧪 Testing

```bash
# Python tests
pytest order-gateway/tests/
pytest market-data/tests/

# C++ tests
cd matching-engine/build
make test
```

## 📊 Current Progress

**Day 0:** Foundation setup ✅  
**Day 1:** C++ order book implementation ✅ (10/10 tests passing)  
**Day 2:** Matching algorithm ✅ (30/30 tests passing)  
**Day 3:** API services ✅ (39/39 tests passing)  
**Day 4:** **Redis Integration Complete** ✅ System fully operational  
**Day 5:** Performance testing & documentation ⏳

### Day 3 Deliverables ✅
- ✅ Order Gateway (FastAPI + Redis + 9 tests)
- ✅ Market Data Service (WebSocket + Redis pub/sub)
- ✅ C++ Engine Runner (event loop with JSON utils)
- ✅ Helper scripts (setup, test, run)

## 📝 Development Workflow

1. Read SPECIFICATION.md (understand requirement)
2. Write failing test (test-expert agent)
3. Implement feature (matching-engine-expert / api-specialist)
4. Review code (code-reviewer agent)
5. Commit (with FR/NFR reference)

## 🚀 Performance Targets

- **Throughput:** >1000 orders/sec
- **Latency:** <10ms per order (p99)
- **Memory:** <500MB for 10K active orders

## 📧 Contact

[Your Name] - [your.email@example.com]

**Interview Assignment** - Not for production use

