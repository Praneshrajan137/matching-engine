#!/usr/bin/env pwsh
#
# C++ Matching Engine Performance Benchmark
# Tests end-to-end throughput with full Redis integration
#
# Architecture:
# PowerShell --> Order Gateway (REST) --> Redis Queue --> C++ Engine --> Redis PubSub --> Market Data
#

param(
    [int]$NumOrders = 5000,
    [int]$Concurrency = 50
)

$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " C++ MATCHING ENGINE BENCHMARK" -ForegroundColor Yellow
Write-Host " Full End-to-End Performance Test" -ForegroundColor Yellow
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Configuration:" -ForegroundColor White
Write-Host "  Total Orders:  $NumOrders"
Write-Host "  Concurrency:   $Concurrency requests in parallel"
Write-Host "  Target:        >1000 orders/sec"
Write-Host "  Goal:          >2000 orders/sec (world-class)" -ForegroundColor Green
Write-Host ""

# Step 1: Verify services are running
Write-Host "=== STEP 1: Verifying Services ===" -ForegroundColor Cyan
Write-Host ""

# Check Redis
if (netstat -ano | findstr ":6379" | Select-String "LISTENING") {
    Write-Host "[OK] Redis (6379)" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Redis NOT running!" -ForegroundColor Red
    Write-Host "Please start: docker run -d -p 6379:6379 redis" -ForegroundColor Yellow
    exit 1
}

# Check Order Gateway
if (netstat -ano | findstr ":8000" | Select-String "LISTENING") {
    Write-Host "[OK] Order Gateway (8000)" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Order Gateway NOT running!" -ForegroundColor Red
    Write-Host "Please start the Order Gateway first" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Step 2: Start C++ Engine
Write-Host "=== STEP 2: Starting C++ Matching Engine ===" -ForegroundColor Cyan
Write-Host ""

$enginePath = "C:\Users\Pranesh\OneDrive\Music\Matching Engine\goquant\matching-engine\build\src\Debug\engine_runner.exe"
$engineJob = Start-Job -ScriptBlock {
    param($path)
    & $path
} -ArgumentList $enginePath

Write-Host "Waiting 3 seconds for engine initialization..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

Write-Host "[OK] C++ Engine running (Job ID: $($engineJob.Id))" -ForegroundColor Green
Write-Host ""

# Step 3: Run benchmark
Write-Host "=== STEP 3: Submitting $NumOrders Orders ===" -ForegroundColor Cyan
Write-Host ""

$url = "http://localhost:8000/v1/orders"
$startTime = Get-Date

# Create order templates
$buyOrders = @()
$sellOrders = @()
for ($i = 0; $i -lt ($NumOrders / 2); $i++) {
    $priceVar = ($i % 100) - 50
    $price = 60000 + $priceVar
    
    $buyOrders += @{
        symbol = "BTC-USDT"
        side = "buy"
        order_type = "limit"
        price = "$price.00"
        quantity = "0.1"
    }
    
    $sellOrders += @{
        symbol = "BTC-USDT"
        side = "sell"
        order_type = "limit"
        price = "$price.00"
        quantity = "0.1"
    }
}

# Submit orders in parallel batches
$submitted = 0
$failed = 0
$batchSize = $Concurrency

Write-Host "Submitting orders in batches of $batchSize..." -ForegroundColor Yellow
Write-Host ""

$progressCounter = 0
for ($batch = 0; $batch -lt [Math]::Ceiling($NumOrders / $batchSize); $batch++) {
    $jobs = @()
    
    for ($i = 0; $i -lt $batchSize; $i++) {
        $orderIndex = $batch * $batchSize + $i
        if ($orderIndex -ge $NumOrders) { break }
        
        $order = if ($orderIndex % 2 -eq 0) { $buyOrders[$orderIndex / 2] } else { $sellOrders[$orderIndex / 2] }
        $body = $order | ConvertTo-Json -Compress
        
        $jobs += Start-Job -ScriptBlock {
            param($url, $body)
            try {
                Invoke-RestMethod -Uri $url -Method POST -ContentType "application/json" -Body $body -TimeoutSec 5 | Out-Null
                return "success"
            } catch {
                return "failed"
            }
        } -ArgumentList $url, $body
    }
    
    # Wait for batch to complete
    $results = Wait-Job $jobs | Receive-Job
    Remove-Job $jobs
    
    $submitted += ($results | Where-Object { $_ -eq "success" }).Count
    $failed += ($results | Where-Object { $_ -eq "failed" }).Count
    
    $progressCounter += $batchSize
    if ($progressCounter % 500 -eq 0 -or $progressCounter -ge $NumOrders) {
        Write-Host "  Progress: $progressCounter / $NumOrders" -ForegroundColor Gray
    }
}

$endTime = Get-Date
$totalSeconds = ($endTime - $startTime).TotalSeconds

Write-Host ""
Write-Host "[OK] Submission complete" -ForegroundColor Green
Write-Host ""

# Step 4: Wait for C++ engine to process
Write-Host "=== STEP 4: Waiting for C++ Engine Processing ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Allowing 5 seconds for engine to drain queue..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Step 5: Stop C++ engine and get stats
Write-Host ""
Write-Host "=== STEP 5: Stopping C++ Engine ===" -ForegroundColor Cyan
Write-Host ""

Stop-Job $engineJob
$engineOutput = Receive-Job $engineJob
Remove-Job $engineJob

Write-Host "C++ Engine Output:" -ForegroundColor White
Write-Host $engineOutput
Write-Host ""

# Step 6: Calculate and display results
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " BENCHMARK RESULTS" -ForegroundColor Yellow
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$throughput = $submitted / $totalSeconds

Write-Host "Orders Submitted:    $submitted / $NumOrders" -ForegroundColor White
Write-Host "Failed:              $failed" -ForegroundColor White
Write-Host "Success Rate:        $([math]::Round($submitted / $NumOrders * 100, 1))%" -ForegroundColor White
Write-Host "Total Time:          $([math]::Round($totalSeconds, 2)) seconds" -ForegroundColor White
Write-Host ""
Write-Host "THROUGHPUT:          $([math]::Round($throughput, 0)) orders/sec" -ForegroundColor Yellow -BackgroundColor Black
Write-Host ""

if ($throughput -ge 2000) {
    Write-Host "[EXCELLENT] $([math]::Round($throughput, 0)) orders/sec - WORLD CLASS!" -ForegroundColor Green
    Write-Host "Far exceeds >1000 orders/sec requirement" -ForegroundColor Green
} elseif ($throughput -ge 1000) {
    Write-Host "[PASS] $([math]::Round($throughput, 0)) orders/sec >= 1000 orders/sec" -ForegroundColor Green
    Write-Host "Assignment requirement MET!" -ForegroundColor Green
} else {
    Write-Host "[FAIL] $([math]::Round($throughput, 0)) orders/sec < 1000 orders/sec" -ForegroundColor Red
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Extract C++ engine stats from output
if ($engineOutput -match "Average Throughput: (\d+) orders/sec") {
    $cppThroughput = $Matches[1]
    Write-Host "C++ Engine Internal Throughput: $cppThroughput orders/sec" -ForegroundColor Cyan
    Write-Host ""
}

