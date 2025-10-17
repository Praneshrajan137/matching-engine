# Redis Quick Start Guide

You mentioned you downloaded Redis - here's how to get it running on Windows.

---

## 🎯 Goal
Start Redis so you can test the full goquant system (all 39 tests are already passing!).

---

## Option 1: Memurai (Easiest for Windows)

**Download:** https://www.memurai.com/get-memurai

1. Download the installer
2. Run installer (accept defaults)
3. Service starts automatically

**Verify:**
```powershell
redis-cli ping
# Should return: PONG
```

If not in PATH, try:
```powershell
"C:\Program Files\Memurai\memurai-cli.exe" ping
```

---

## Option 2: Redis ZIP File

If you downloaded a ZIP file:

1. Find where you extracted it (e.g., `C:\redis`)
2. Open terminal in that folder
3. Run:
```powershell
.\redis-server.exe
```

Leave this window open (Redis is now running).

**In a new terminal:**
```powershell
cd C:\path\to\redis
.\redis-cli.exe ping
# Should return: PONG
```

---

## Option 3: Docker (If you have Docker Desktop)

```powershell
docker run -d -p 6379:6379 --name redis redis:7-alpine

# Verify
docker ps
```

---

## ✅ Once Redis Responds to PING

You're ready to run the full system!

**Run this script:**
```powershell
cd "C:\Users\Pranesh\OneDrive\Music\Matching Engine\goquant"

# This will open 3 windows
.\scripts\start_all_services.ps1
```

**Or manually (4 terminals):**

**Terminal 1: Order Gateway**
```powershell
cd "C:\Users\Pranesh\OneDrive\Music\Matching Engine\goquant\order-gateway"
.\.venv\Scripts\Activate.ps1
uvicorn src.main:app --reload --port 8000
```

**Terminal 2: Market Data**
```powershell
cd "C:\Users\Pranesh\OneDrive\Music\Matching Engine\goquant\market-data"
.\.venv\Scripts\Activate.ps1
uvicorn src.main:app --reload --port 8001
```

**Terminal 3: C++ Engine**
```powershell
cd "C:\Users\Pranesh\OneDrive\Music\Matching Engine\goquant\matching-engine\build\src\Debug"
.\engine_runner.exe
```

**Terminal 4: Test**
```powershell
curl http://localhost:8000/health
# Should show: "status": "healthy", "redis": "connected"

curl -X POST http://localhost:8000/v1/orders `
  -H "Content-Type: application/json" `
  -d '{\"symbol\":\"BTC-USDT\",\"order_type\":\"limit\",\"side\":\"buy\",\"quantity\":\"1.0\",\"price\":\"60000.00\"}'
```

---

## 🔍 Can't find your Redis download?

**Search your Downloads folder:**
```powershell
Get-ChildItem -Path "$env:USERPROFILE\Downloads" -Recurse -Filter "*redis*" | Select-Object FullName
```

**Or search whole disk (slow):**
```powershell
Get-ChildItem -Path C:\ -Recurse -Filter "redis*.exe" -ErrorAction SilentlyContinue | Select-Object FullName
```

---

## 🆘 Still stuck?

Tell me:
1. Which version did you download? (Memurai / Redis ZIP / Docker)
2. Where did you extract/install it?
3. Any error messages?

I'll help you get it running!

