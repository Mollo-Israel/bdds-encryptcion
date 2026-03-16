import time
from datetime import datetime

from fastapi import FastAPI

from models import HealthResponse, RateResponse, SnapshotResponse
from rate_engine import rate_engine

app = FastAPI(
    title="BCB Rate Service",
    description="Servicio simulado del Banco Central de Bolivia - Tipo de cambio USD/BOB",
    version="1.0.0",
)

_start_time = time.time()


@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(
        status="ok",
        uptime_seconds=round(time.time() - _start_time, 2),
    )


@app.get("/rate", response_model=RateResponse)
def get_rate():
    return RateResponse(rate=rate_engine.get_rate())


@app.get("/snapshot", response_model=SnapshotResponse)
def get_snapshot():
    snapshot = rate_engine.get_snapshot()
    return SnapshotResponse(
        rate=snapshot["rate"],
        timestamp=snapshot["timestamp"],
        next_update=snapshot["next_update"],
    )
