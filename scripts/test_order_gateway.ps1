# Test script for Order Gateway API
# Tests all endpoints without requiring Redis

Write-Host "🧪 Testing Order Gateway API" -ForegroundColor Cyan
Write-Host "=============================" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://localhost:8000"

# Test 1: Health Check
Write-Host "Test 1: Health Check" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/health" -Method Get
    Write-Host "✅ Health check passed" -ForegroundColor Green
    Write-Host "   Status: $($response.status)" -ForegroundColor Gray
} catch {
    Write-Host "❌ Health check failed: $_" -ForegroundColor Red
}

Write-Host ""

# Test 2: Valid Market Order
Write-Host "Test 2: Submit Valid Market Order" -ForegroundColor Yellow
$order1 = @{
    symbol = "BTC-USDT"
    order_type = "market"
    side = "buy"
    quantity = "1.5"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/v1/orders" -Method Post `
        -ContentType "application/json" -Body $order1
    Write-Host "✅ Market order accepted" -ForegroundColor Green
    Write-Host "   Order ID: $($response.order_id)" -ForegroundColor Gray
} catch {
    Write-Host "❌ Market order failed: $_" -ForegroundColor Red
}

Write-Host ""

# Test 3: Valid Limit Order
Write-Host "Test 3: Submit Valid Limit Order" -ForegroundColor Yellow
$order2 = @{
    symbol = "BTC-USDT"
    order_type = "limit"
    side = "sell"
    quantity = "2.0"
    price = "60000.00"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/v1/orders" -Method Post `
        -ContentType "application/json" -Body $order2
    Write-Host "✅ Limit order accepted" -ForegroundColor Green
    Write-Host "   Order ID: $($response.order_id)" -ForegroundColor Gray
} catch {
    Write-Host "❌ Limit order failed: $_" -ForegroundColor Red
}

Write-Host ""

# Test 4: Invalid Order (market with price)
Write-Host "Test 4: Invalid Order (market with price)" -ForegroundColor Yellow
$order3 = @{
    symbol = "BTC-USDT"
    order_type = "market"
    side = "buy"
    quantity = "1.0"
    price = "60000.00"  # Invalid for market
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/v1/orders" -Method Post `
        -ContentType "application/json" -Body $order3 -ErrorAction Stop
    Write-Host "❌ Should have rejected invalid order" -ForegroundColor Red
} catch {
    if ($_.Exception.Response.StatusCode -eq 422) {
        Write-Host "✅ Correctly rejected with 422 Validation Error" -ForegroundColor Green
    } else {
        Write-Host "❌ Wrong error code: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "✅ Test suite complete!" -ForegroundColor Green

