Param(
    [switch]$SkipMigrations
)

$ErrorActionPreference = "Stop"

function Load-EnvFile {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        throw ".env file not found at $Path"
    }

    Get-Content $Path | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith("#")) {
            return
        }
        $parts = $line.Split("=", 2)
        if ($parts.Count -ne 2) {
            return
        }
        $name = $parts[0].Trim()
        $value = $parts[1].Trim()
        [Environment]::SetEnvironmentVariable($name, $value, "Process")
    }
}

function Assert-RequiredEnv {
    $required = @("DATABASE_URL")
    foreach ($key in $required) {
        $value = [Environment]::GetEnvironmentVariable($key, "Process")
        if ([string]::IsNullOrWhiteSpace($value)) {
            throw "Missing required environment variable: $key"
        }
    }
}

function Test-DatabaseConnectivity {
    Write-Host "Checking database connectivity..."
    python -c "from database import engine; conn = engine.connect(); conn.close(); print('Database OK')" | Out-Host
}

function Run-Migrations {
    Write-Host "Applying migrations..."
    python "migrations/apply_migrations.py" | Out-Host
}

function Start-Api {
    $host = [Environment]::GetEnvironmentVariable("UVICORN_HOST", "Process")
    if ([string]::IsNullOrWhiteSpace($host)) { $host = "0.0.0.0" }

    $port = [Environment]::GetEnvironmentVariable("UVICORN_PORT", "Process")
    if ([string]::IsNullOrWhiteSpace($port)) { $port = "5001" }

    $logLevel = [Environment]::GetEnvironmentVariable("LOG_LEVEL", "Process")
    if ([string]::IsNullOrWhiteSpace($logLevel)) { $logLevel = "debug" }

    Write-Host "Starting API at http://${host}:${port} (log level: $logLevel)..."
    python "main.py"
}

try {
    $projectRoot = Split-Path -Parent $PSScriptRoot
    Set-Location $projectRoot

    Load-EnvFile -Path ".env"
    Assert-RequiredEnv
    Test-DatabaseConnectivity

    if (-not $SkipMigrations) {
        Run-Migrations
    } else {
        Write-Host "Skipping migrations due to -SkipMigrations."
    }

    Start-Api
}
catch {
    Write-Error $_.Exception.Message
    exit 1
}
