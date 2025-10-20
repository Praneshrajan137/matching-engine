# Benchmark Runner Script
# Runs performance benchmark with optimized settings

param(
    [int]$Workers = 4,
    [int]$Orders = 1000,
    [int]$Threads = 4
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Blue
Write-Host "  GoQuant Performance Benchmark Runner" -ForegroundColor Blue
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Blue
Write-Host ""

$projectRoot = "C:\Users\Pranesh\OneDrive\Music\Matching Engine\.cursor\goquant"
Set-Location $projectRoot

# Check Redis
Write-Host "Checking Redis..." -ForegroundColor Cyan
$redisCheck = docker exec redis redis-cli ping 2>&1
if ($redisCheck -notmatch "PONG") {
    Write-Host "❌ Redis not running. Starting..." -ForegroundColor Red
    docker start redis 2>&1 | Out-Null
    Start-Sleep -Seconds 2
}
Write-Host "✅ Redis is running" -ForegroundColor Green

# Set optimized environment
$env:UVICORN_WORKERS = $Workers
$env:LOG_LEVEL = "WARNING"
Write-Host "✅ Environment configured: $Workers workers, WARNING log level" -ForegroundColor Green
Write-Host ""

# Check if services are already running
$gatewayRunning = $false
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 2 -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        $gatewayRunning = $true
    }
} catch {}

if ($gatewayRunning) {
    Write-Host "✅ Order Gateway already running" -ForegroundColor Green
} else {
    Write-Host "Starting Order Gateway with $Workers workers..." -ForegroundColor Cyan
    $gateway_dir = Join-Path $projectRoot "order-gateway"
    
    $gatewayProcess = Start-Process python -ArgumentList "-m","uvicorn","src.main:app","--host","0.0.0.0","--port","8000","--workers","$Workers","--log-level","warning" `
        -WorkingDirectory $gateway_dir `
        -PassThru -NoNewWindow
    
    Write-Host "Waiting for Order Gateway to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    
    # Verify started
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 2
        Write-Host "✅ Order Gateway started successfully" -ForegroundColor Green
    } catch {
        Write-Host "❌ Failed to start Order Gateway" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "Starting benchmark..." -ForegroundColor Cyan
Write-Host "  Orders: $Orders" -ForegroundColor Gray
Write-Host "  Threads: $Threads" -ForegroundColor Gray
Write-Host ""

# Run benchmark
cd benchmark
python performance_test.py

# Cleanup (only if we started it)
if (-not $gatewayRunning -and $gatewayProcess) {
    Write-Host ""
    Write-Host "Stopping Order Gateway..." -ForegroundColor Yellow
    Stop-Process -Id $gatewayProcess.Id -Force -ErrorAction SilentlyContinue
    Write-Host "✅ Cleanup complete" -ForegroundColor Green
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Blue
Write-Host "  Benchmark Complete" -ForegroundColor Blue
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Blue
Write-Host ""
