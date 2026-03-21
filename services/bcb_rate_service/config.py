import os

BASE_RATE: float = float(os.getenv("BASE_RATE", "6.86"))
OSCILACION: float = float(os.getenv("OSCILACION", "0.0"))
PRECISION: int = int(os.getenv("PRECISION", "4"))
