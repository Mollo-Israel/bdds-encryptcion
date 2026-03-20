# =============================================================
# run_demo.ps1 - Ejecuta el barrido paralelo completo ASFI
# Ejecutar desde la raiz del proyecto: .\run_demo.ps1
# Prerequisito: .\start.ps1 ya debe haber finalizado correctamente.
# =============================================================

$root      = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonExe = Join-Path $root "services\bank_service_template\.venv312\Scripts\python.exe"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  DEMO: Barrido Paralelo ASFI - 14 bancos simultaneos" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

& $pythonExe (Join-Path $root "parallel\sweep.py")

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "Auditoria disponible en: http://localhost:9000/audit/path" -ForegroundColor Cyan
    Write-Host "Cuentas en ASFI: http://localhost:9000/docs  -> GET /banks/{id}/accounts" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "Revisa los logs de cada banco y de ASFI para mas detalle." -ForegroundColor Yellow
}
