#!/usr/bin/env pwsh
#
# QUICK Performance Benchmark - 1 Minute Test
# Demonstrates >1000 orders/sec requirement
#

$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " QUICK PERFORMANCE TEST" -ForegroundColor Yellow
Write-Host " Target: >1000 orders/sec" -ForegroundColor Yellow
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$NumOrders = 2000  # Reasonable for quick test
$Concurrency = 100  # High concurrency for speed

Write-Host "Configuration:" -ForegroundColor White
Write-Host "  Orders:        $NumOrders"
Write-Host "  Concurrency:   $Concurrency parallel requests"
Write-Host "  Test Duration: ~30-60 seconds"
Write-Host ""

# Check services
Write-Host "Verifying services..." -ForegroundColor Yellow

if (!(netstat -ano | findstr ":6379" | Select-String "LISTENING")) {
    Write-Host "[ERROR] Redis not running!" -ForegroundColor Red
    exit 1
}
if (!(netstat -ano | findstr ":8000" | Select-String "LISTENING")) {
    Write-Host "[ERROR] Order Gateway not running!" -ForegroundColor Red
    exit 1
}

Write-Host "[OK] All services ready" -ForegroundColor Green
Write-Host ""

# Start C++ Engine
Write-Host "Starting C++ Matching Engine..." -ForegroundColor Yellow
$enginePath = "C:\Users\Pranesh\OneDrive\Music\Matching Engine\goquant\matching-engine\build\src\Debug\engine_runner.exe"
$engineJob = Start-Job -ScriptBlock {
    param($path)
    & $path
} -ArgumentList $enginePath

Start-Sleep -Seconds 3
Write-Host "[OK] Engine started" -ForegroundColor Green
Write-Host ""

# Run benchmark
Write-Host "Submitting $NumOrders orders..." -ForegroundColor Yellow
Write-Host ""

$url = "http://localhost:8000/v1/orders"
$startTime = Get-Date

$submitted = 0
$failed = 0

# Submit in parallel batches
for ($batch = 0; $batch -lt [Math]::Ceiling($NumOrders / $Concurrency); $batch++) {
    $jobs = @()
    
    for ($i = 0; $i -lt $Concurrency; $i++) {
        $orderIndex = $batch * $Concurrency + $i
        if ($orderIndex -ge $NumOrders) { break }
        
        $side = if ($orderIndex % 2 -eq 0) { "buy" } else { "sell" }
        $priceVar = ($orderIndex % 50) - 25
        $price = 60000 + $priceVar
        
        $order = @{
            symbol = "BTC-USDT"
            side = $side
            order_type = "limit"
            price = "$price.00"
            quantity = "0.1"
        } | ConvertTo-Json -Compress
        
        $jobs += Start-Job -ScriptBlock {
            param($url, $body)
            try {
                Invoke-RestMethod -Uri $url -Method POST -ContentType "application/json" -Body $body -TimeoutSec 10 -ErrorAction Stop | Out-Null
                return "ok"
            } catch {
                return "fail"
            }
        } -ArgumentList $url, $order
    }
    
    # Wait for batch
    $results = Wait-Job $jobs -Timeout 30 | Receive-Job
    Remove-Job $jobs -Force
    
    $submitted += ($results | Where-Object { $_ -eq "ok" }).Count
    $failed += ($results | Where-Object { $_ -eq "fail" }).Count
    
    Write-Host "  Batch $($batch+1): $submitted / $NumOrders submitted" -ForegroundColor Gray
}

$endTime = Get-Date
$totalSeconds = ($endTime - $startTime).TotalSeconds

Write-Host ""
Write-Host "[OK] Submission complete" -ForegroundColor Green
Write-Host ""

# Wait for processing
Write-Host "Waiting 3 seconds for engine to process..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# Stop engine
Stop-Job $engineJob -ErrorAction SilentlyContinue
$engineOutput = Receive-Job $engineJob
Remove-Job $engineJob -Force

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " RESULTS" -ForegroundColor Yellow
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$throughput = $submitted / $totalSeconds
$successRate = ($submitted / $NumOrders) * 100

Write-Host "Orders Submitted:    $submitted / $NumOrders" -ForegroundColor White
Write-Host "Success Rate:        $([math]::Round($successRate, 1))%" -ForegroundColor White
Write-Host "Failed:              $failed" -ForegroundColor White
Write-Host "Total Time:          $([math]::Round($totalSeconds, 2)) seconds" -ForegroundColor White
Write-Host ""
Write-Host "THROUGHPUT:          $([math]::Round($throughput, 0)) orders/sec" -ForegroundColor Yellow -BackgroundColor Black
Write-Host ""

# Verdict
if ($throughput -ge 2000) {
    Write-Host "[EXCELLENT] $([math]::Round($throughput, 0)) orders/sec - WORLD CLASS!" -ForegroundColor Green
    Write-Host ""
    Write-Host "This is 2x the requirement!" -ForegroundColor Green
} elseif ($throughput -ge 1000) {
    Write-Host "[PASS] $([math]::Round($throughput, 0)) orders/sec >= 1000 orders/sec" -ForegroundColor Green
    Write-Host ""
    Write-Host "Assignment requirement MET!" -ForegroundColor Green
} else {
    Write-Host "[FAIL] $([math]::Round($throughput, 0)) orders/sec < 1000 orders/sec" -ForegroundColor Red
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Show C++ engine stats
if ($engineOutput) {
    Write-Host "C++ Engine Output:" -ForegroundColor Cyan
    $engineOutput | Select-String -Pattern "STATS|Throughput|Processed" | ForEach-Object { Write-Host $_ }
}

