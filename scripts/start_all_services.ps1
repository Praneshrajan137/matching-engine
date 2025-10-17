# Start all goquant services
# Requires: Python 3.11+, Redis

param(
    [switch]$Help
)

if ($Help) {
    Write-Host @"
🚀 GoQuant Service Launcher
============================

This script starts all 3 services in separate PowerShell windows:
1. Order Gateway (FastAPI:8000)
2. Market Data (FastAPI:8001)
3. C++ Engine Runner (console app)

Prerequisites:
- Python 3.11+ installed
- Redis running (Memurai/WSL/Docker)
- Virtual environments created
- C++ engine built

Usage:
  .\start_all_services.ps1

To stop all services:
  Close all PowerShell windows or press Ctrl+C in each
"@
    exit
}

$workspaceRoot = "C:\Users\Pranesh\OneDrive\Music\Matching Engine\goquant"

Write-Host "🚀 Starting GoQuant Services..." -ForegroundColor Cyan
Write-Host ""

# Check Redis
Write-Host "Checking Redis connection..." -ForegroundColor Yellow
try {
    $redisCheck = redis-cli ping 2>&1
    if ($redisCheck -match "PONG") {
        Write-Host "✅ Redis is running" -ForegroundColor Green
    } else {
        Write-Host "❌ Redis not responding. Please start Redis first." -ForegroundColor Red
        Write-Host "   Memurai: net start Memurai" -ForegroundColor Gray
        Write-Host "   WSL: wsl redis-server --daemonize yes" -ForegroundColor Gray
        Write-Host "   Docker: docker start redis" -ForegroundColor Gray
        exit 1
    }
} catch {
    Write-Host "❌ redis-cli not found. Please install Redis." -ForegroundColor Red
    exit 1
}

Write-Host ""

# Start Order Gateway
Write-Host "Starting Order Gateway on port 8000..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList @"
    -NoExit
    -Command
    cd '$workspaceRoot\order-gateway' ;
    .\.venv\Scripts\Activate.ps1 ;
    uvicorn src.main:app --reload --port 8000
"@

Start-Sleep -Seconds 2

# Start Market Data
Write-Host "Starting Market Data on port 8001..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList @"
    -NoExit
    -Command
    cd '$workspaceRoot\market-data' ;
    .\.venv\Scripts\Activate.ps1 ;
    uvicorn src.main:app --reload --port 8001
"@

Start-Sleep -Seconds 2

# Start C++ Engine Runner
Write-Host "Starting C++ Engine Runner..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList @"
    -NoExit
    -Command
    cd '$workspaceRoot\matching-engine\build\Debug' ;
    .\engine_runner.exe
"@

Write-Host ""
Write-Host "✅ All services started!" -ForegroundColor Green
Write-Host ""
Write-Host "Service URLs:" -ForegroundColor Cyan
Write-Host "  Order Gateway API:  http://localhost:8000/v1/docs" -ForegroundColor Gray
Write-Host "  Market Data Stats:  http://localhost:8001/stats" -ForegroundColor Gray
Write-Host "  WebSocket:          ws://localhost:8001/ws/market-data" -ForegroundColor Gray
Write-Host ""
Write-Host "To test the system, run:" -ForegroundColor Cyan
Write-Host "  .\scripts\test_order_gateway.ps1" -ForegroundColor Gray

