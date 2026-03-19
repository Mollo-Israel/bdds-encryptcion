-- =========================================================
-- BANK SCHEMA - SQL SERVER
-- Esquema base para las bases de datos bancarias
-- Adaptado para SQL Server
-- =========================================================

IF OBJECT_ID('cuentas', 'U') IS NULL
CREATE TABLE cuentas (
    cuenta_id BIGINT PRIMARY KEY,
    banco_id INT NOT NULL,
    ci VARCHAR(64) NOT NULL,
    nombre VARCHAR(150) NOT NULL,
    apellido VARCHAR(150) NOT NULL,
    numero_cuenta VARCHAR(128) NOT NULL,
    saldo_usd_encrypted VARCHAR(MAX) NOT NULL,
    saldo_bs DECIMAL(18,4) NULL,
    codigo_verificacion CHAR(8) NULL,
    fecha_conversion DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME NOT NULL DEFAULT GETDATE(),
    CONSTRAINT uq_cuentas_banco_numero UNIQUE (banco_id, numero_cuenta)
);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_cuentas_ci' AND object_id = OBJECT_ID('cuentas'))
    CREATE INDEX idx_cuentas_ci ON cuentas(ci);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_cuentas_banco_id' AND object_id = OBJECT_ID('cuentas'))
    CREATE INDEX idx_cuentas_banco_id ON cuentas(banco_id);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_cuentas_numero_cuenta' AND object_id = OBJECT_ID('cuentas'))
    CREATE INDEX idx_cuentas_numero_cuenta ON cuentas(numero_cuenta);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_cuentas_fecha_conversion' AND object_id = OBJECT_ID('cuentas'))
    CREATE INDEX idx_cuentas_fecha_conversion ON cuentas(fecha_conversion);