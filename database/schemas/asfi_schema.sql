-- =========================================================
-- ASFI SCHEMA
-- Estructura mínima y centralizada para ASFI
-- =========================================================

CREATE TABLE IF NOT EXISTS bancos (
    banco_id INT PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    algoritmo VARCHAR(50) NOT NULL,
    endpoint_api VARCHAR(255) NOT NULL,
    version_llave VARCHAR(50) NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'ACTIVO',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100) NOT NULL DEFAULT 'SYSTEM',
    updated_by VARCHAR(100) NOT NULL DEFAULT 'SYSTEM',
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMP NULL,
    deleted_by VARCHAR(100) NULL
);

CREATE TABLE IF NOT EXISTS cuentas (
    asfi_cuenta_id BIGSERIAL PRIMARY KEY,
    cuenta_id BIGINT NOT NULL,
    banco_id INT NOT NULL,
    ci VARCHAR(64) NOT NULL,
    nombre VARCHAR(150) NOT NULL,
    apellido VARCHAR(150) NOT NULL,
    numero_cuenta VARCHAR(128) NOT NULL,
    saldo_usd_original DECIMAL(18,4) NOT NULL,
    saldo_bs DECIMAL(18,4) NULL,
    tipo_cambio_aplicado DECIMAL(10,4) NULL,
    codigo_verificacion CHAR(8) NULL,
    fecha_conversion TIMESTAMP NULL,
    estado VARCHAR(30) NOT NULL DEFAULT 'PENDIENTE',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100) NOT NULL DEFAULT 'SYSTEM',
    updated_by VARCHAR(100) NOT NULL DEFAULT 'SYSTEM',
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMP NULL,
    deleted_by VARCHAR(100) NULL,
    CONSTRAINT fk_cuentas_banco
        FOREIGN KEY (banco_id) REFERENCES bancos(banco_id),
    CONSTRAINT uq_cuentas_banco_cuenta
        UNIQUE (banco_id, cuenta_id),
    CONSTRAINT uq_cuentas_banco_numero
        UNIQUE (banco_id, numero_cuenta)
);

CREATE INDEX IF NOT EXISTS idx_cuentas_banco_id
    ON cuentas(banco_id);

CREATE INDEX IF NOT EXISTS idx_cuentas_cuenta_id
    ON cuentas(cuenta_id);

CREATE INDEX IF NOT EXISTS idx_cuentas_ci
    ON cuentas(ci);

CREATE INDEX IF NOT EXISTS idx_cuentas_numero_cuenta
    ON cuentas(numero_cuenta);

CREATE INDEX IF NOT EXISTS idx_cuentas_estado
    ON cuentas(estado);

CREATE INDEX IF NOT EXISTS idx_cuentas_fecha_conversion
    ON cuentas(fecha_conversion);