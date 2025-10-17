# GoQuant Trading System - Quick Start Guide

**Get the system running in 5 minutes!**

---

## ✅ Prerequisites Check

Before starting, ensure you have:

- ✅ **Docker** installed and running
- ✅ **Python 3.11+** installed
- ✅ **C++ compiler** (MSVC on Windows)
- ✅ **CMake** installed

---

## 🚀 Quick Start (3 Commands)

### Option 1: Automated Startup (Recommended)

```bash
# 1. Navigate to project directory
cd goquant

# 2. Run the startup script
python start_system.py
```

That's it! The script will:
- ✅ Start Redis automatically
- ✅ Launch Order Gateway (Port 8000)
- ✅ Launch Market Data Service (Port 8001)
- ✅ Start C++ Matching Engine
- ✅ Monitor all services

Press `Ctrl+C` to stop all services gracefully.

---

### Option 2: Manual Startup

If you prefer manual control:

#### Step 1: Start Redis

```bash
docker start redis
# Or if container doesn't exist:
docker run -d --name redis -p 6379:6379 redis:latest

# Verify:
docker exec redis redis-cli ping
# Should return: PONG
```

#### Step 2: Start Order Gateway (Terminal 1)

```bash
cd order-gateway
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
```

#### Step 3: Start Market Data Service (Terminal 2)

```bash
cd market-data
python -m uvicorn src.main:app --host 0.0.0.0 --port 8001
```

#### Step 4: Start C++ Engine (Terminal 3)

```bash
cd matching-engine/build/src/Debug
./engine_runner.exe
```

---

## 🧪 Verify Everything Works

Run the automated test suite:

```bash
python test_system.py
```

Expected output:
```
[PASS] Health Checks
[PASS] Order Submission
[PASS] Input Validation
[PASS] Performance Test
[PASS] API Documentation

✓ ALL TESTS PASSED (5/5)
```

---

## 📊 Access the Services

Once running, you can access:

| Service | URL | Description |
|---------|-----|-------------|
| **Order Gateway** | http://localhost:8000 | REST API for order submission |
| **API Documentation** | http://localhost:8000/v1/docs | Interactive Swagger UI |
| **Market Data** | http://localhost:8001 | WebSocket server |
| **Health Checks** | http://localhost:8000/health | Service status |
| | http://localhost:8001/health | |

---

## 📝 Submit Your First Order

### Using curl:

```bash
curl -X POST http://localhost:8000/v1/orders \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTC-USDT",
    "order_type": "limit",
    "side": "buy",
    "price": "60000.00",
    "quantity": "1.0"
  }'
```

### Using Python:

```python
import requests

order = {
    "symbol": "BTC-USDT",
    "order_type": "limit",
    "side": "buy",
    "price": "60000.00",
    "quantity": "1.0"
}

response = requests.post(
    "http://localhost:8000/v1/orders",
    json=order
)

print(response.json())
# Output: {"order_id": "...", "status": "accepted", "timestamp": "..."}
```

### Using PowerShell:

```powershell
$order = @{
    symbol = "BTC-USDT"
    side = "buy"
    order_type = "limit"
    price = "60000.00"
    quantity = "1.0"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/v1/orders" `
  -Method POST `
  -ContentType "application/json" `
  -Body $order
```

---

## 🎯 Test All 4 Order Types

```bash
# 1. Market Order (executes immediately)
curl -X POST http://localhost:8000/v1/orders \
  -H "Content-Type: application/json" \
  -d '{"symbol":"BTC-USDT","order_type":"market","side":"buy","quantity":"0.1"}'

# 2. Limit Order (rests on book if not marketable)
curl -X POST http://localhost:8000/v1/orders \
  -H "Content-Type: application/json" \
  -d '{"symbol":"BTC-USDT","order_type":"limit","side":"sell","price":"60000.00","quantity":"1.0"}'

# 3. IOC Order (immediate-or-cancel)
curl -X POST http://localhost:8000/v1/orders \
  -H "Content-Type: application/json" \
  -d '{"symbol":"BTC-USDT","order_type":"ioc","side":"buy","price":"60000.00","quantity":"0.5"}'

# 4. FOK Order (fill-or-kill)
curl -X POST http://localhost:8000/v1/orders \
  -H "Content-Type: application/json" \
  -d '{"symbol":"BTC-USDT","order_type":"fok","side":"sell","price":"59900.00","quantity":"0.3"}'
```

---

## 🔍 Monitor the System

### Check Service Health:

```bash
# Order Gateway
curl http://localhost:8000/health

# Market Data
curl http://localhost:8001/health
```

### Watch Redis Queue:

```bash
# See queued orders
docker exec redis redis-cli LLEN order_queue

# Monitor in real-time
docker exec redis redis-cli MONITOR
```

### View Logs:

The Python services print logs to stdout/stderr. The C++ engine uses JSON structured logging.

---

## 🛑 Stop the System

### If using automated startup:
Press `Ctrl+C` in the terminal running `start_system.py`

### If using manual startup:
Press `Ctrl+C` in each terminal window (Order Gateway, Market Data, C++ Engine)

### Stop Redis:
```bash
docker stop redis
# Or to stop and remove:
docker stop redis && docker rm redis
```

---

## ⚡ Performance Benchmarking

Run the performance benchmark:

```bash
cd benchmark
python performance_test.py
```

This will:
- Submit 5000 orders using 10 concurrent threads
- Measure throughput (orders/sec)
- Calculate latency statistics (P50, P95, P99)
- Verify against >1000 orders/sec requirement

---

## 🐛 Troubleshooting

### Redis connection failed
```bash
# Check if Redis is running
docker ps | grep redis

# Restart Redis
docker restart redis

# Check logs
docker logs redis
```

### Port already in use
```bash
# Find process using port 8000
# Windows:
netstat -ano | findstr :8000

# Kill the process (replace PID)
taskkill /PID <PID> /F

# Linux/Mac:
lsof -ti:8000 | xargs kill -9
```

### C++ engine won't start
```bash
# Rebuild the engine
cd matching-engine/build
cmake --build . --config Debug

# Check if executable exists
ls src/Debug/engine_runner.exe
```

### Python dependencies missing
```bash
# Install all dependencies
cd order-gateway
python -m pip install fastapi uvicorn redis pydantic

cd ../market-data
python -m pip install fastapi uvicorn redis websockets
```

---

## 📚 Next Steps

- **Read the Architecture**: See `SPECIFICATION.md` for system design
- **Review the Code**: Check `matching-engine/src/matching_engine.cpp`
- **Run Unit Tests**: Execute C++ tests with `ctest -C Debug -V`
- **Explore API**: Visit http://localhost:8000/v1/docs
- **Watch WebSocket**: Connect to `ws://localhost:8001/ws/market-data`

---

## 📧 Support

For issues:
1. Check logs in each service terminal
2. Verify all services are running with `test_system.py`
3. Review `TROUBLESHOOTING.md` for common issues
4. Check Redis is accessible: `docker exec redis redis-cli ping`

---

## 🎉 Success Indicators

Your system is working correctly if:

✅ All health checks return `{"status": "healthy", "redis": "connected"}`  
✅ Test suite passes 5/5 tests  
✅ Orders receive 201 Created response with `order_id`  
✅ C++ engine logs show "Order received" messages  
✅ No error messages in any terminal window  

**Happy Trading!** 🚀