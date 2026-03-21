# =============================================================
# stop_apis.ps1
# Mata APIs locales por puertos
# =============================================================

$ports = @(8001..8014) + @(9000,9101)

foreach ($port in $ports) {
    $lines = netstat -ano | Select-String ":$port"
    foreach ($line in $lines) {
        $parts = ($line -replace "\s+", " ").Trim().Split(" ")
        if ($parts.Length -ge 5) {
            $pid = $parts[-1]
            if ($pid -match '^\d+$' -and $pid -ne "0") {
                try {
                    Stop-Process -Id $pid -Force -ErrorAction Stop
                    Write-Host "Puerto ${port}: PID $pid detenido." -ForegroundColor Green
                } catch {
                    Write-Host "Puerto ${port}: no se pudo detener PID $pid." -ForegroundColor DarkYellow
                }
            }
        }
    }
}