-- =========================================================
-- ASFI INIT: Tablas y seed de bancos
-- Se ejecuta automáticamente al crear la BD asfi_central
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
    CONSTRAINT fk_cuentas_banco FOREIGN KEY (banco_id) REFERENCES bancos(banco_id),
    CONSTRAINT uq_cuentas_banco_cuenta UNIQUE (banco_id, cuenta_id),
    CONSTRAINT uq_cuentas_banco_numero UNIQUE (banco_id, numero_cuenta)
);

CREATE INDEX IF NOT EXISTS idx_cuentas_banco_id ON cuentas(banco_id);
CREATE INDEX IF NOT EXISTS idx_cuentas_cuenta_id ON cuentas(cuenta_id);
CREATE INDEX IF NOT EXISTS idx_cuentas_ci ON cuentas(ci);
CREATE INDEX IF NOT EXISTS idx_cuentas_numero_cuenta ON cuentas(numero_cuenta);
CREATE INDEX IF NOT EXISTS idx_cuentas_estado ON cuentas(estado);
CREATE INDEX IF NOT EXISTS idx_cuentas_fecha_conversion ON cuentas(fecha_conversion);

-- Seed: 14 bancos con endpoints y algoritmos
-- Banco 13 usa Neo4j (base orientada a grafos)
INSERT INTO bancos (banco_id, nombre, algoritmo, endpoint_api, version_llave) VALUES
(1,  'Banco Union S.A.',                         'CAESAR',   'http://localhost:8001', 'v1'),
(2,  'Banco Mercantil Santa Cruz S.A.',           'ATBASH',   'http://localhost:8002', 'v1'),
(3,  'Banco Nacional de Bolivia S.A. (BNB)',      'VIGENERE', 'http://localhost:8003', 'v1'),
(4,  'Banco de Credito de Bolivia S.A. (BCP)',    'PLAYFAIR', 'http://localhost:8004', 'v1'),
(5,  'Banco BISA S.A.',                           'HILL',     'http://localhost:8005', 'v1'),
(6,  'Banco Ganadero S.A.',                       'DES',      'http://localhost:8006', 'v1'),
(7,  'Banco Economico S.A.',                      '3DES',     'http://localhost:8007', 'v1'),
(8,  'Banco Prodem S.A.',                         'BLOWFISH', 'http://localhost:8008', 'v1'),
(9,  'Banco Solidario S.A.',                      'TWOFISH',  'http://localhost:8009', 'v1'),
(10, 'Banco Fortaleza S.A.',                      'AES',      'http://localhost:8010', 'v1'),
(11, 'Banco FIE S.A.',                            'RSA',      'http://localhost:8011', 'v1'),
(12, 'Banco PYME de la Comunidad S.A.',           'ELGAMAL',  'http://localhost:8012', 'v1'),
(13, 'Banco de Desarrollo Productivo S.A.M.',     'ECC',      'http://localhost:8013', 'v1'),
(14, 'Banco de la Nacion Argentina',              'CHACHA20', 'http://localhost:8014', 'v1')
ON CONFLICT (banco_id) DO NOTHING;
