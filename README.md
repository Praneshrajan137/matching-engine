# High-Performance Matching Engine

A cryptocurrency matching engine with production-grade core algorithms and architecture. Achieves **2,300+ orders/second** with sub-10ms latency using battle-tested price-time priority matching.

## 🎯 Overview

This matching engine implements:
- **Price-time priority matching** (REG NMS-inspired)
- **4 order types**: Market, Limit, IOC (Immediate-or-Cancel), FOK (Fill-or-Kill)
- **High performance**: 2,300+ orders/second sustained throughput
- **Real-time market data**: WebSocket broadcast with <5ms latency
- **Production-grade core**: Battle-tested matching algorithms with 90%+ test coverage

**Note**: The core matching logic, data structures, and system architecture are production-ready. Operational features (persistence, authentication, monitoring) are documented for extension.

## 🏗️ Architecture

**Microservices Design (3 services):**
1. **Order Gateway** (Python/FastAPI) - REST API for order submission
2. **Matching Engine** (C++) - High-performance order book with optimal data structures
3. **Market Data** (Python) - WebSocket real-time market data feed

**Technology Stack:**
- C++17 for performance-critical matching logic (<10μs per order)
- Python 3.11+ with FastAPI for API services
- Redis for lightweight message passing
- Composite data structures (std::map + std::list + hash map) for O(1) operations

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

## 📚 Additional Resources

- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues and solutions


## 🧪 Testing

```bash
# Python tests
pytest order-gateway/tests/
pytest market-data/tests/

# C++ tests
cd matching-engine/build
make test
```

## ✅ Features

### Core Matching
- Price-time priority with strict FIFO ordering
- Trade-through prevention (REG NMS compliant)
- Real-time BBO (Best Bid/Offer) calculation
- Support for 4 order types: Market, Limit, IOC, FOK

### API & Data Feeds
- RESTful order submission API (FastAPI)
- WebSocket real-time market data
- Trade execution reports
- L2 order book depth (top 10 levels)

### Testing & Quality
- 90%+ test coverage
- 39+ unit and integration tests
- Comprehensive performance benchmarks
- Detailed technical documentation (3,300+ lines)

## 🚀 Performance

- **Throughput:** 2,325 orders/second (4× single-core baseline)
- **Latency:** <10ms (p99), <5ms (p50)
- **Memory:** <300MB for 10K active orders
- **Matching Speed:** <10μs per order (C++ core)

See [PERFORMANCE_REPORT.md](PERFORMANCE_REPORT.md) for detailed benchmarks.

## 📄 Documentation

- **[SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md)** - Complete system design, data structures, and algorithms
- **[PERFORMANCE_REPORT.md](PERFORMANCE_REPORT.md)** - Detailed benchmarks and optimization analysis
- **[USER_GUIDE.md](HOW_TO_USE_SYSTEM.md)** - API usage examples and integration guide
- **[DECISIONS.md](DECISIONS.md)** - Architecture decision records (ADRs)
- **[FEATURES.md](SPECIFICATION.md)** - Complete feature specifications

## 🔧 Production Considerations

**Production-ready components:**
- ✅ Core matching algorithms (price-time priority)
- ✅ High-performance data structures
- ✅ Real-time market data feeds
- ✅ Comprehensive test coverage (90%+)
- ✅ Detailed technical documentation

**Extensions for full deployment:**
- ⏳ Persistence layer (order book snapshots)
- ⏳ Authentication & authorization
- ⏳ Risk management & position limits
- ⏳ Multi-symbol support
- ⏳ Monitoring & alerting infrastructure

See [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md) Section 7 for detailed trade-offs and implementation paths.

