# =============================================================
# start.ps1 - Script maestro de orquestación BDDS-Encryptcion
# Ejecutar desde la raiz del proyecto: .\start.ps1
# =============================================================

$root        = Split-Path -Parent $MyInvocation.MyCommand.Path
$servicePath = Join-Path $root "services\bank_service_template"
$pythonExe   = Join-Path $servicePath ".venv312\Scripts\python.exe"
$bcbPath     = Join-Path $root "services\bcb_rate_service"
$asfiPath    = Join-Path $root "services\asfi_service"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  BDDS - Plataforma Distribuida de Conversion Monetaria ASFI" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# ---------------------------------------------------------------------------
# 1. Levantar contenedores Docker
# ---------------------------------------------------------------------------
Write-Host "[1/7] Levantando contenedores Docker..." -ForegroundColor Yellow
Push-Location (Join-Path $root "docker")
docker compose up -d
if ($LASTEXITCODE -ne 0) { Write-Error "docker compose up fallo"; Pop-Location; exit 1 }
Pop-Location
Write-Host "      Contenedores iniciados." -ForegroundColor Green

# ---------------------------------------------------------------------------
# 2. Esperar readiness de bases de datos relacionales y NoSQL
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[2/7] Esperando readiness de bases de datos (hasta 120s c/u)..." -ForegroundColor Yellow
& $pythonExe (Join-Path $root "scripts\wait_ports.py") `
    "localhost:5432" "localhost:5433" "localhost:3307" `
    "localhost:1433" "localhost:27017" "localhost:9042"
if ($LASTEXITCODE -ne 0) { Write-Error "Alguna base de datos no respondio"; exit 1 }

# Neo4j tarda mas en inicializar el motor interno
Write-Host "      Esperando Neo4j (bolt:7687) - puede tardar hasta 60s..." -ForegroundColor Yellow
& $pythonExe (Join-Path $root "scripts\wait_ports.py") "localhost:7687"
if ($LASTEXITCODE -ne 0) { Write-Error "Neo4j no respondio"; exit 1 }
Write-Host "      Espera adicional Neo4j (15s para que termine el init interno)..."
Start-Sleep -Seconds 15
Write-Host "      Todas las bases de datos listas." -ForegroundColor Green

# ---------------------------------------------------------------------------
# 3. Levantar los 14 microservicios bancarios
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[3/7] Levantando 14 microservicios bancarios..." -ForegroundColor Yellow
& (Join-Path $root "start_all_banks.ps1")
Write-Host "      Ventanas de bancos abiertas. Esperando inicializacion (20s)..."
Start-Sleep -Seconds 20

# ---------------------------------------------------------------------------
# 4. Verificar que los bancos respondan
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[4/7] Verificando disponibilidad de bancos..." -ForegroundColor Yellow
& $pythonExe (Join-Path $root "scripts\wait_ports.py") `
    "localhost:8001" "localhost:8002" "localhost:8003" "localhost:8004" `
    "localhost:8005" "localhost:8006" "localhost:8007" "localhost:8008" `
    "localhost:8009" "localhost:8010" "localhost:8011" "localhost:8012" `
    "localhost:8013" "localhost:8014"
if ($LASTEXITCODE -ne 0) { Write-Error "Algun banco no respondio"; exit 1 }
Write-Host "      Los 14 bancos estan listos." -ForegroundColor Green

# ---------------------------------------------------------------------------
# 5. Levantar BCB Rate Service y ASFI Service
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[5/7] Levantando BCB Rate Service (puerto 9101)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", `
    "Set-Location '$bcbPath'; & '$pythonExe' -m uvicorn main:app --port 9101"

Write-Host "      Levantando ASFI Service (puerto 9000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", `
    "Set-Location '$asfiPath'; & '$pythonExe' -m uvicorn main:app --port 9000"

Write-Host "      Esperando inicializacion de BCB y ASFI (15s)..."
Start-Sleep -Seconds 15

& $pythonExe (Join-Path $root "scripts\wait_ports.py") "localhost:9101" "localhost:9000"
if ($LASTEXITCODE -ne 0) { Write-Error "BCB o ASFI no respondieron"; exit 1 }
Write-Host "      BCB y ASFI listos." -ForegroundColor Green

# ---------------------------------------------------------------------------
# 6. Cargar datos en bancos via ETL (bank_router)
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[6/7] Cargando dataset en los 14 bancos (ETL)..." -ForegroundColor Yellow
Set-Location $root
& $pythonExe (Join-Path $root "etl\bank_router.py")
if ($LASTEXITCODE -ne 0) { Write-Error "ETL bank_router fallo"; exit 1 }
Write-Host "      Datos cargados correctamente." -ForegroundColor Green

# ---------------------------------------------------------------------------
# 7. Sistema listo
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "[7/7] SISTEMA LISTO PARA DEMO" -ForegroundColor Green
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
