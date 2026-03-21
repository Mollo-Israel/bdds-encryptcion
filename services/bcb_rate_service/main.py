import time

from fastapi import FastAPI, HTTPException

from models import ConfigRequest, ConfigResponse, HealthResponse, RateResponse, SnapshotResponse
from rate_engine import rate_engine

app = FastAPI(
    title="BCB Rate Service",
    description=(
        "Servicio simulado del Banco Central de Bolivia. "
        "Tipo de cambio USD/BOB configurable: PATCH /config para ajustar base y oscilación."
    ),
    version="2.0.0",
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
    """Retorna el tipo de cambio actual (base + oscilación)."""
    return RateResponse(rate=rate_engine.get_rate())


@app.get("/snapshot", response_model=SnapshotResponse)
def get_snapshot():
    """Retorna el tipo de cambio junto con los parámetros de configuración actuales."""
    snap = rate_engine.get_snapshot()
    return SnapshotResponse(
        rate=snap["rate"],
        tipo_cambio_base=snap["tipo_cambio_base"],
        oscilacion=snap["oscilacion"],
        timestamp=snap["timestamp"],
    )


@app.get("/config", response_model=ConfigResponse)
def get_config():
    """Consulta la configuración actual del tipo de cambio."""
    snap = rate_engine.get_snapshot()
    return ConfigResponse(
        tipo_cambio_base=snap["tipo_cambio_base"],
        oscilacion=snap["oscilacion"],
        tipo_final=snap["rate"],
    )


@app.patch("/config", response_model=ConfigResponse)
def update_config(body: ConfigRequest):
    """
    Configura el tipo de cambio manualmente.

    - **tipo_cambio_base**: valor base en BOB/USD (ej. 6.86). Opcional.
    - **oscilacion**: ajuste sobre la base, rango [-0.9999, 0.9999]. Opcional.
    - **tipo_final** resultante = base + oscilacion

    Envía sólo los campos que quieres cambiar.
    """
    if body.tipo_cambio_base is None and body.oscilacion is None:
        raise HTTPException(
            status_code=422,
            detail="Debes enviar al menos un campo: tipo_cambio_base u oscilacion.",
        )

    try:
        rate_engine.set_config(
            base=body.tipo_cambio_base,
            oscilacion=body.oscilacion,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    snap = rate_engine.get_snapshot()
    return ConfigResponse(
        tipo_cambio_base=snap["tipo_cambio_base"],
        oscilacion=snap["oscilacion"],
        tipo_final=snap["rate"],
    )
