$servicePath = "D:\SISTEMAS DISTRIBUIDOS\bdds-encryptcion\services\bank_service_template"
$pythonExe   = Join-Path $servicePath ".venv312\Scripts\python.exe"

$sharedToken = "ASFI-2026-TOKEN"
$authEnabled = "true"

$banks = @(
    @{Id="1";  Name="Banco Union S.A.";                       Algorithm="CAESAR";   Engine="postgresql"; DbUrl="postgresql+psycopg2://admin:admin123@localhost:5432/banco_union"; Port="8001"},
    @{Id="2";  Name="Banco Mercantil Santa Cruz S.A.";       Algorithm="ATBASH";   Engine="postgresql"; DbUrl="postgresql+psycopg2://admin:admin123@localhost:5432/banco_mercantil_santa_cruz"; Port="8002"},
    @{Id="3";  Name="Banco Nacional de Bolivia S.A. (BNB)";  Algorithm="VIGENERE"; Engine="postgresql"; DbUrl="postgresql+psycopg2://admin:admin123@localhost:5432/banco_nacional_bolivia"; Port="8003"},
    @{Id="4";  Name="Banco de Credito de Bolivia S.A. (BCP)";Algorithm="PLAYFAIR"; Engine="mysql";      DbUrl="mysql+pymysql://root:root123@localhost:3307/banco_credito_bolivia"; Port="8004"},
    @{Id="5";  Name="Banco BISA S.A.";                       Algorithm="HILL";      Engine="mysql";      DbUrl="mysql+pymysql://root:root123@localhost:3307/banco_bisa"; Port="8005"},
    @{Id="6";  Name="Banco Ganadero S.A.";                   Algorithm="DES";       Engine="mysql";      DbUrl="mysql+pymysql://root:root123@localhost:3307/banco_ganadero"; Port="8006"},
    @{Id="7";  Name="Banco Economico S.A.";                  Algorithm="3DES";      Engine="sqlserver";  DbUrl="mssql+pyodbc://sa:SqlServer123%21@localhost:1433/banco_economico?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes"; Port="8007"},
    @{Id="8";  Name="Banco Prodem S.A.";                     Algorithm="BLOWFISH";  Engine="sqlserver";  DbUrl="mssql+pyodbc://sa:SqlServer123%21@localhost:1433/banco_prodem?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes"; Port="8008"},
    @{Id="9";  Name="Banco Solidario S.A.";                  Algorithm="TWOFISH";   Engine="sqlserver";  DbUrl="mssql+pyodbc://sa:SqlServer123%21@localhost:1433/banco_solidario?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes"; Port="8009"},
    @{Id="10"; Name="Banco Fortaleza S.A.";                  Algorithm="AES";       Engine="mongodb";    DbUrl="mongodb://admin:admin123@localhost:27017/banco_fortaleza?authSource=admin"; Port="8010"},
    @{Id="11"; Name="Banco FIE S.A.";                        Algorithm="RSA";       Engine="mongodb";    DbUrl="mongodb://admin:admin123@localhost:27017/banco_fie?authSource=admin"; Port="8011"},
    @{Id="12"; Name="Banco PYME de la Comunidad S.A.";       Algorithm="ELGAMAL";   Engine="cassandra";  DbUrl="cassandra://localhost:9042/banco_pyme_comunidad"; Port="8012"},
    @{Id="13"; Name="Banco de Desarrollo Productivo S.A.M."; Algorithm="ECC";       Engine="cassandra";  DbUrl="cassandra://localhost:9042/banco_desarrollo_productivo"; Port="8113"},
    @{Id="14"; Name="Banco de la Nacion Argentina";          Algorithm="CHACHA20";  Engine="cassandra";  DbUrl="cassandra://localhost:9042/banco_nacion_argentina"; Port="8014"}
)

foreach ($b in $banks) {
    $cmd = @"
Set-Location '$servicePath'
`$env:BANK_ID='$($b.Id)'
`$env:BANK_NAME='$($b.Name)'
`$env:ALGORITHM='$($b.Algorithm)'
`$env:DB_ENGINE='$($b.Engine)'
`$env:DB_URL='$($b.DbUrl)'
`$env:PORT='$($b.Port)'
`$env:ASFI_SHARED_TOKEN='$sharedToken'
`$env:AUTH_ENABLED='$authEnabled'
& '$pythonExe' -m uvicorn main:app --port $($b.Port)
"@

    Start-Process powershell -ArgumentList "-NoExit", "-Command", $cmd
}