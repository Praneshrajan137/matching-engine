# Troubleshooting Guide

Common issues and solutions for the GoQuant Matching Engine system.

---

## 🔴 Redis Connection Issues

### Problem: "Failed to connect to Redis"

**Symptoms:**
- Order Gateway health check returns 503
- Services fail to start
- Error: `redis.exceptions.ConnectionError`

**Solutions:**

**Check if Redis is running:**
```powershell
# Windows
docker ps | findstr redis

# Should show running container
```

**Start Redis:**
```powershell
# If container exists but stopped
docker start redis

# If container doesn't exist
docker run -d --name redis -p 6379:6379 redis:latest
```

**Verify Redis is accessible:**
```powershell
docker exec redis redis-cli ping
# Should return: PONG
```

**Check port not blocked:**
```powershell
# Test Redis connection
telnet localhost 6379
# OR
Test-NetConnection -ComputerName localhost -Port 6379
```

---

## 🔴 Port Already in Use

### Problem: "Address already in use" (Port 8000 or 8001)

**Symptoms:**
- Services fail to start
- Error: `OSError: [WinError 10048]`

**Solution:**

**Find process using the port:**
```powershell
# Windows
netstat -ano | findstr :8000
netstat -ano | findstr :8001

# Note the PID (last column)
```

**Kill the process:**
```powershell
taskkill /PID <PID> /F

# Example:
taskkill /PID 12345 /F
```

**Linux/Mac:**
```bash
# Find and kill process
lsof -ti:8000 | xargs kill -9
lsof -ti:8001 | xargs kill -9
```

---

## 🔴 Virtual Environment Issues

### Problem: "ModuleNotFoundError: No module named 'fastapi'"

**Symptoms:**
- Python services fail to start
- Missing module errors

**Solution:**

**Create and activate venv:**
```powershell
# For Order Gateway
cd order-gateway
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

**Repeat for Market Data:**
```powershell
cd ../market-data
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Fix PowerShell execution policy (if needed):**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## 🔴 C++ Engine Build Failures

### Problem: CMake or compiler errors

**Symptoms:**
- Build fails with CMake errors
- Missing compiler
- Linker errors

**Solutions:**

**Reconfigure CMake:**
```powershell
cd matching-engine
Remove-Item -Recurse -Force build
mkdir build
cd build
cmake ..
cmake --build . --config Debug
```

**Check Visual Studio Build Tools installed:**
- Download from: https://visualstudio.microsoft.com/downloads/
- Install "Desktop development with C++"

**Check CMake installed:**
```powershell
cmake --version
# Should show version 3.10 or higher
```

---

## 🔴 C++ Engine Won't Start

### Problem: engine_runner.exe crashes immediately

**Symptoms:**
- Engine exits with error code
- No logs produced
- System error dialog

**Solutions:**

**Check Redis is running FIRST:**
```powershell
docker ps | findstr redis
```

**Run engine manually to see errors:**
```powershell
cd matching-engine\build\src\Debug
.\engine_runner.exe

# Check output for specific error messages
```

**Common causes:**
- Redis not running (most common)
- Port 6379 not accessible
- Missing DLL files (rare on Windows)

---

## 🔴 No WebSocket Messages

### Problem: WebSocket connects but no market data

**Symptoms:**
- websocket_test.html shows "Connected"
- No trade/BBO/L2 messages appear
- Browser console shows no errors

**Solutions:**

**Check Market Data service is running:**
```powershell
curl http://localhost:8001/health

# Should return: {"status":"healthy"}
```

**Verify Redis pub/sub channels:**
```powershell
docker exec redis redis-cli PUBSUB CHANNELS

# Should show:
# 1) "trade_events"
# 2) "bbo_updates"
# 3) "order_book_updates"
```

**Check if anyone is subscribed:**
```powershell
docker exec redis redis-cli PUBSUB NUMSUB trade_events bbo_updates order_book_updates

# Should show non-zero subscribers
```

**Manually publish test message:**
```powershell
docker exec redis redis-cli PUBLISH trade_events '{"test":"message"}'

# Should appear in WebSocket
```

---

## 🔴 Benchmark Fails or Low Performance

### Problem: Benchmark shows <1000 orders/sec

**Symptoms:**
- Throughput below target
- Many failed requests
- Timeout errors

**Solutions:**

**Ensure uvicorn workers are set:**
```powershell
# Check if workers parameter is used
$env:UVICORN_WORKERS = "4"
python start_system.py
```

**Reduce logging during benchmark:**
```powershell
$env:LOG_LEVEL = "WARNING"
python start_system.py
```

**Check system resources:**
```powershell
# Windows Task Manager
# - CPU usage should be <80%
# - Memory should have >2GB free
# - Disk I/O not maxed
```

**Use optimized benchmark:**
```powershell
cd benchmark
python performance_test.py

# Should use requests.Session for connection reuse
```

---

## 🔴 Orders Not Being Processed

### Problem: Orders submitted but not processed by engine

**Symptoms:**
- Queue length keeps growing
- No engine logs
- No trades generated

**Check queue length:**
```powershell
curl http://localhost:8000/health

# Check queue_length in response
```

**Check if engine is consuming:**
```powershell
docker exec redis redis-cli LLEN order_queue

# Submit order, then check again
# Length should decrease
```

**Verify engine is running:**
```powershell
# Check if engine_runner.exe process exists
Get-Process engine_runner -ErrorAction SilentlyContinue
```

**Check engine logs:**
- Look for "Order received" messages
- Look for "Redis connection established"
- Look for error messages

---

## 🔴 Permission Denied Errors

### Problem: Cannot run scripts or executables

**Symptoms:**
- "Access denied"
- "Permission denied"
- Scripts won't execute

**Solutions:**

**PowerShell execution policy:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Docker permissions:**
```powershell
# Run PowerShell as Administrator for Docker commands
# OR add user to docker-users group
```

**File permissions:**
```powershell
# Ensure you have write access to project directory
icacls "C:\Users\Pranesh\OneDrive\Music\Matching Engine" /grant ${env:USERNAME}:(OI)(CI)F
```

---

## 🔴 Test Scripts Fail

### Problem: test_priority_0.ps1 or test_task_a.ps1 fail

**Check Prerequisites:**
```powershell
# 1. Redis running
docker ps | findstr redis

# 2. C++ engine built
Test-Path "matching-engine\build\src\Debug\engine_runner.exe"

# 3. Python dependencies installed
cd order-gateway
pip list | findstr fastapi

# 4. Current directory correct
Get-Location
# Should be in goquant folder
```

**Run with verbose output:**
```powershell
.\test_task_a.ps1 -Verbose
```

---

## 📞 Getting More Help

### Enable Debug Logging

**For Python services:**
```powershell
$env:LOG_LEVEL = "DEBUG"
python start_system.py
```

**For C++ engine:**
- Debug logs are already enabled in code
- Check console output or redirect to file:
```powershell
.\engine_runner.exe > engine_debug.log 2>&1
```

### Collect Diagnostic Information

```powershell
# System info
systeminfo | findstr /C:"OS"

# Docker status
docker ps
docker logs redis

# Port status
netstat -ano | findstr "6379 8000 8001"

# Python version
python --version

# CMake version
cmake --version
```

### Clean Slate Restart

```powershell
# 1. Stop all services
# Press Ctrl+C in start_system.py terminal

# 2. Clean Redis
docker exec redis redis-cli FLUSHALL

# 3. Restart
python start_system.py
```

---

## 📚 Additional Resources

- **README.md** - Quick start guide
- **WORK_COMPLETE_SUMMARY.md** - What's been implemented
- **REMAINING_WORK_ROADMAP.md** - Detailed task breakdown
- **GitHub Issues** - Report bugs or ask questions

---

**Still stuck?** Check the logs in:
- Order Gateway console output
- Market Data console output
- C++ Engine console output
- Redis logs: `docker logs redis`
