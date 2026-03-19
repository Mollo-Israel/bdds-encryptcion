import os

BASE_RATE: float = float(os.getenv("BASE_RATE", "6.86"))
UPDATE_INTERVAL_SECONDS: int = int(os.getenv("UPDATE_INTERVAL_SECONDS", "180"))
MAX_VARIATION: float = float(os.getenv("MAX_VARIATION", "0.9999"))
PRECISION: int = int(os.getenv("PRECISION", "4"))