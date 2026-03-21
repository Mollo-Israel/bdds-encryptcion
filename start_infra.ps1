# =============================================================
# start_infra.ps1
# Levanta SOLO la infraestructura Docker y espera motores listos
# Ejecutar desde la raíz: .\start_infra.ps1
# =============================================================

$root = Split-Path -Parent $MyInvocation.MyCommand.Path

function Wait-Port {
    param(
        [string]$TargetHost = "localhost",
        [int]$Port,
        [int]$TimeoutSeconds = 180,
        [int]$SleepSeconds = 2
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)

    while ((Get-Date) -lt $deadline) {
        try {
            $client = New-Object System.Net.Sockets.TcpClient
            $iar = $client.BeginConnect($TargetHost, $Port, $null, $null)
            $ok = $iar.AsyncWaitHandle.WaitOne(1000, $false)
            if ($ok -and $client.Connected) {
                $client.EndConnect($iar)
                $client.Close()
                Write-Host "      ${TargetHost}:$Port OK" -ForegroundColor Green
                return $true
            }
            $client.Close()
        } catch {}
        Start-Sleep -Seconds $SleepSeconds
    }

    Write-Host "      ${TargetHost}:$Port TIMEOUT" -ForegroundColor Red
    return $false
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  BDDS - LEVANTANDO SOLO INFRAESTRUCTURA" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Docker up
Write-Host "[1/4] Levantando contenedores Docker..." -ForegroundColor Yellow
Push-Location (Join-Path $root "docker")
docker compose up -d
if ($LASTEXITCODE -ne 0) {
    Pop-Location
    Write-Error "docker compose up falló"
    exit 1
}
Pop-Location
Write-Host "      Contenedores iniciados." -ForegroundColor Green

# 2. Espera puertos básicos
Write-Host ""
Write-Host "[2/4] Esperando puertos base..." -ForegroundColor Yellow

$ports = @(5432, 5433, 3307, 1433, 27017, 9042, 7687, 7474)
$allOk = $true

foreach ($p in $ports) {
    $ok = Wait-Port -TargetHost "localhost" -Port $p -TimeoutSeconds 180
    if (-not $ok) { $allOk = $false }
}

if (-not $allOk) {
    Write-Error "Uno o más puertos base no respondieron."
    exit 1
}

# 3. Espera extra real para motores pesados
Write-Host ""
Write-Host "[3/4] Espera adicional para inicialización real..." -ForegroundColor Yellow
Write-Host "      MySQL / Cassandra / SQL Server aún pueden estar terminando init." -ForegroundColor DarkYellow
Start-Sleep -Seconds 90
Write-Host "      Espera completada." -ForegroundColor Green

# 4. Fin
Write-Host ""
Write-Host "[4/4] INFRAESTRUCTURA LISTA" -ForegroundColor Green
Write-Host ""
Write-Host "Servicios disponibles:" -ForegroundColor Cyan
Write-Host "  PostgreSQL bancos : localhost:5432"
Write-Host "  PostgreSQL ASFI   : localhost:5433"
Write-Host "  MySQL             : localhost:3307"
Write-Host "  SQL Server        : localhost:1433"
Write-Host "  MongoDB           : localhost:27017"
Write-Host "  Cassandra         : localhost:9042"
Write-Host "  Neo4j Bolt        : localhost:7687"
Write-Host "  Neo4j UI          : http://localhost:7474"
Write-Host ""
Write-Host "Siguiente paso:" -ForegroundColor Cyan
Write-Host "  .\start_apis.ps1"
Write-Host ""