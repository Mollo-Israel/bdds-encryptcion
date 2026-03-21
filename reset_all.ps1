# =============================================================
# reset_all.ps1 - Limpieza total del entorno BDDS-Encryptcion
# Ejecutar desde la raíz: .\reset_all.ps1
# =============================================================

$root = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  BDDS - RESET TOTAL DEL ENTORNO" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# ---------------------------------------------------------------------------
# 1. Matar procesos Python/uvicorn locales asociados a bancos/ASFI/BCB
# ---------------------------------------------------------------------------
Write-Host "[1/5] Cerrando procesos Python/uvicorn locales..." -ForegroundColor Yellow

$portsToKill = @(8001..8014) + @(9000, 9101)

foreach ($port in $portsToKill) {
    $lines = netstat -ano | Select-String ":$port"
    foreach ($line in $lines) {
        $parts = ($line -replace "\s+", " ").Trim().Split(" ")
        if ($parts.Length -ge 5) {
            $pid = $parts[-1]
            if ($pid -match '^\d+$' -and $pid -ne "0") {
                try {
                    Stop-Process -Id $pid -Force -ErrorAction Stop
                    Write-Host "      Puerto ${port}: proceso PID $pid detenido." -ForegroundColor Green
                } catch {
                    Write-Host "      Puerto ${port}: no se pudo detener PID $pid (quizá ya murió)." -ForegroundColor DarkYellow
                }
            }
        }
    }
}

# cierre adicional por nombre
Get-Process python, python3, uvicorn -ErrorAction SilentlyContinue | ForEach-Object {
    try {
        Stop-Process -Id $_.Id -Force -ErrorAction Stop
        Write-Host "      Proceso $($_.ProcessName) PID $($_.Id) detenido." -ForegroundColor Green
    } catch {}
}

# ---------------------------------------------------------------------------
# 2. Docker compose down -v
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[2/5] Bajando contenedores, red y volúmenes Docker..." -ForegroundColor Yellow
Push-Location (Join-Path $root "docker")
docker compose down -v --remove-orphans
if ($LASTEXITCODE -ne 0) {
    Write-Host "      Aviso: docker compose down devolvió error o no había recursos activos." -ForegroundColor DarkYellow
}
Pop-Location

# ---------------------------------------------------------------------------
# 3. Limpieza opcional de contenedores huérfanos
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[3/5] Limpiando contenedores detenidos..." -ForegroundColor Yellow
docker container prune -f | Out-Null

# ---------------------------------------------------------------------------
# 4. Mostrar puertos todavía ocupados
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[4/5] Verificando puertos relevantes..." -ForegroundColor Yellow
foreach ($port in $portsToKill + @(5432,5433,3307,1433,27017,9042,7474,7687)) {
    $lines = netstat -ano | Select-String ":$port"
    if ($lines) {
        Write-Host "      Advertencia: el puerto $port aún aparece ocupado." -ForegroundColor Red
    }
}

# ---------------------------------------------------------------------------
# 5. Fin
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[5/5] RESET FINALIZADO" -ForegroundColor Green
Write-Host ""
Write-Host "Ahora puedes levantar todo de nuevo con:" -ForegroundColor Cyan
Write-Host "  .\start.ps1"
Write-Host ""