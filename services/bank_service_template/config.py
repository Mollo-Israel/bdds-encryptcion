import os

# Identidad del banco
BANK_ID: int = int(os.getenv("BANK_ID", "0"))
BANK_NAME: str = os.getenv("BANK_NAME", "Bank Template")
ALGORITHM: str = os.getenv("ALGORITHM", "NONE")

# Base de datos
DB_ENGINE: str = os.getenv("DB_ENGINE", "sqlite")   # sqlite | postgresql | mysql
DB_URL: str = os.getenv("DB_URL", "sqlite:///./bank.db")

# Servidor
PORT: int = int(os.getenv("PORT", "8001"))
