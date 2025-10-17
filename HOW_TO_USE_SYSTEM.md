# How to Use Your Trading System

Complete guide to interacting with your Order Gateway and Market Data services.

---

## Table of Contents

1. [Monitor Health](#1-monitor-health-easiest)
2. [Submit Orders](#2-submit-orders)
3. [Connect to WebSocket](#3-connect-to-websocket)
4. [View API Documentation](#4-view-api-documentation)
5. [Troubleshooting](#troubleshooting)

---

## 1. Monitor Health (EASIEST)

### Using Your Web Browser

Just open these URLs in your browser (Chrome, Firefox, Edge, etc.):

#### Order Gateway Health
```
http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "order-gateway",
  "redis": "connected"
}
```

#### Market Data Health
```
http://localhost:8001/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "market-data",
  "redis": "connected",
  "active_connections": 0
}
```

#### Market Data Stats
```
http://localhost:8001/stats
```

**Expected Response:**
```json
{
  "active_websocket_connections": 0,
  "service": "market-data",
  "version": "1.0.0"
}
```

### Using PowerShell

Open PowerShell and run:

```powershell
# Check Order Gateway
Invoke-RestMethod -Uri "http://localhost:8000/health" | ConvertTo-Json

# Check Market Data
Invoke-RestMethod -Uri "http://localhost:8001/health" | ConvertTo-Json
```

---

## 2. Submit Orders

### Method A: Using PowerShell (Recommended for Windows)

#### Submit a BUY LIMIT Order

```powershell
$order = @{
    side = "buy"
    order_type = "limit"
    price = "60000.00"
    quantity = "1.5"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/v1/orders" `
    -Method POST `
    -ContentType "application/json" `
    -Body $order
```

**Expected Response:**
```json
{
  "order_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "accepted",
  "message": "Order accepted and queued for processing"
}
```

#### Submit a SELL MARKET Order

```powershell
$order = @{
    side = "sell"
    order_type = "market"
    quantity = "0.5"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/v1/orders" `
    -Method POST `
    -ContentType "application/json" `
    -Body $order
```

#### Submit an IOC (Immediate-Or-Cancel) Order

```powershell
$order = @{
    side = "buy"
    order_type = "ioc"
    price = "59500.00"
    quantity = "2.0"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/v1/orders" `
    -Method POST `
    -ContentType "application/json" `
    -Body $order
```

#### Submit a FOK (Fill-Or-Kill) Order

```powershell
$order = @{
    side = "sell"
    order_type = "fok"
    price = "60500.00"
    quantity = "1.0"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/v1/orders" `
    -Method POST `
    -ContentType "application/json" `
    -Body $order
```

### Method B: Using curl (Cross-Platform)

If you have curl installed:

```bash
# BUY LIMIT Order
curl -X POST http://localhost:8000/v1/orders \
  -H "Content-Type: application/json" \
  -d '{
    "side": "buy",
    "order_type": "limit",
    "price": "60000.00",
    "quantity": "1.5"
  }'

# SELL MARKET Order
curl -X POST http://localhost:8000/v1/orders \
  -H "Content-Type: application/json" \
  -d '{
    "side": "sell",
    "order_type": "market",
    "quantity": "0.5"
  }'
```

### Method C: Using Postman (GUI Tool)

1. **Open Postman** (or install from https://www.postman.com/)

2. **Create a new request:**
   - Method: `POST`
   - URL: `http://localhost:8000/v1/orders`
   - Headers: `Content-Type: application/json`

3. **Body (raw JSON):**
   ```json
   {
     "side": "buy",
     "order_type": "limit",
     "price": "60000.00",
     "quantity": "1.5"
   }
   ```

4. **Click "Send"**

### Method D: Using Python Script

Create a file `submit_order.py`:

```python
import requests
import json

def submit_order(side, order_type, quantity, price=None):
    url = "http://localhost:8000/v1/orders"
    
    payload = {
        "side": side,
        "order_type": order_type,
        "quantity": quantity
    }
    
    if price:
        payload["price"] = price
    
    response = requests.post(url, json=payload)
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    return response.json()

# Examples
submit_order("buy", "limit", "1.5", "60000.00")
submit_order("sell", "market", "0.5")
submit_order("buy", "ioc", "2.0", "59500.00")
```

Run it:
```bash
python submit_order.py
```

---

## 3. Connect to WebSocket

### Method A: Using Online WebSocket Tester (EASIEST)

1. **Open your browser and go to:**
   ```
   https://www.websocket.org/echo.html
   ```
   OR
   ```
   https://websocketking.com/
   ```

2. **Enter the WebSocket URL:**
   ```
   ws://localhost:8001/ws/market-data
   ```

3. **Click "Connect"**

4. **You should see a welcome message:**
   ```json
   {
     "type": "connected",
     "message": "Connected to GoQuant Market Data Feed",
     "subscriptions": ["trades"]
   }
   ```

5. **Now submit an order (in another tab)** and watch for trade events!

### Method B: Using JavaScript in Browser Console

1. **Open your browser** (Chrome/Firefox)
2. **Press F12** to open Developer Tools
3. **Go to Console tab**
4. **Paste this code:**

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8001/ws/market-data');

// Connection opened
ws.addEventListener('open', (event) => {
    console.log('✅ Connected to Market Data Feed');
});

// Listen for messages
ws.addEventListener('message', (event) => {
    const data = JSON.parse(event.data);
    console.log('📊 Received:', data);
    
    if (data.type === 'trade') {
        console.log(`💰 TRADE: ${data.data.quantity} @ ${data.data.price}`);
        console.log(`   Trade ID: ${data.data.trade_id}`);
        console.log(`   Aggressor: ${data.data.aggressor_side}`);
    }
});

// Connection closed
ws.addEventListener('close', (event) => {
    console.log('❌ Disconnected from Market Data Feed');
});

// Error handling
ws.addEventListener('error', (error) => {
    console.error('⚠️ WebSocket error:', error);
});
```

5. **Press Enter**
6. **You should see:** `✅ Connected to Market Data Feed`

### Method C: Using Python WebSocket Client

Create a file `websocket_client.py`:

```python
import asyncio
import websockets
import json

async def listen_market_data():
    uri = "ws://localhost:8001/ws/market-data"
    
    async with websockets.connect(uri) as websocket:
        print("✅ Connected to Market Data Feed")
        
        # Receive messages
        while True:
            message = await websocket.receive()
            data = json.loads(message)
            
            print(f"\n📊 Received: {data['type']}")
            
            if data['type'] == 'trade':
                trade = data['data']
                print(f"   💰 TRADE: {trade['quantity']} @ ${trade['price']}")
                print(f"   Trade ID: {trade['trade_id']}")
                print(f"   Aggressor: {trade['aggressor_side']}")
            else:
                print(f"   {json.dumps(data, indent=2)}")

# Run the client
asyncio.run(listen_market_data())
```

Install websockets library:
```bash
pip install websockets
```

Run the client:
```bash
python websocket_client.py
```

### Method D: Using wscat (Command Line)

Install wscat:
```bash
npm install -g wscat
```

Connect:
```bash
wscat -c ws://localhost:8001/ws/market-data
```

---

## 4. View API Documentation

### Interactive API Docs (Swagger UI)

#### Order Gateway API Docs
```
http://localhost:8000/v1/docs
```

**What you can do:**
- 📖 View all endpoints
- 🧪 Test API directly in browser
- 📋 See request/response schemas
- 🔍 Try different order types

#### Market Data API Docs
```
http://localhost:8001/docs
```

**What you can do:**
- 📖 View WebSocket endpoint details
- 🧪 See message formats
- 📋 Check health endpoints

---

## Quick Test Scenario

### Scenario: Submit an order and see it in WebSocket

**Step 1:** Open WebSocket connection
```
1. Go to https://websocketking.com/
2. Connect to: ws://localhost:8001/ws/market-data
3. Wait for welcome message
```

**Step 2:** Submit an order (in PowerShell)
```powershell
$order = @{
    side = "buy"
    order_type = "limit"
    price = "60000.00"
    quantity = "1.5"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/v1/orders" `
    -Method POST `
    -ContentType "application/json" `
    -Body $order
```

**Step 3:** Watch for trade event in WebSocket!
```json
{
  "type": "trade",
  "data": {
    "trade_id": "T0001",
    "symbol": "BTC-USDT",
    "price": "60000.00",
    "quantity": "1.5",
    "aggressor_side": "buy",
    "timestamp": 1697380800
  }
}
```

---

## Troubleshooting

### "Unable to connect to remote server"

**Check if services are running:**
```powershell
# Check ports
netstat -ano | findstr ":8000"
netstat -ano | findstr ":8001"

# Check health
Invoke-RestMethod -Uri "http://localhost:8000/health"
Invoke-RestMethod -Uri "http://localhost:8001/health"
```

**Restart services if needed:**
```powershell
# Start Order Gateway
cd order-gateway
.\.venv\Scripts\Activate.ps1
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000

# Start Market Data (in another window)
cd market-data
.\.venv\Scripts\Activate.ps1
python -m uvicorn src.main:app --host 0.0.0.0 --port 8001
```

### "Connection refused" for WebSocket

Make sure Market Data service is running on port 8001:
```powershell
Invoke-RestMethod -Uri "http://localhost:8001/health"
```

### Order returns error 422

**Common causes:**
1. Missing required field (quantity, side)
2. Invalid price format (use string "60000.00", not number)
3. Invalid order_type (must be: market, limit, ioc, fok)

**Example valid order:**
```json
{
  "side": "buy",
  "order_type": "limit",
  "price": "60000.00",
  "quantity": "1.5"
}
```

---

## Summary of URLs

| Service | Endpoint | Purpose |
|---------|----------|---------|
| Order Gateway | http://localhost:8000/health | Health check |
| Order Gateway | http://localhost:8000/v1/orders | Submit orders (POST) |
| Order Gateway | http://localhost:8000/v1/docs | API documentation |
| Market Data | http://localhost:8001/health | Health check |
| Market Data | http://localhost:8001/stats | Service statistics |
| Market Data | http://localhost:8001/docs | API documentation |
| Market Data | ws://localhost:8001/ws/market-data | WebSocket feed |

---

**Need more help?** Check the logs in the PowerShell windows where services are running!

