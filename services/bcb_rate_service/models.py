from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


class RateResponse(BaseModel):
    rate: float
    currency_from: str = "USD"
    currency_to: str = "BOB"


class SnapshotResponse(BaseModel):
    rate: float
    currency_from: str = "USD"
    currency_to: str = "BOB"
    tipo_cambio_base: float
    oscilacion: float
    timestamp: datetime


class HealthResponse(BaseModel):
    status: str
    service: str = "bcb-rate-service"
    uptime_seconds: float


class ConfigRequest(BaseModel):
    """
    Permite configurar el tipo de cambio BCB manualmente.

    - tipo_cambio_base : valor base en BOB/USD (ej. 6.86)
    - oscilacion       : ajuste sobre la base, rango [-0.9999, 0.9999]
    - tipo_final       : base + oscilacion  (calculado por el servidor)
    """

    tipo_cambio_base: Optional[float] = None
    oscilacion: Optional[float] = None

    @field_validator("oscilacion")
    @classmethod
    def validate_oscilacion(cls, v):
        if v is not None and not (-0.9999 <= v <= 0.9999):
            raise ValueError("oscilacion debe estar en el rango [-0.9999, 0.9999]")
        return v

    @field_validator("tipo_cambio_base")
    @classmethod
    def validate_base(cls, v):
        if v is not None and v <= 0:
            raise ValueError("tipo_cambio_base debe ser mayor que 0")
        return v


class ConfigResponse(BaseModel):
    tipo_cambio_base: float
    oscilacion: float
    tipo_final: float
    currency_from: str = "USD"
    currency_to: str = "BOB"
