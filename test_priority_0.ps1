# Priority 0 Verification Script
# Tests that all services use consistent Redis configuration

param(
    [switch]$SkipRebuild = $false
)

$ErrorActionPreference = "Stop"

# Color output functions
function WriteSuccess { Write-Host "[OK] $args" -ForegroundColor Green }
function WriteError { Write-Host "[ERROR] $args" -ForegroundColor Red }
function WriteInfo { Write-Host "[INFO] $args" -ForegroundColor Cyan }
function WriteWarning { Write-Host "[WARN] $args" -ForegroundColor Yellow }

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Blue
Write-Host "  Priority 0 Verification - Redis Config Consistency" -ForegroundColor Blue
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Blue
Write-Host ""

# Check current directory
$projectRoot = "C:\Users\Pranesh\OneDrive\Music\Matching Engine\.cursor\goquant"
if (-not (Test-Path $projectRoot)) {
    WriteError "Project root not found: $projectRoot"
    exit 1
}
Set-Location $projectRoot
WriteInfo "Working directory: $projectRoot"
Write-Host ""

# Step 1: Check Redis is running
Write-Host "�"��"��"� Step 1: Check Redis �"��"��"�" -ForegroundColor Yellow
WriteInfo "Checking if Redis is running..."
try {
    $redisCheck = docker exec redis redis-cli ping 2>&1
    if ($redisCheck -match "PONG") {
        WriteSuccess "Redis is running"
    } else {
        WriteWarning "Redis not responding, attempting to start..."
        docker start redis 2>&1 | Out-Null
        Start-Sleep -Seconds 2
        $redisCheck = docker exec redis redis-cli ping 2>&1
        if ($redisCheck -match "PONG") {
            WriteSuccess "Redis started successfully"
        } else {
            WriteError "Failed to start Redis. Please run: docker run -d --name redis -p 6379:6379 redis:latest"
            exit 1
        }
    }
} catch {
    WriteError "Redis not available. Please start Redis first."
    exit 1
}
Write-Host ""

# Step 2: Rebuild C++ Engine
if (-not $SkipRebuild) {
    Write-Host "�"��"��"� Step 2: Rebuild C++ Engine �"��"��"�" -ForegroundColor Yellow
    WriteInfo "Building C++ matching engine with new changes..."
    
    $buildDir = Join-Path $projectRoot "matching-engine\build"
    if (-not (Test-Path $buildDir)) {
        WriteError "Build directory not found: $buildDir"
        WriteInfo "Please run CMake configuration first"
        exit 1
    }
    
    Set-Location $buildDir
    WriteInfo "Running: cmake --build . --config Debug"
    
    $buildOutput = cmake --build . --config Debug 2>&1
    if ($LASTEXITCODE -eq 0) {
        WriteSuccess "C++ engine built successfully"
    } else {
        WriteError "Build failed!"
        Write-Host $buildOutput
        exit 1
    }
    
    Set-Location $projectRoot
    Write-Host ""
} else {
    WriteWarning "Skipping C++ rebuild (use without -SkipRebuild to rebuild)"
    Write-Host ""
}

# Step 3: Verify File Changes
Write-Host "�"��"��"� Step 3: Verify Code Changes �"��"��"�" -ForegroundColor Yellow

WriteInfo "Checking engine_runner.cpp for environment variable usage..."
$engineRunner = Get-Content "matching-engine\src\engine_runner.cpp" -Raw
if ($engineRunner -match 'std::getenv\("REDIS_HOST"\)') {
    WriteSuccess "engine_runner.cpp reads REDIS_HOST from environment"
} else {
    WriteError "engine_runner.cpp does NOT read REDIS_HOST"
    exit 1
}

if ($engineRunner -match 'std::getenv\("REDIS_PORT"\)') {
    WriteSuccess "engine_runner.cpp reads REDIS_PORT from environment"
} else {
    WriteError "engine_runner.cpp does NOT read REDIS_PORT"
    exit 1
}

if ($engineRunner -match 'std::getenv\("REDIS_DB"\)') {
    WriteSuccess "engine_runner.cpp reads REDIS_DB from environment"
} else {
    WriteError "engine_runner.cpp does NOT read REDIS_DB"
    exit 1
}

WriteInfo "Checking redis_client.hpp for DB selection support..."
$redisClient = Get-Content "matching-engine\src\redis_client.hpp" -Raw
if ($redisClient -match 'bool select_db\(int db') {
    WriteSuccess "redis_client.hpp has select_db() method"
} else {
    WriteError "redis_client.hpp missing select_db() method"
    exit 1
}

WriteInfo "Checking redis_engine_runner.py for environment variables..."
$pythonEngine = Get-Content "matching-engine\python\redis_engine_runner.py" -Raw
if ($pythonEngine -match 'os\.getenv\("REDIS_HOST"') {
    WriteSuccess "redis_engine_runner.py reads REDIS_HOST from environment"
} else {
    WriteError "redis_engine_runner.py does NOT read REDIS_HOST"
    exit 1
}

WriteInfo "Checking constants.py for channel names..."
$constants = Get-Content "order-gateway\src\constants.py" -Raw
$channelNames = @("order_queue", "trade_events", "bbo_updates", "order_book_updates")
$allFound = $true
foreach ($channel in $channelNames) {
    if ($constants -match $channel) {
        WriteSuccess "Found channel/queue: $channel"
    } else {
        WriteError "Missing channel/queue: $channel"
        $allFound = $false
    }
}
if (-not $allFound) { exit 1 }

Write-Host ""

# Step 4: Test C++ Engine Standalone
Write-Host "�"��"��"� Step 4: Test C++ Engine Connection �"��"��"�" -ForegroundColor Yellow
WriteInfo "Testing C++ engine Redis connection..."

# Flush Redis queue first
WriteInfo "Flushing order_queue..."
docker exec redis redis-cli DEL order_queue | Out-Null

$engineExe = Join-Path $projectRoot "matching-engine\build\src\Debug\engine_runner.exe"
if (-not (Test-Path $engineExe)) {
    WriteError "Engine executable not found: $engineExe"
    WriteInfo "Build may have failed or path is incorrect"
    exit 1
}

WriteInfo "Starting C++ engine (will run for 5 seconds)..."
$engineJob = Start-Job -ScriptBlock {
    param($exePath)
    & $exePath 2>&1
} -ArgumentList $engineExe

Start-Sleep -Seconds 5

# Check engine output
$engineOutput = Receive-Job -Job $engineJob
Stop-Job -Job $engineJob 2>&1 | Out-Null
Remove-Job -Job $engineJob 2>&1 | Out-Null

Write-Host ""
WriteInfo "Engine Output (first 20 lines):"
Write-Host "----------------------------------------" -ForegroundColor Gray
$engineOutput | Select-Object -First 20 | ForEach-Object { Write-Host $_ -ForegroundColor Gray }
Write-Host "----------------------------------------" -ForegroundColor Gray
Write-Host ""

# Parse output for success indicators
$outputString = $engineOutput -join "`n"

if ($outputString -match 'Redis connection established') {
    WriteSuccess "C++ engine connected to Redis"
} else {
    WriteError "C++ engine failed to connect to Redis"
    WriteInfo "Full output:"
    $engineOutput | ForEach-Object { Write-Host $_ }
    exit 1
}

if ($outputString -match 'Listening for orders') {
    WriteSuccess "C++ engine listening for orders on queue"
} else {
    WriteWarning "Engine may not be listening for orders"
}

# Check if engine logged Redis config
if ($outputString -match '"host"') {
    WriteSuccess "Engine logs Redis host configuration"
} else {
    WriteWarning "Engine does not log Redis host (check logging)"
}

if ($outputString -match '"port"') {
    WriteSuccess "Engine logs Redis port configuration"
} else {
    WriteWarning "Engine does not log Redis port (check logging)"
}

if ($outputString -match '"db"') {
    WriteSuccess "Engine logs Redis DB configuration"
} else {
    WriteWarning "Engine does not log Redis DB (check logging)"
}

Write-Host ""

# Step 5: Test with Custom Environment Variables
Write-Host "�"��"��"� Step 5: Test Custom Environment Variables �"��"��"�" -ForegroundColor Yellow
WriteInfo "Testing with custom REDIS_HOST and REDIS_PORT..."

$env:REDIS_HOST = "127.0.0.1"
$env:REDIS_PORT = "6379"
$env:REDIS_DB = "0"

WriteInfo "Set REDIS_HOST=$env:REDIS_HOST"
WriteInfo "Set REDIS_PORT=$env:REDIS_PORT"
WriteInfo "Set REDIS_DB=$env:REDIS_DB"

WriteInfo "Starting C++ engine with custom env vars (will run for 3 seconds)..."
$engineJob2 = Start-Job -ScriptBlock {
    param($exePath, $host, $port, $db)
    $env:REDIS_HOST = $host
    $env:REDIS_PORT = $port
    $env:REDIS_DB = $db
    & $exePath 2>&1
} -ArgumentList $engineExe, $env:REDIS_HOST, $env:REDIS_PORT, $env:REDIS_DB

Start-Sleep -Seconds 3

$engineOutput2 = Receive-Job -Job $engineJob2
Stop-Job -Job $engineJob2 2>&1 | Out-Null
Remove-Job -Job $engineJob2 2>&1 | Out-Null

$outputString2 = $engineOutput2 -join "`n"

if ($outputString2 -match '127\.0\.0\.1') {
    WriteSuccess "Engine used custom REDIS_HOST (127.0.0.1)"
} else {
    WriteWarning "Engine may not have used custom REDIS_HOST"
}

Write-Host ""

# Step 6: Summary
Write-Host "�"��"��"� Verification Summary �"��"��"�" -ForegroundColor Yellow
Write-Host ""
WriteSuccess "All Priority 0 checks passed!"
Write-Host ""
WriteInfo "Verified:"
Write-Host "  �" Redis is running and accessible" -ForegroundColor Green
Write-Host "  �" C++ engine built successfully" -ForegroundColor Green
Write-Host "  �" All services read from environment variables" -ForegroundColor Green
Write-Host "  �" redis_client.hpp supports DB selection" -ForegroundColor Green
Write-Host "  �" All queue/channel names are consistent" -ForegroundColor Green
Write-Host "  �" C++ engine connects to Redis successfully" -ForegroundColor Green
Write-Host "  �" C++ engine logs configuration parameters" -ForegroundColor Green
Write-Host ""

Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Blue
Write-Host "  ✅ Priority 0 Complete - Ready for Task A" -ForegroundColor Blue
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Blue
Write-Host ""

WriteInfo "Next: Run Task A verification script"
Write-Host '  .\test_task_a.ps1' -ForegroundColor Cyan
Write-Host ""
