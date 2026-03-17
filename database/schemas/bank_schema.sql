-- =========================================================
-- BANK SCHEMA
-- Esquema base para las bases de datos bancarias
-- Aplica a motores relacionales:
-- PostgreSQL / MySQL / SQL Server
-- =========================================================

CREATE TABLE IF NOT EXISTS cuentas (
    cuenta_id BIGINT PRIMARY KEY,
    banco_id INT NOT NULL,
    ci VARCHAR(20) NOT NULL,
    nombre VARCHAR(150) NOT NULL,
    apellido VARCHAR(150) NOT NULL,
    numero_cuenta VARCHAR(32) NOT NULL,
    saldo_usd_encrypted TEXT NOT NULL,
    saldo_bs DECIMAL(18,4) NULL,
    codigo_verificacion CHAR(8) NULL,
    fecha_conversion TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_cuentas_banco_numero UNIQUE (banco_id, numero_cuenta)
);

CREATE INDEX idx_cuentas_ci ON cuentas(ci);
CREATE INDEX idx_cuentas_banco_id ON cuentas(banco_id);
CREATE INDEX idx_cuentas_numero_cuenta ON cuentas(numero_cuenta);
CREATE INDEX idx_cuentas_fecha_conversion ON cuentas(fecha_conversion);