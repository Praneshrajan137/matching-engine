# Quick Performance Benchmark - PowerShell Version
# Tests order submission throughput

$NUM_ORDERS = 1000
$URL = "http://localhost:8000/v1/orders"

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "PERFORMANCE BENCHMARK" -ForegroundColor Yellow
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Testing: $NUM_ORDERS orders"
Write-Host "Target:  >1000 orders/sec"
Write-Host ""

# Check connection
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 2
    Write-Host "[OK] Order Gateway is running" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Order Gateway not running" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Starting benchmark..." -ForegroundColor Yellow
Write-Host ""

$startTime = Get-Date
$success = 0
$failed = 0

for ($i = 0; $i -lt $NUM_ORDERS; $i++) {
    $side = if ($i % 2 -eq 0) { "buy" } else { "sell" }
    $priceVar = ($i % 100) - 50
    $price = 60000 + $priceVar
    
    $order = @{
        symbol = "BTC-USDT"
        side = $side
        order_type = "limit"
        price = "$price.00"
        quantity = "0.1"
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri $URL -Method POST -ContentType "application/json" -Body $order -TimeoutSec 5
        $success++
    } catch {
        $failed++
    }
    
    if (($i + 1) % 100 -eq 0) {
        Write-Host "  Progress: $($i+1)/$NUM_ORDERS"
    }
}

$endTime = Get-Date
$totalTime = ($endTime - $startTime).TotalSeconds
$throughput = $NUM_ORDERS / $totalTime

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "RESULTS" -ForegroundColor Yellow
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Total Time:    $([math]::Round($totalTime, 2)) seconds"
Write-Host "Throughput:    $([math]::Round($throughput, 2)) orders/sec"
Write-Host "Success:       $success/$NUM_ORDERS ($([math]::Round($success/$NUM_ORDERS*100, 1))%)"
Write-Host "Failed:        $failed"
Write-Host ""

if ($throughput -ge 1000) {
    Write-Host "[PASS] $([math]::Round($throughput, 0)) orders/sec >= 1000 orders/sec" -ForegroundColor Green
    Write-Host "Assignment requirement MET!" -ForegroundColor Green
} else {
    Write-Host "[FAIL] $([math]::Round($throughput, 0)) orders/sec < 1000 orders/sec" -ForegroundColor Red
    Write-Host "Assignment requirement NOT MET" -ForegroundColor Red
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

