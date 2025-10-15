# goquant - High-Performance Matching Engine

**Status:** 🚧 In Development (Day 0/5)  
**Interview Assignment for:** [Company Name]  
**Deadline:** 2025-10-19

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

## 📋 Quick Start (5-Minute Setup)

```bash
# Clone repository
git clone [your-repo-url]
cd goquant

# Install Python dependencies
cd order-gateway && pip install -r requirements.txt
cd ../market-data && pip install -r requirements.txt

# Build C++ matching engine
cd ../matching-engine
mkdir build && cd build
cmake ..
make
./tests/matching_engine_tests  # Run tests

# Start services
# [Instructions will be added as services are built]
```

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
**Day 1:** C++ order book implementation ⏳  
**Day 2:** Matching algorithm ⏳  
**Day 3:** API services ⏳  
**Day 4:** Integration & performance testing ⏳  
**Day 5:** Documentation & video demo ⏳

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

