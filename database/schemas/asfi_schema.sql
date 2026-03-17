-- =========================================================
-- ASFI SCHEMA
-- Esquema base para la base central de ASFI
-- =========================================================

CREATE TABLE IF NOT EXISTS bancos (
    banco_id INT PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    algoritmo VARCHAR(50) NOT NULL,
    endpoint_api VARCHAR(255) NOT NULL,
    version_llave VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS conversiones (
    conversion_id BIGINT PRIMARY KEY,
    batch_id VARCHAR(64) NOT NULL,
    cuenta_id BIGINT NOT NULL,
    banco_id INT NOT NULL,
    saldo_usd_original DECIMAL(18,4) NOT NULL,
    tipo_cambio_aplicado DECIMAL(10,4) NOT NULL,
    saldo_bs_convertido DECIMAL(18,4) NOT NULL,
    codigo_verificacion CHAR(8) NOT NULL,
    fecha_conversion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    hash_integridad VARCHAR(256) NOT NULL,
    estado VARCHAR(30) NOT NULL,
    CONSTRAINT fk_conversiones_banco
        FOREIGN KEY (banco_id) REFERENCES bancos(banco_id)
);

CREATE TABLE IF NOT EXISTS audit_log (
    log_id BIGINT PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    batch_id VARCHAR(64) NOT NULL,
    banco_id INT NOT NULL,
    cuenta_id BIGINT NOT NULL,
    tipo_cambio_aplicado DECIMAL(10,4) NOT NULL,
    evento VARCHAR(100) NOT NULL,
    hash_evento VARCHAR(256) NOT NULL,
    CONSTRAINT fk_audit_log_banco
        FOREIGN KEY (banco_id) REFERENCES bancos(banco_id)
);

CREATE TABLE IF NOT EXISTS inconsistencias (
    inconsistencia_id BIGINT PRIMARY KEY,
    cuenta_id BIGINT NOT NULL,
    banco_id INT NOT NULL,
    tipo_error VARCHAR(100) NOT NULL,
    descripcion TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_inconsistencias_banco
        FOREIGN KEY (banco_id) REFERENCES bancos(banco_id)
);

CREATE INDEX idx_conversiones_batch_id ON conversiones(batch_id);
CREATE INDEX idx_conversiones_banco_id ON conversiones(banco_id);
CREATE INDEX idx_conversiones_cuenta_id ON conversiones(cuenta_id);
CREATE INDEX idx_conversiones_fecha_conversion ON conversiones(fecha_conversion);
CREATE INDEX idx_conversiones_estado ON conversiones(estado);

CREATE INDEX idx_audit_log_batch_id ON audit_log(batch_id);
CREATE INDEX idx_audit_log_banco_id ON audit_log(banco_id);
CREATE INDEX idx_audit_log_cuenta_id ON audit_log(cuenta_id);
CREATE INDEX idx_audit_log_timestamp ON audit_log(timestamp);

CREATE INDEX idx_inconsistencias_cuenta_id ON inconsistencias(cuenta_id);
CREATE INDEX idx_inconsistencias_banco_id ON inconsistencias(banco_id);
CREATE INDEX idx_inconsistencias_timestamp ON inconsistencias(timestamp);