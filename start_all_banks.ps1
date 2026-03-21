# =============================================================
# start.ps1 - Orquestador robusto BDDS-Encryptcion
# Ejecutar desde la raíz: .\start.ps1
# =============================================================

$root        = Split-Path -Parent $MyInvocation.MyCommand.Path
$servicePath = Join-Path $root "services\bank_service_template"
$pythonExe   = Join-Path $servicePath ".venv312\Scripts\python.exe"
$bcbPath     = Join-Path $root "services\bcb_rate_service"
$asfiPath    = Join-Path $root "services\asfi_service"

function Wait-PortGroup {
    param(
        [string[]]$Targets,
        [string]$Label = "puertos"
    )

    Write-Host "      Esperando $Label ..." -ForegroundColor Yellow
    & $pythonExe (Join-Path $root "scripts\wait_ports.py") @Targets
    if ($LASTEXITCODE -ne 0) {
        Write-Error "No respondieron todos los targets de $Label"
        exit 1
    }
}

function Kill-PortIfBusy {
    param([int]$Port)

    $lines = netstat -ano | Select-String ":$Port"
    foreach ($line in $lines) {
        $parts = ($line -replace "\s+", " ").Trim().Split(" ")
        if ($parts.Length -ge 5) {
            $pid = $parts[-1]
            if ($pid -match '^\d+$' -and $pid -ne "0") {
                try {
                    Stop-Process -Id $pid -Force -ErrorAction Stop
                    Write-Host "      Puerto ${Port}: PID $pid detenido." -ForegroundColor Green
                } catch {
                    Write-Host "      Puerto ${Port}: no se pudo detener PID $pid." -ForegroundColor DarkYellow
                }
            }
        }
    }
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  BDDS - Plataforma Distribuida de Conversion Monetaria ASFI" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# ---------------------------------------------------------------------------
# 0. Verificaciones básicas
# ---------------------------------------------------------------------------
Write-Host "[0/8] Verificando entorno..." -ForegroundColor Yellow

if (-not (Test-Path $pythonExe)) {
    Write-Error "No se encontró Python del template: $pythonExe"
    exit 1
}

docker version | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Error "Docker no está disponible o no está corriendo."
    exit 1
}

# cerrar puertos locales sensibles por si quedaron restos
foreach ($p in @(8001..8014) + @(9000,9101)) {
    Kill-PortIfBusy -Port $p
}

# ---------------------------------------------------------------------------
# 1. Levantar contenedores Docker
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[1/8] Levantando contenedores Docker..." -ForegroundColor Yellow
Push-Location (Join-Path $root "docker")
docker compose up -d
if ($LASTEXITCODE -ne 0) {
    Write-Error "docker compose up falló"
    Pop-Location
    exit 1
}
Pop-Location
Write-Host "      Contenedores iniciados." -ForegroundColor Green

# ---------------------------------------------------------------------------
# 2. Espera de puertos base
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[2/8] Esperando puertos base..." -ForegroundColor Yellow
Wait-PortGroup -Label "bases relacionales y NoSQL" -Targets @(
    "localhost:5432",
    "localhost:5433",
    "localhost:3307",
    "localhost:1433",
    "localhost:27017",
    "localhost:9042"
)

Write-Host "      Esperando Neo4j (bolt:7687)..." -ForegroundColor Yellow
Wait-PortGroup -Label "Neo4j" -Targets @("localhost:7687")

# ---------------------------------------------------------------------------
# 3. Espera extra de startup real
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[3/8] Espera adicional por inicialización real de motores..." -ForegroundColor Yellow
Write-Host "      MySQL, Cassandra y SQL Server tardan más que un puerto abierto." -ForegroundColor DarkYellow
Write-Host "      Esperando 120 segundos..." -ForegroundColor Yellow
Start-Sleep -Seconds 120
Write-Host "      Espera base completada." -ForegroundColor Green

# ---------------------------------------------------------------------------
# 4. Levantar bancos
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[4/8] Levantando 14 microservicios bancarios..." -ForegroundColor Yellow
& (Join-Path $root "start_all_banks.ps1")
if ($LASTEXITCODE -ne 0) {
    Write-Error "start_all_banks.ps1 falló"
    exit 1
}
Write-Host "      Ventanas de bancos abiertas. Esperando inicialización (60s)..." -ForegroundColor Yellow
Start-Sleep -Seconds 60

# ---------------------------------------------------------------------------
# 5. Verificar bancos
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[5/8] Verificando disponibilidad de bancos..." -ForegroundColor Yellow
& $pythonExe (Join-Path $root "scripts\wait_ports.py") `
    "localhost:8001" "localhost:8002" "localhost:8003" "localhost:8004" `
    "localhost:8005" "localhost:8006" "localhost:8007" "localhost:8008" `
    "localhost:8009" "localhost:8010" "localhost:8011" "localhost:8012" `
    "localhost:8013" "localhost:8014"

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: No todos los bancos respondieron." -ForegroundColor Red
    Write-Host "Revisa las ventanas PowerShell abiertas por banco para identificar el motor que falló." -ForegroundColor Yellow
    Write-Host "Si quieres reiniciar limpio, ejecuta: .\reset_all.ps1" -ForegroundColor Cyan
    exit 1
}
Write-Host "      Los 14 bancos están listos." -ForegroundColor Green

# ---------------------------------------------------------------------------
# 6. Levantar BCB y ASFI
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[6/8] Levantando BCB Rate Service y ASFI..." -ForegroundColor Yellow

Start-Process powershell -ArgumentList "-NoExit", "-Command", `
    "Set-Location '$bcbPath'; & '$pythonExe' -m uvicorn main:app --host 0.0.0.0 --port 9101"

Start-Process powershell -ArgumentList "-NoExit", "-Command", `
    "Set-Location '$asfiPath'; & '$pythonExe' -m uvicorn main:app --host 0.0.0.0 --port 9000"

Write-Host "      Esperando inicialización de BCB y ASFI (20s)..." -ForegroundColor Yellow
Start-Sleep -Seconds 20

Wait-PortGroup -Label "BCB y ASFI" -Targets @("localhost:9101", "localhost:9000")
Write-Host "      BCB y ASFI listos." -ForegroundColor Green

# ---------------------------------------------------------------------------
# 7. Cargar datos ETL
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[7/8] Cargando dataset en los 14 bancos (ETL)..." -ForegroundColor Yellow
Set-Location $root
& $pythonExe (Join-Path $root "etl\bank_router.py")
if ($LASTEXITCODE -ne 0) {
    Write-Error "ETL bank_router falló"
    exit 1
}
Write-Host "      Datos cargados correctamente." -ForegroundColor Green

# ---------------------------------------------------------------------------
# 8. Sistema listo
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "[8/8] SISTEMA LISTO PARA DEMO" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  BCB Rate Service : http://localhost:9101/rate"
Write-Host "  ASFI Service     : http://localhost:9000/banks"
Write-Host "  Bancos           : http://localhost:8001 .. http://localhost:8014"
Write-Host "  Neo4j UI         : http://localhost:7474  (user: neo4j / pass: admin123)"
Write-Host "  ASFI Docs        : http://localhost:9000/docs"
Write-Host ""
Write-Host "Para ejecutar el barrido paralelo completo:" -ForegroundColor Cyan
Write-Host "  .\run_demo.ps1"
Write-Host ""
Write-Host "Para resetear todo y volver a empezar limpio:" -ForegroundColor Cyan
Write-Host "  .\reset_all.ps1"
Write-Host ""