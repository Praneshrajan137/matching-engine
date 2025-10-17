# goquant - High-Performance Matching Engine

**Status:** 🚧 In Development (Day 3/5 COMPLETE ✅)  
**Interview Assignment for:** [Company Name]  
**Deadline:** 2025-10-19

> **Day 3 Update:** All code complete! Awaiting Python/Redis installation for testing.  
> See `DAY3_IMPLEMENTATION_COMPLETE.md` for details.

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
2. **Redis** - See `REDIS_SETUP_WINDOWS.md` (Memurai recommended)
3. **Visual Studio Build Tools** - For C++ compilation

### Automated Setup
```powershell
# Setup Python environments
.\scripts\setup_python_env.ps1

# Build C++ engine
cd matching-engine\build
cmake ..
cmake --build . --config Debug

# Run tests
cd ..\order-gateway
.venv\Scripts\Activate.ps1
pytest tests/ -v

# Start all services
.\scripts\start_all_services.ps1
```

### Manual Setup
See `DAY3_IMPLEMENTATION_COMPLETE.md` for detailed instructions.

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
**Day 3:** API services ✅ **CODE COMPLETE** (awaiting Python/Redis install)  
**Day 4:** Integration & performance testing ⏳  
**Day 5:** Documentation & video demo ⏳

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

