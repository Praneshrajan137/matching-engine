# Redis Setup for Windows

## Current Status
- ❌ Redis not installed
- ❌ Python not installed
- ⏳ Implementation code ready

## Prerequisites for Day 3

### 1. Install Python 3.11+

**Option A: Official Python (Recommended)**
```powershell
# Download from https://www.python.org/downloads/
# During installation, CHECK "Add Python to PATH"
```

**Option B: Microsoft Store**
```powershell
# Search for "Python 3.11" in Microsoft Store
```

**Verify installation:**
```powershell
python --version  # Should show Python 3.11.x or higher
```

### 2. Install Redis for Windows

**Option A: Memurai (Recommended for Windows)**
```powershell
# Download from https://www.memurai.com/get-memurai
# Free Developer Edition available
# Installs as Windows Service
```

**Option B: WSL2 + Redis**
```powershell
# Enable WSL
wsl --install

# Inside WSL Ubuntu terminal:
sudo apt-get update
sudo apt-get install redis-server
redis-server --daemonize yes
```

**Option C: Docker Desktop**
```powershell
# Install Docker Desktop for Windows
# Then run:
docker run -d -p 6379:6379 --name redis redis:7-alpine
```

**Verify Redis:**
```powershell
redis-cli ping  # Should return "PONG"
```

## Quick Start After Setup

### Terminal 1: Install Dependencies
```powershell
cd "C:\Users\Pranesh\OneDrive\Music\Matching Engine\goquant\order-gateway"
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Terminal 2: Run Tests (TDD Verification)
```powershell
cd "C:\Users\Pranesh\OneDrive\Music\Matching Engine\goquant\order-gateway"
.venv\Scripts\Activate.ps1
pytest tests/test_api.py -v
```

**Expected:** All tests should PASS (implementation already complete)

### Terminal 3: Start Order Gateway
```powershell
cd "C:\Users\Pranesh\OneDrive\Music\Matching Engine\goquant\order-gateway"
.venv\Scripts\Activate.ps1
uvicorn src.main:app --reload --port 8000
```

### Terminal 4: Test API
```powershell
# Submit a test order
curl -X POST http://localhost:8000/v1/orders `
  -H "Content-Type: application/json" `
  -d '{\"symbol\":\"BTC-USDT\",\"order_type\":\"limit\",\"side\":\"buy\",\"quantity\":\"1.5\",\"price\":\"60000.00\"}'

# Check health
curl http://localhost:8000/health
```

### Verify Redis Queue
```powershell
redis-cli LRANGE order_queue 0 -1
```

## Troubleshooting

### Redis Connection Error
```
Error: Failed to connect to Redis
```
**Fix:** Start Redis service
```powershell
# Memurai
net start Memurai

# WSL
wsl redis-server --daemonize yes

# Docker
docker start redis
```

### Import Errors in Tests
```
Error: No module named 'fastapi'
```
**Fix:** Activate virtual environment
```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

