# Setup Python virtual environments for all services
# Run this script after installing Python 3.11+

param(
    [switch]$Help
)

if ($Help) {
    Write-Host @"
🐍 Python Environment Setup
============================

This script creates virtual environments and installs dependencies for:
- Order Gateway
- Market Data Service

Prerequisites:
- Python 3.11+ installed and in PATH

Usage:
  .\setup_python_env.ps1
"@
    exit
}

$workspaceRoot = "C:\Users\Pranesh\OneDrive\Music\Matching Engine\goquant"

Write-Host "🐍 Setting up Python environments..." -ForegroundColor Cyan
Write-Host ""

# Check Python version
Write-Host "Checking Python version..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Found: $pythonVersion" -ForegroundColor Green
    
    if ($pythonVersion -notmatch "Python 3\.(1[1-9]|[2-9]\d)") {
        Write-Host "⚠️  Warning: Python 3.11+ recommended" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Python not found. Please install Python 3.11+" -ForegroundColor Red
    Write-Host "   Download from: https://www.python.org/downloads/" -ForegroundColor Gray
    exit 1
}

Write-Host ""

# Setup Order Gateway
Write-Host "Setting up Order Gateway..." -ForegroundColor Yellow
Push-Location "$workspaceRoot\order-gateway"

if (Test-Path ".venv") {
    Write-Host "  Virtual environment already exists, skipping..." -ForegroundColor Gray
} else {
    Write-Host "  Creating virtual environment..." -ForegroundColor Gray
    python -m venv .venv
}

Write-Host "  Installing dependencies..." -ForegroundColor Gray
& .\.venv\Scripts\Activate.ps1
pip install -q --upgrade pip
pip install -q -r requirements.txt

Write-Host "✅ Order Gateway ready" -ForegroundColor Green

Pop-Location
Write-Host ""

# Setup Market Data
Write-Host "Setting up Market Data..." -ForegroundColor Yellow
Push-Location "$workspaceRoot\market-data"

if (Test-Path ".venv") {
    Write-Host "  Virtual environment already exists, skipping..." -ForegroundColor Gray
} else {
    Write-Host "  Creating virtual environment..." -ForegroundColor Gray
    python -m venv .venv
}

Write-Host "  Installing dependencies..." -ForegroundColor Gray
& .\.venv\Scripts\Activate.ps1
pip install -q --upgrade pip
pip install -q -r requirements.txt

Write-Host "✅ Market Data ready" -ForegroundColor Green

Pop-Location
Write-Host ""

Write-Host "✅ All Python environments configured!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Install Redis (see REDIS_SETUP_WINDOWS.md)" -ForegroundColor Gray
Write-Host "2. Build C++ engine: cd matching-engine\build && cmake .. && cmake --build ." -ForegroundColor Gray
Write-Host "3. Start services: .\scripts\start_all_services.ps1" -ForegroundColor Gray

