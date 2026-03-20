$ErrorActionPreference = "Stop"

Write-Host "PELIGRO: esto vaciara TODAS las bases de usuario (14 bancos + ASFI si esta en estos motores)." -ForegroundColor Yellow
Write-Host "La estructura se conserva; los datos se borran." -ForegroundColor Yellow

# Ajusta esto solo si tu usuario de Postgres no es admin
$pgUser = "admin"

# --------------------------------------------------
# 1) POSTGRES
# --------------------------------------------------
Write-Host "`n=== POSTGRES ===" -ForegroundColor Cyan

$pgDbs = docker exec postgres_banks psql -U $pgUser -d postgres -At -c "SELECT datname FROM pg_database WHERE datistemplate = false AND datname <> 'postgres';"
$pgDbs = $pgDbs | Where-Object { $_ -and $_.Trim() -ne "" }

foreach ($db in $pgDbs) {
    Write-Host "Limpiando Postgres DB: $db" -ForegroundColor Green

    $tables = docker exec postgres_banks psql -U $pgUser -d $db -At -c "SELECT quote_ident(schemaname)||'.'||quote_ident(tablename) FROM pg_tables WHERE schemaname='public';"
    $tables = $tables | Where-Object { $_ -and $_.Trim() -ne "" }

    if ($tables.Count -gt 0) {
        $tableList = $tables -join ", "
        docker exec postgres_banks psql -U $pgUser -d $db -c "TRUNCATE TABLE $tableList RESTART IDENTITY CASCADE;"
    }
    else {
        Write-Host "  sin tablas" -ForegroundColor DarkYellow
    }
}

# --------------------------------------------------
# 2) MYSQL
# --------------------------------------------------
Write-Host "`n=== MYSQL ===" -ForegroundColor Cyan

$mysqlPass = (docker exec mysql_banks printenv MYSQL_ROOT_PASSWORD).Trim()
if (-not $mysqlPass) {
    throw "No pude leer MYSQL_ROOT_PASSWORD del contenedor mysql_banks. Pon la contraseña manualmente en `$mysqlPass."
}

$mysqlDbs = docker exec mysql_banks mysql -u root "-p$mysqlPass" -N -e "SHOW DATABASES;"
$mysqlDbs = $mysqlDbs | Where-Object { $_ -and $_ -notmatch '^(information_schema|mysql|performance_schema|sys)$' }

foreach ($db in $mysqlDbs) {
    Write-Host "Limpiando MySQL DB: $db" -ForegroundColor Green

    $tables = docker exec mysql_banks mysql -u root "-p$mysqlPass" -N -e "SELECT table_name FROM information_schema.tables WHERE table_schema='$db';"
    $tables = $tables | Where-Object { $_ -and $_.Trim() -ne "" }

    if ($tables.Count -gt 0) {
        foreach ($t in $tables) {
            docker exec mysql_banks mysql -u root "-p$mysqlPass" -e "SET FOREIGN_KEY_CHECKS=0; USE $db; TRUNCATE TABLE $t; SET FOREIGN_KEY_CHECKS=1;"
            Write-Host "  - $t"
        }
    }
    else {
        Write-Host "  sin tablas" -ForegroundColor DarkYellow
    }
}

# --------------------------------------------------
# 3) MONGO
# --------------------------------------------------
Write-Host "`n=== MONGO ===" -ForegroundColor Cyan

$mongoDbsJson = docker exec mongo_banks mongosh --quiet --eval "JSON.stringify(db.adminCommand({listDatabases:1}).databases.map(d=>d.name))"
$mongoDbs = $mongoDbsJson | ConvertFrom-Json
$mongoDbs = $mongoDbs | Where-Object { $_ -notin @("admin","config","local") }

foreach ($db in $mongoDbs) {
    Write-Host "Limpiando Mongo DB: $db" -ForegroundColor Green

    $colsJson = docker exec mongo_banks mongosh --quiet --eval "JSON.stringify(db.getSiblingDB('$db').getCollectionNames())"
    $cols = $colsJson | ConvertFrom-Json

    if ($cols.Count -gt 0) {
        foreach ($c in $cols) {
            docker exec mongo_banks mongosh --quiet --eval "db.getSiblingDB('$db').getCollection('$c').deleteMany({})" | Out-Null
            Write-Host "  - $c"
        }
    }
    else {
        Write-Host "  sin colecciones" -ForegroundColor DarkYellow
    }
}

# --------------------------------------------------
# 4) CASSANDRA
# --------------------------------------------------
Write-Host "`n=== CASSANDRA ===" -ForegroundColor Cyan

$keyspacesRaw = docker exec cassandra_banks cqlsh -e "DESCRIBE KEYSPACES;"
$keyspaces = ($keyspacesRaw -join " ") -split "\s+" | Where-Object {
    $_ -and $_ -notmatch '^(system|system_auth|system_distributed|system_schema|system_traces)$'
}
$keyspaces = $keyspaces | Select-Object -Unique

foreach ($ks in $keyspaces) {
    Write-Host "Limpiando Cassandra keyspace: $ks" -ForegroundColor Green

    $tablesRaw = docker exec cassandra_banks cqlsh -e "USE $ks; DESCRIBE TABLES;"
    $tables = ($tablesRaw -join " ") -split "\s+" | Where-Object { $_ -and $_.Trim() -ne "" }
    $tables = $tables | Select-Object -Unique

    if ($tables.Count -gt 0) {
        foreach ($t in $tables) {
            docker exec cassandra_banks cqlsh -e "TRUNCATE $ks.$t;"
            Write-Host "  - $t"
        }
    }
    else {
        Write-Host "  sin tablas" -ForegroundColor DarkYellow
    }
}

# --------------------------------------------------
# 5) SQL SERVER
# --------------------------------------------------
Write-Host "`n=== SQL SERVER ===" -ForegroundColor Cyan

$saPass = (docker exec sqlserver_banks printenv SA_PASSWORD).Trim()
if (-not $saPass) {
    throw "No pude leer SA_PASSWORD del contenedor sqlserver_banks. Pon la contraseña manualmente en `$saPass."
}

$sqlcmdTest = docker exec sqlserver_banks bash -lc "test -x /opt/mssql-tools18/bin/sqlcmd && echo ok"
if ($sqlcmdTest.Trim() -eq "ok") {
    $sqlcmd = "/opt/mssql-tools18/bin/sqlcmd"
}
else {
    $sqlcmd = "/opt/mssql-tools/bin/sqlcmd"
}

$sqlDbs = docker exec sqlserver_banks $sqlcmd -C -S localhost -U sa -P $saPass -h -1 -W -Q "SET NOCOUNT ON; SELECT name FROM sys.databases WHERE name NOT IN ('master','tempdb','model','msdb');"
$sqlDbs = $sqlDbs | Where-Object { $_ -and $_.Trim() -ne "" }

$resetSql = @"
EXEC sp_MSforeachtable 'ALTER TABLE ? NOCHECK CONSTRAINT ALL';
EXEC sp_MSforeachtable 'DELETE FROM ?';
EXEC sp_MSforeachtable 'IF OBJECTPROPERTY(OBJECT_ID(''?'') , ''TableHasIdentity'') = 1 DBCC CHECKIDENT (''?'', RESEED, 0)';
EXEC sp_MSforeachtable 'ALTER TABLE ? WITH CHECK CHECK CONSTRAINT ALL';
"@
$resetSql = $resetSql -replace "`r?`n", " "

foreach ($db in $sqlDbs) {
    Write-Host "Limpiando SQL Server DB: $db" -ForegroundColor Green
    docker exec sqlserver_banks $sqlcmd -C -S localhost -U sa -P $saPass -d $db -Q $resetSql
}

Write-Host "`nLISTO: todas las bases de usuario quedaron vacias." -ForegroundColor Yellow
Write-Host "Estructura intacta. Datos borrados." -ForegroundColor Yellow