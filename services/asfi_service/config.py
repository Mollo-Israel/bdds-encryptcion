import os

# Identidad del servicio
SERVICE_NAME: str = os.getenv("SERVICE_NAME", "ASFI Service")
PORT: int = int(os.getenv("PORT", "9000"))

# Base de datos central ASFI
DB_ENGINE: str = os.getenv("DB_ENGINE", "postgresql")
DB_URL: str = os.getenv(
    "DB_URL",
    "postgresql+psycopg2://admin:admin123@localhost:5433/asfi_central",
)

# Seguridad / autenticación hacia bancos
ASFI_SHARED_TOKEN: str = os.getenv("ASFI_SHARED_TOKEN", "ASFI-2026-TOKEN")
AUTH_HEADER_NAME: str = os.getenv("AUTH_HEADER_NAME", "Authorization")

# HTTP
REQUEST_TIMEOUT_SECONDS: int = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))

# BCB
BCB_RATE_API_URL: str = os.getenv("BCB_RATE_API_URL", "http://localhost:9101")