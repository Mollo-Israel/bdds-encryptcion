import os

# Identidad del banco
BANK_ID: int = int(os.getenv("BANK_ID", "0"))
BANK_NAME: str = os.getenv("BANK_NAME", "Bank Template")
ALGORITHM: str = os.getenv("ALGORITHM", "NONE")

# Base de datos
DB_ENGINE: str = os.getenv("DB_ENGINE", "sqlite")
DB_URL: str = os.getenv("DB_URL", "sqlite:///./bank.db")

# Servidor
PORT: int = int(os.getenv("PORT", "8001"))

# Seguridad / autenticación entre nodos
ASFI_SHARED_TOKEN: str = os.getenv("ASFI_SHARED_TOKEN", "ASFI-DEFAULT-TOKEN")
AUTH_ENABLED: bool = os.getenv("AUTH_ENABLED", "true").strip().lower() in {"1", "true", "yes", "on"}
AUTH_HEADER_NAME: str = os.getenv("AUTH_HEADER_NAME", "Authorization")