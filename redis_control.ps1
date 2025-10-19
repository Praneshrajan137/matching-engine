# Redis Control Script for GoQuant
# Manages Redis Docker container for the matching engine system

param(
    [Parameter(Position=0)]
    [ValidateSet("start", "stop", "restart", "status", "logs", "clear")]
    [string]$Action = "status"
)

$ContainerName = "redis"
$RedisImage = "redis:7-alpine"
$RedisPort = 6379

function Write-Status {
    param($Message, $Type = "Info")
    $Color = switch($Type) {
        "Success" { "Green" }
        "Error" { "Red" }
        "Warning" { "Yellow" }
        default { "Cyan" }
    }
    Write-Host "[" -NoNewline
    Write-Host $Type.ToUpper() -ForegroundColor $Color -NoNewline
    Write-Host "] $Message"
}

function Test-DockerRunning {
    try {
        docker ps | Out-Null
        return $true
    } catch {
        return $false
    }
}

function Get-RedisStatus {
    if (-not (Test-DockerRunning)) {
        Write-Status "Docker is not running" "Error"
        Write-Status "Please start Docker Desktop and try again" "Warning"
        return $false
    }
    
    $container = docker ps -a --filter "name=^${ContainerName}$" --format "{{.Status}}"
    
    if ($container) {
        if ($container -like "Up*") {
            Write-Status "Redis is running" "Success"
            Write-Status "Container: $container" "Info"
            return $true
        } else {
            Write-Status "Redis container exists but is stopped" "Warning"
            Write-Status "Status: $container" "Info"
            return $false
        }
    } else {
        Write-Status "Redis container does not exist" "Warning"
        return $false
    }
}

function Start-RedisContainer {
    Write-Status "Starting Redis..." "Info"
    
    if (-not (Test-DockerRunning)) {
        Write-Status "Docker is not running. Please start Docker Desktop first." "Error"
        return
    }
    
    # Check if container exists
    $exists = docker ps -a --filter "name=^${ContainerName}$" --format "{{.Names}}"
    
    if ($exists) {
        Write-Status "Starting existing container..." "Info"
        docker start $ContainerName | Out-Null
    } else {
        Write-Status "Creating new Redis container..." "Info"
        docker run -d --name $ContainerName -p ${RedisPort}:6379 $RedisImage | Out-Null
    }
    
    Start-Sleep -Seconds 2
    
    if (Get-RedisStatus) {
        Write-Status "Redis started successfully" "Success"
        Write-Status "Testing connection..." "Info"
        
        try {
            python -c "import redis; r = redis.Redis(host='localhost', port=6379); print('✓ Connection test:', r.ping())"
            Write-Status "Redis is ready for GoQuant" "Success"
        } catch {
            Write-Status "Redis is running but connection test failed" "Warning"
        }
    } else {
        Write-Status "Failed to start Redis" "Error"
    }
}

function Stop-RedisContainer {
    Write-Status "Stopping Redis..." "Info"
    
    $exists = docker ps --filter "name=^${ContainerName}$" --format "{{.Names}}"
    
    if ($exists) {
        docker stop $ContainerName | Out-Null
        Write-Status "Redis stopped" "Success"
    } else {
        Write-Status "Redis is not running" "Warning"
    }
}

function Restart-RedisContainer {
    Write-Status "Restarting Redis..." "Info"
    Stop-RedisContainer
    Start-Sleep -Seconds 2
    Start-RedisContainer
}

function Show-RedisLogs {
    Write-Status "Showing Redis logs (Ctrl+C to exit)..." "Info"
    docker logs -f $ContainerName
}

function Clear-RedisData {
    Write-Status "Clearing Redis data..." "Warning"
    Write-Host "This will delete ALL data in Redis. Are you sure? (y/N): " -NoNewline -ForegroundColor Yellow
    $confirm = Read-Host
    
    if ($confirm -eq "y" -or $confirm -eq "Y") {
        try {
            python -c "import redis; r = redis.Redis(host='localhost', port=6379); r.flushall(); print('All Redis data cleared')"
            Write-Status "Redis data cleared successfully" "Success"
        } catch {
            Write-Status "Failed to clear Redis data. Is Redis running?" "Error"
        }
    } else {
        Write-Status "Operation cancelled" "Info"
    }
}

# Main script
Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  GoQuant Redis Control" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

switch ($Action) {
    "start" {
        Start-RedisContainer
    }
    "stop" {
        Stop-RedisContainer
    }
    "restart" {
        Restart-RedisContainer
    }
    "status" {
        Get-RedisStatus
    }
    "logs" {
        Show-RedisLogs
    }
    "clear" {
        Clear-RedisData
    }
}

Write-Host ""
Write-Host "Available commands:" -ForegroundColor Gray
Write-Host "  .\redis_control.ps1 start     - Start Redis" -ForegroundColor Gray
Write-Host "  .\redis_control.ps1 stop      - Stop Redis" -ForegroundColor Gray
Write-Host "  .\redis_control.ps1 restart   - Restart Redis" -ForegroundColor Gray
Write-Host "  .\redis_control.ps1 status    - Check status" -ForegroundColor Gray
Write-Host "  .\redis_control.ps1 logs      - View logs" -ForegroundColor Gray
Write-Host "  .\redis_control.ps1 clear     - Clear all data" -ForegroundColor Gray
Write-Host ""
