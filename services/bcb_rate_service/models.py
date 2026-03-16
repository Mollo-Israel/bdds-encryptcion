from pydantic import BaseModel
from datetime import datetime


class RateResponse(BaseModel):
    rate: float
    currency_from: str = "USD"
    currency_to: str = "BOB"


class SnapshotResponse(BaseModel):
    rate: float
    currency_from: str = "USD"
    currency_to: str = "BOB"
    timestamp: datetime
    next_update: datetime


class HealthResponse(BaseModel):
    status: str
    service: str = "bcb-rate-service"
    uptime_seconds: float
