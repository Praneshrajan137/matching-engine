# Quick Start Commands - Copy & Paste

**All systems operational! Use these commands to interact with your trading system.**

---

## 📊 1. Monitor Health (Browser)

Just open these URLs in your browser:

```
http://localhost:8000/health
http://localhost:8001/health
http://localhost:8000/v1/docs
```

**Or in PowerShell:**

```powershell
# Check all services
Invoke-RestMethod -Uri "http://localhost:8000/health" | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8001/health" | ConvertTo-Json
```

---

## 📝 2. Submit Orders (PowerShell)

### BUY LIMIT Order

```powershell
$order = @{
    symbol = "BTC-USDT"
    side = "buy"
    order_type = "limit"
    price = "60000.00"
    quantity = "1.5"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/v1/orders" -Method POST -ContentType "application/json" -Body $order
```

### SELL MARKET Order

```powershell
$order = @{
    symbol = "BTC-USDT"
    side = "sell"
    order_type = "market"
    quantity = "0.5"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/v1/orders" -Method POST -ContentType "application/json" -Body $order
```

### IOC (Immediate-Or-Cancel) Order

```powershell
$order = @{
    symbol = "BTC-USDT"
    side = "buy"
    order_type = "ioc"
    price = "59500.00"
    quantity = "2.0"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/v1/orders" -Method POST -ContentType "application/json" -Body $order
```

### FOK (Fill-Or-Kill) Order

```powershell
$order = @{
    symbol = "BTC-USDT"
    side = "sell"
    order_type = "fok"
    price = "60500.00"
    quantity = "1.0"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/v1/orders" -Method POST -ContentType "application/json" -Body $order
```

---

## 🌐 3. WebSocket Connection

### Method A: Beautiful HTML Viewer (EASIEST)

```powershell
# Open the WebSocket test page
Start-Process "C:\Users\Pranesh\OneDrive\Music\Matching Engine\goquant\websocket_test.html"
```

Then click the **"Connect"** button!

### Method B: JavaScript in Browser Console

1. Open browser and press **F12**
2. Go to **Console** tab
3. Paste this code:

```javascript
const ws = new WebSocket('ws://localhost:8001/ws/market-data');

ws.onopen = () => console.log('✅ Connected!');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('📊 Received:', data);
    
    if (data.type === 'trade') {
        console.log(`💰 TRADE: ${data.data.quantity} @ $${data.data.price}`);
    }
};
```

### Method C: Online WebSocket Tester

1. Go to https://websocketking.com/
2. Enter URL: `ws://localhost:8001/ws/market-data`
3. Click **"Connect"**

---

## 🧪 4. Full Integration Test

### Step 1: Open WebSocket (in browser)

```
http://websocketking.com/
Connect to: ws://localhost:8001/ws/market-data
```

### Step 2: Submit Test Orders (in PowerShell)

```powershell
# Create matching BUY and SELL orders
$buy = @{
    symbol = "BTC-USDT"
    side = "buy"
    order_type = "limit"
    price = "60000.00"
    quantity = "1.0"
} | ConvertTo-Json

$sell = @{
    symbol = "BTC-USDT"
    side = "sell"
    order_type = "limit"
    price = "60000.00"
    quantity = "1.0"
} | ConvertTo-Json

# Submit BUY order
Invoke-RestMethod -Uri "http://localhost:8000/v1/orders" -Method POST -ContentType "application/json" -Body $buy

# Submit SELL order (will match!)
Invoke-RestMethod -Uri "http://localhost:8000/v1/orders" -Method POST -ContentType "application/json" -Body $sell
```

### Step 3: Watch Trade Event in WebSocket!

You should see:

```json
{
  "type": "trade",
  "data": {
    "trade_id": "T0001",
    "symbol": "BTC-USDT",
    "price": "60000.00",
    "quantity": "1.0",
    "aggressor_side": "sell"
  }
}
```

---

## 🔧 5. Troubleshooting Commands

### Check if services are running

```powershell
# Check ports
netstat -ano | findstr ":8000"  # Order Gateway
netstat -ano | findstr ":8001"  # Market Data
netstat -ano | findstr ":6379"  # Redis

# Test health
try {
    Invoke-RestMethod -Uri "http://localhost:8000/health"
    Write-Host "✅ Order Gateway: RUNNING" -ForegroundColor Green
} catch {
    Write-Host "❌ Order Gateway: NOT RUNNING" -ForegroundColor Red
}

try {
    Invoke-RestMethod -Uri "http://localhost:8001/health"
    Write-Host "✅ Market Data: RUNNING" -ForegroundColor Green
} catch {
    Write-Host "❌ Market Data: NOT RUNNING" -ForegroundColor Red
}
```

### Restart services if needed

```powershell
# Terminal 1: Redis
docker start redis

# Terminal 2: Order Gateway
cd "C:\Users\Pranesh\OneDrive\Music\Matching Engine\goquant\order-gateway"
.\.venv\Scripts\Activate.ps1
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000

# Terminal 3: Market Data
cd "C:\Users\Pranesh\OneDrive\Music\Matching Engine\goquant\market-data"
.\.venv\Scripts\Activate.ps1
python -m uvicorn src.main:app --host 0.0.0.0 --port 8001
```

---

## 📚 6. API Documentation

### Interactive Swagger UI (try API in browser)

```
http://localhost:8000/v1/docs   <- Order Gateway API
http://localhost:8001/docs      <- Market Data API
```

**What you can do:**
- 🔍 View all endpoints
- 🧪 Test API directly in browser
- 📋 See request/response schemas
- 💾 Download OpenAPI spec

---

## 📖 7. More Information

- **Complete Guide:** `HOW_TO_USE_SYSTEM.md`
- **WebSocket Viewer:** `websocket_test.html`
- **Fix Documentation:** `MARKET_DATA_FIX_SUMMARY.md`
- **Integration Report:** `INTEGRATION_TEST_REPORT.md`

---

## ✅ Quick Status Check

```powershell
Write-Host "=== SYSTEM STATUS ===" -ForegroundColor Cyan

$og = try { Invoke-RestMethod "http://localhost:8000/health" -TimeoutSec 2 } catch { $null }
$md = try { Invoke-RestMethod "http://localhost:8001/health" -TimeoutSec 2 } catch { $null }

if ($og) { Write-Host "✅ Order Gateway (8000): $($og.status)" -ForegroundColor Green } 
else { Write-Host "❌ Order Gateway (8000): NOT RUNNING" -ForegroundColor Red }

if ($md) { Write-Host "✅ Market Data (8001): $($md.status)" -ForegroundColor Green } 
else { Write-Host "❌ Market Data (8001): NOT RUNNING" -ForegroundColor Red }

if ((netstat -ano | findstr ":6379")) { Write-Host "✅ Redis (6379): RUNNING" -ForegroundColor Green } 
else { Write-Host "❌ Redis (6379): NOT RUNNING" -ForegroundColor Red }

Write-Host "===================" -ForegroundColor Cyan
```

---

**🎉 You're all set! Start by opening the WebSocket viewer and submitting test orders!**

